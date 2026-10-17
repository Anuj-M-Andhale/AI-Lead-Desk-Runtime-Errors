
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import truststore
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_DIR / ".env", override=True)
truststore.inject_into_ssl()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

STT_MODEL = "gemini-2.5-flash"
TTS_MODEL = "gemini-3.8-flash-tts"
TTS_VOICE = "Kore"

MAX_AUDIO_SIZE = 20 * 1024 * 1024
MAX_TTS_CHARACTERS = 4000

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ai_lead_desk.telegram")

rag_service = None
rag_lock = asyncio.Lock()


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing from .env.")

    return genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# RAG SERVICE
# ============================================================

async def get_rag_service():
    global rag_service

    if rag_service is None:
        async with rag_lock:
            if rag_service is None:
                logger.info("Initializing DocumentRAGService...")

                from ai_lead_desk.rag_service import DocumentRAGService

                rag_service = await asyncio.to_thread(
                    DocumentRAGService,
                    PROJECT_DIR,
                )

                logger.info("DocumentRAGService initialized.")

    return rag_service


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(audio_path: str) -> str:
    """Transcribe a Telegram audio file using Gemini."""
    client = get_gemini_client()
    uploaded_file = None

    try:
        uploaded_file = client.files.upload(file=audio_path)

        response = client.models.generate_content(
            model=STT_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=(
                                "Transcribe the supplied audio accurately. "
                                "Preserve the language spoken. Return only "
                                "the spoken words without commentary."
                            )
                        ),
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type=(
                                getattr(uploaded_file, "mime_type", None)
                                or "audio/ogg"
                            ),
                        ),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0,
            ),
        )

        transcript = (response.text or "").strip()

        if not transcript:
            raise RuntimeError("Gemini returned an empty transcription.")

        return transcript

    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                logger.warning(
                    "Could not delete temporary Gemini upload.",
                    exc_info=True,
                )


# ============================================================
# TEXT TO SPEECH + TELEGRAM AUDIO CONVERSION
# ============================================================

def generate_telegram_voice(
    text: str,
    output_ogg_path: str,
) -> str:
    """
    Generate speech using Gemini and convert it to OGG/Opus
    for Telegram's native voice-message player.
    """
    if not text.strip():
        raise ValueError("Cannot generate speech from empty text.")

    text = text[:MAX_TTS_CHARACTERS]

    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg was not found in PATH. Install it with:\n"
            "conda install -c conda-forge ffmpeg\n"
            "Then restart PowerShell."
        )

    client = get_gemini_client()

    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=TTS_VOICE,
                    )
                )
            ),
        ),
    )

    audio_bytes = None

    for candidate in response.candidates or []:
        if not candidate.content:
            continue

        for part in candidate.content.parts or []:
            if part.inline_data and part.inline_data.data:
                audio_bytes = part.inline_data.data
                break

        if audio_bytes:
            break

    if not audio_bytes:
        raise RuntimeError("Gemini did not return audio data.")

    # Gemini TTS normally returns raw 24 kHz, 16-bit mono PCM.
    # Wrap the PCM in a WAV container for FFmpeg.
    with tempfile.TemporaryDirectory(
        prefix="ai_lead_desk_tts_"
    ) as temp_dir:
        wav_path = Path(temp_dir) / "speech.wav"

        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(audio_bytes)

        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(wav_path),
            "-vn",
            "-c:a", "libopus",
            "-application", "voip",
            "-b:a", "48k",
            "-ac", "1",
            "-ar", "48000",
            "-f", "ogg",
            output_ogg_path,
        ]

        # Capture both output streams so conversion failures
        # include the actual FFmpeg diagnostic.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            details = "\n".join(
                part.strip()
                for part in (result.stdout, result.stderr)
                if part and part.strip()
            )

            raise RuntimeError(
                f"FFmpeg exited with code {result.returncode}.\n"
                f"Command: {' '.join(command)}\n"
                f"FFmpeg output:\n"
                f"{details or 'No diagnostic output captured.'}"
            )

    if (
        not os.path.isfile(output_ogg_path)
        or os.path.getsize(output_ogg_path) == 0
    ):
        raise RuntimeError(
            "FFmpeg reported success, but the OGG file is missing or empty."
        )

    logger.info(
        "Created Telegram voice audio: %s bytes",
        os.path.getsize(output_ogg_path),
    )

    return output_ogg_path


# ============================================================
# FORMAT RAG ANSWERS
# ============================================================

def format_answer(result) -> str:
    """Extract the answer and avoid exposing internal metadata."""
    if isinstance(result, dict):
        answer = str(result.get("answer", "")).strip()

        if not answer:
            return (
                "I couldn't find a reliable answer in the institute's "
                "available documents. Please contact an admissions "
                "counselor for confirmation."
            )

        if not result.get("grounded", False):
            return (
                "I couldn't verify that information in the institute's "
                "available documents. Please contact the institute "
                "for confirmation."
            )

        if result.get("answer_mode") == "deterministic_course_facts":
            import re

            match = re.search(
                r"for\s+(.+?)\s+is:\s*(.+)",
                answer,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if match:
                course = match.group(1).strip().rstrip(".")
                facts = match.group(2).strip()

                def format_inr(match_obj):
                    amount = int(match_obj.group(1).replace(",", ""))
                    return f"₹{amount:,}"

                facts = re.sub(
                    r"\bINR\s*([\d,]+)\b",
                    format_inr,
                    facts,
                    flags=re.IGNORECASE,
                )

                return f"{course}\n{facts.rstrip('.')}"

        return answer

    if isinstance(result, str):
        return result.strip()

    return str(result).strip()


# ============================================================
# SEND TEXT
# ============================================================

async def send_long_message(message, text: str):
    """Split long answers into Telegram-sized messages."""
    for index in range(0, len(text), 4000):
        await message.reply_text(text[index:index + 4000])


# ============================================================
# SEND PLAYABLE TELEGRAM VOICE MESSAGE
# ============================================================

async def send_voice_reply(message, answer: str):
    """Send OGG/Opus as a playable Telegram voice note."""
    with tempfile.TemporaryDirectory(
        prefix="ai_lead_desk_voice_"
    ) as temp_dir:
        ogg_path = str(Path(temp_dir) / "reply.ogg")

        await asyncio.to_thread(
            generate_telegram_voice,
            answer,
            ogg_path,
        )

        # Do not send WAV or a document fallback.
        with open(ogg_path, "rb") as voice_file:
            await message.reply_voice(
                voice=voice_file,
                caption="AI Lead Desk",
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
                pool_timeout=30,
            )


# ============================================================
# RAG ANSWERING PIPELINE
# ============================================================

async def answer_question(
    message,
    query: str,
    speak: bool = False,
):
    service = await get_rag_service()

    result = await asyncio.to_thread(
        service.answer,
        query,
    )

    answer = format_answer(result)

    if not answer:
        answer = (
            "I couldn't find a reliable answer in the available "
            "institute documents."
        )

    # Always send the readable response first.
    await send_long_message(message, answer)

    if speak:
        try:
            await message.reply_text(
                "🔊 Generating your voice reply..."
            )

            await send_voice_reply(message, answer)

        except Exception as exc:
            logger.exception("Voice generation or delivery failed.")

            # No WAV attachment is sent if voice generation fails.
            await message.reply_text(
                "The text answer was sent, but I couldn't create or "
                "send the Telegram voice message.\n\n"
                f"Error: {str(exc)[:700]}"
            )


# ============================================================
# TELEGRAM COMMANDS
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "Welcome to AI Lead Desk! 👋\n\n"
        "Ask about institute courses, fees, duration, schedules, "
        "and syllabus.\n\n"
        "🎙 Send a voice note to receive a transcription, a text "
        "answer, and a playable Telegram voice reply.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/voice on - Enable speech for text questions\n"
        "/voice off - Disable speech for text questions"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "Send a text question, voice note, or audio file.\n\n"
        "Voice messages are transcribed and answered using institute "
        "documents. The bot then sends text plus playable speech.\n\n"
        "/voice on - Speak answers to text questions\n"
        "/voice off - Text-only answers to text questions"
    )


async def voice_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if message is None:
        return

    if (
        not context.args
        or context.args[0].lower() not in {"on", "off"}
    ):
        await message.reply_text(
            "Usage: /voice on or /voice off"
        )
        return

    enabled = context.args[0].lower() == "on"
    context.user_data["voice_replies"] = enabled

    if enabled:
        await message.reply_text(
            "🔊 Voice replies are enabled for text questions."
        )
    else:
        await message.reply_text(
            "Text-only replies are enabled for text questions."
        )


# ============================================================
# TEXT MESSAGE HANDLER
# ============================================================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if message is None or not message.text:
        return

    query = message.text.strip()

    if not query:
        return

    try:
        await context.bot.send_chat_action(
            chat_id=message.chat_id,
            action=ChatAction.TYPING,
        )

        await answer_question(
            message,
            query,
            speak=context.user_data.get("voice_replies", False),
        )

    except Exception:
        logger.exception("Failed to process text question.")

        await message.reply_text(
            "Sorry, I couldn't process your question. Please try again."
        )


# ============================================================
# AUDIO MESSAGE HANDLER
# ============================================================

async def handle_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if message is None:
        return

    audio = message.voice or message.audio

    if audio is None:
        return

    if audio.file_size and audio.file_size > MAX_AUDIO_SIZE:
        await message.reply_text(
            "Your audio exceeds 20 MB. Please send a shorter recording."
        )
        return

    try:
        await context.bot.send_chat_action(
            chat_id=message.chat_id,
            action=ChatAction.TYPING,
        )

        await message.reply_text("🎧 Transcribing your audio...")

        telegram_file = await context.bot.get_file(audio.file_id)

        with tempfile.TemporaryDirectory(
            prefix="ai_lead_desk_input_"
        ) as temp_dir:
            suffix = ".oga" if message.voice else ".audio"
            audio_path = str(Path(temp_dir) / f"input{suffix}")

            await telegram_file.download_to_drive(
                custom_path=audio_path
            )

            transcript = await asyncio.to_thread(
                transcribe_audio,
                audio_path,
            )

        await message.reply_text(
            f"📝 I heard:\n{transcript}"
        )

        await context.bot.send_chat_action(
            chat_id=message.chat_id,
            action=ChatAction.TYPING,
        )

        # Audio input always receives a Telegram voice reply.
        await answer_question(
            message,
            transcript,
            speak=True,
        )

    except Exception:
        logger.exception("Failed to process audio.")

        await message.reply_text(
            "Sorry, I couldn't process that audio. "
            "Please try again or send your question as text."
        )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing from your .env file."
        )

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from your .env file."
        )

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=30,
    )

    updates_request = HTTPXRequest(
        connection_pool_size=2,
        connect_timeout=30,
        read_timeout=40,
        write_timeout=30,
        pool_timeout=30,
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request)
        .get_updates_request(updates_request)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voice", voice_command))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO,
            handle_audio,
        )
    )

    logger.info("Starting AI Lead Desk Telegram bot...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
