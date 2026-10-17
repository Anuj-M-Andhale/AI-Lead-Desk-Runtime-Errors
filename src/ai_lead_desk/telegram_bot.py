
"""
AI Lead Desk â€” Telegram Bot
Features:
- Text-based institute/course queries using DocumentRAGService
- Voice message transcription using Gemini
- Gemini-generated voice replies
- Telegram-compatible OGG/Opus audio using FFmpeg
- Per-user voice reply controls: /voice on and /voice off
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

import truststore

# Use the operating system's trusted certificates, useful on Windows
# systems that use managed certificate stores.
truststore.inject_into_ssl()

from dotenv import load_dotenv
from google import genai
from groq import Groq
from google.genai import types
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.error import TelegramError
from telegram.ext import (
    CallbackQueryHandler,
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from ai_lead_desk.rag_service import DocumentRAGService
from ai_lead_desk import lead_store


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_DIR / ".env"

load_dotenv(ENV_FILE)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

GEMINI_STT_MODEL = os.getenv(
    "GEMINI_STT_MODEL",
    "gemini-2.5-flash",
).strip()

GEMINI_TTS_MODEL = os.getenv(
    "GEMINI_TTS_MODEL",
    "gemini-3.8-flash-tts",
).strip()

GEMINI_TTS_VOICE = os.getenv(
    "GEMINI_TTS_VOICE",
    "Kore",
).strip()

MAX_TTS_CHARACTERS = 3500

# This is the executable extracted into the project directory.
# An environment variable takes priority over searching PATH.
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "").strip()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("ai_lead_desk.telegram")


# ============================================================
# LAZY SERVICE INITIALIZATION
# ============================================================

_rag_service: DocumentRAGService | None = None
_gemini_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    """Create the Gemini client only when required."""
    global _gemini_client

    if _gemini_client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is missing from the project's .env file."
            )

        _gemini_client = genai.Client(
            api_key=GEMINI_API_KEY,
        )

    return _gemini_client


def get_rag_service() -> DocumentRAGService:
    """Initialize the institute document RAG service on first use."""
    global _rag_service

    if _rag_service is None:
        logger.info("Initializing DocumentRAGService...")

        _rag_service = DocumentRAGService(
            project_dir=PROJECT_DIR,
        )

        logger.info("DocumentRAGService initialized.")

    return _rag_service


# ============================================================
# RESPONSE FORMATTING
# ============================================================

def format_answer(result: Any) -> str:
    """Extract a readable answer from the RAG service response."""
    if isinstance(result, dict):
        answer = (
            result.get("answer")
            or result.get("response")
            or result.get("output")
            or result.get("text")
        )

        if answer is None:
            answer = str(result)
    else:
        answer = str(result)

    answer = answer.strip()

    if not answer:
        return (
            "I couldn't generate an answer for that question. "
            "Please try asking in a different way."
        )

    # Telegram messages have a maximum text length. Split long
    # responses later when sending them instead of truncating here.
    return answer


async def send_long_message(
    message: Message,
    text: str,
) -> None:
    """Send long answers as multiple Telegram messages."""
    max_length = 4000
    remaining = text.strip()

    while remaining:
        if len(remaining) <= max_length:
            chunk = remaining
            remaining = ""
        else:
            split_at = remaining.rfind("\n", 0, max_length)

            if split_at < max_length // 2:
                split_at = remaining.rfind(" ", 0, max_length)

            if split_at < max_length // 2:
                split_at = max_length

            chunk = remaining[:split_at].strip()
            remaining = remaining[split_at:].strip()

        if chunk:
            await message.reply_text(
                chunk,
                connect_timeout=30,
                read_timeout=60,
                write_timeout=60,
                pool_timeout=30,
            )


# ============================================================
# GEMINI SPEECH-TO-TEXT
# ============================================================

def transcribe_audio(audio_path: str) -> str:
    """
    Upload an audio file to Gemini and transcribe the speech.

    The uploaded Gemini file is deleted after processing when
    possible.
    """
    client = get_gemini_client()
    uploaded_file = None

    try:
        uploaded_file = client.files.upload(
            file=audio_path,
            config={"mime_type": "audio/ogg"},
        )

        response = client.models.generate_content(
            model=GEMINI_STT_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=(
                                "You are a multilingual speech transcription "
                                "system. Automatically identify the language "
                                "spoken in the audio. Support English, Hindi, "
                                "Marathi, and natural code-switching between "
                                "these languages. Transcribe exactly what is "
                                "spoken in the original language; do not "
                                "translate it into English or another language. "
                                "For Hindi and Marathi, use Devanagari script; "
                                "for English, use Latin script. Preserve names, "
                                "numbers, and course codes. Return only the "
                                "transcription, with no language label or "
                                "commentary."
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
            raise RuntimeError(
                "Gemini did not return a transcription."
            )

        return transcript

    finally:
        if uploaded_file is not None:
            try:
                if getattr(uploaded_file, "name", None):
                    client.files.delete(
                        name=uploaded_file.name,
                    )
            except Exception:
                logger.warning(
                    "Could not delete the temporary Gemini audio file.",
                    exc_info=True,
                )


# ============================================================
# GEMINI TEXT-TO-SPEECH + TELEGRAM AUDIO CONVERSION
# ============================================================

def resolve_ffmpeg() -> str:
    """Resolve FFmpeg from .env or the system PATH."""
    configured_path = FFMPEG_PATH or os.getenv(
        "FFMPEG_PATH",
        "",
    ).strip()

    ffmpeg = configured_path or shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg executable was not found. Set FFMPEG_PATH in "
            "the project's .env file to the full path of ffmpeg.exe."
        )

    ffmpeg_path = Path(ffmpeg).expanduser()

    if not ffmpeg_path.is_file():
        raise RuntimeError(
            "The configured FFmpeg executable does not exist. "
            "Check the FFMPEG_PATH entry in .env."
        )

    return str(ffmpeg_path.resolve())


def generate_telegram_voice(
    text: str,
    output_ogg_path: str,
) -> str:
    """
    Generate speech using Gemini TTS and convert its PCM audio
    to Telegram-compatible OGG/Opus.
    """
    text = text.strip()[:MAX_TTS_CHARACTERS]

    if not text:
        raise ValueError(
            "Cannot generate voice for an empty answer."
        )

    ffmpeg = resolve_ffmpeg()
    client = get_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_TTS_MODEL,
        # Keep speaking rules separate from the answer; otherwise TTS may
        # accidentally read the rules aloud as part of the audio.
        contents=text,
        # Do not pass system_instruction here: this TTS model rejects
        # developer/system instructions. Send only the answer as content so
        # there are no speaking rules for the model to read aloud.
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=GEMINI_TTS_VOICE,
                    ),
                ),
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
        raise RuntimeError(
            "Gemini did not return audio data."
        )

    output_path = Path(output_ogg_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Gemini TTS returns raw PCM audio. Wrap it in a WAV container
    # before converting it to OGG/Opus.
    with tempfile.TemporaryDirectory(
        prefix="ai_lead_desk_tts_",
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
            "-loglevel",
            "error",
            "-i",
            str(wav_path),
            "-vn",
            "-c:a",
            "libopus",
            "-b:a",
            "32k",
            "-application",
            "voip",
            "-f",
            "ogg",
            str(output_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            details = (
                result.stderr.strip()
                or result.stdout.strip()
                or "No diagnostic output captured."
            )

            raise RuntimeError(
                f"FFmpeg exited with code {result.returncode}.\n"
                f"FFmpeg output:\n{details}"
            )

    if (
        not output_path.is_file()
        or output_path.stat().st_size == 0
    ):
        raise RuntimeError(
            "FFmpeg reported success, but the OGG file is missing "
            "or empty."
        )

    logger.info(
        "Created Telegram voice audio: %s bytes",
        output_path.stat().st_size,
    )

    return str(output_path)


# ============================================================
# TELEGRAM COMMANDS
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Start a session and request the user's name."""
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    context.user_data.setdefault("voice_replies", False)

    lead_store.get_or_create_lead("telegram", user.id)
    lead_store.set_awaiting_name("telegram", user.id, True)

    await message.reply_text(
        "Welcome to AI Lead Desk!\\n\\n"
        "Before we begin, what is your name?\\n"
        "Please type your name in your next message.\\n\\n"
        "I'll save it to your profile so I can personalize "
        "your experience.\\n\\n"
        "After that, ask questions about institute courses "
        "and documents, or send a voice message."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /help."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text(
        "AI Lead Desk Help\n\n"
        "Send a text message to ask a question.\n"
        "Send a voice note to have it transcribed and answered.\n\n"
        "Commands:\n"
        "/start â€” Start the bot\n"
        "/help â€” Show help\n"
        "/voice on â€” Enable spoken AI replies\n"
        "/voice off â€” Disable spoken AI replies"
    )


async def voice_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Enable or disable spoken AI replies for the current user."""
    message = update.effective_message

    if not message:
        return

    if not context.args:
        enabled = context.user_data.get(
            "voice_replies",
            True,
        )

        await message.reply_text(
            "Voice replies are currently "
            + ("ON." if enabled else "OFF.")
            + "\nUse /voice on or /voice off to change this."
        )
        return

    option = context.args[0].strip().lower()

    if option in {"on", "yes", "true", "1"}:
        context.user_data["voice_replies"] = True

        await message.reply_text(
            "Voice replies enabled. I'll send spoken AI answers "
            "when audio generation succeeds."
        )

    elif option in {"off", "no", "false", "0"}:
        context.user_data["voice_replies"] = False

        await message.reply_text(
            "Voice replies disabled. I'll answer using text."
        )

    else:
        await message.reply_text(
            "Use /voice on or /voice off."
        )


# ============================================================
# QUESTION ANSWERING
# ============================================================

async def get_ai_answer(query: str) -> str:
    """Run the RAG service without blocking the Telegram event loop."""
    def run_rag() -> str:
        service = get_rag_service()
        result = service.answer(query)
        return format_answer(result)

    return await asyncio.to_thread(run_rag)



def mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "?? Ask institute-related doubts",
            callback_data="mode:institute",
        )],
        [InlineKeyboardButton(
            "?? Get course guidance",
            callback_data="mode:guidance",
        )],
    ])


def change_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "?? Change mode",
            callback_data="mode:menu",
        )
    ]])


async def handle_mode_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    choice = (query.data or "").partition(":")[2]

    if choice == "menu":
        await query.edit_message_text(
            "What would you like help with?",
            reply_markup=mode_keyboard(),
        )
        return

    if choice == "institute":
        context.user_data["assistant_mode"] = "institute"
        message = (
            "?? Institute Doubts mode selected. Ask about institute "
            "courses and documents; answers use the institute knowledge base."
        )
    elif choice == "guidance":
        context.user_data["assistant_mode"] = "guidance"
        message = (
            "?? Course Guidance mode selected. Tell me about your interests, "
            "current studies, or career goals. I'll help you explore courses, "
            "skills, careers, and learning paths using general AI guidance."
        )
    else:
        await query.edit_message_text("Please choose a valid mode.")
        return

    await query.edit_message_text(
        message,
        reply_markup=change_mode_keyboard(),
    )



async def get_guidance_answer(query: str, history: list[dict]) -> str:
    """Answer with Groq using recent saved conversation turns."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from the .env file.")

    messages = [{
        "role": "system",
        "content": (
            "You are AI Lead Desk, a friendly course and career guidance "
            "assistant for students. Use the conversation history to "
            "understand follow-up questions and remember details the student "
            "has shared. Give practical, concise guidance about courses, "
            "skills, projects, roadmaps, and careers. Do not guarantee jobs, "
            "salaries, or admissions, and do not invent institute policies. "
            "Match the student's language. If official institute details "
            "are needed, suggest Institute Doubts mode."
        ),
    }]

    # Only pass prior turns here; the current question is appended below.
    for item in history[-12:]:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        role = "assistant" if item.get("direction") == "outbound" else "user"
        messages.append({"role": role, "content": content[:2000]})

    messages.append({"role": "user", "content": query[:4000]})

    def generate() -> str:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv(
                "GROQ_GUIDANCE_MODEL", "openai/gpt-oss-20b"
            ).strip(),
            messages=messages,
            max_completion_tokens=700,
            temperature=0.4,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("Groq returned an empty guidance response.")
        return content.strip()

    return await asyncio.to_thread(generate)


def adapt_answer_to_question_language(query: str, answer: str) -> str:
    """
    Rewrite an answer in the language used by the question while preserving
    the original facts. Supports English, Hindi, Marathi, and code-switching.
    """
    client = get_gemini_client()

    prompt = f"""
You are the multilingual response editor for an institute information bot.

Identify the language or natural language mix used in the USER QUESTION.
Then rewrite the DRAFT ANSWER in that same language or mix:
- English question -> answer in English.
- Hindi question -> answer in natural Hindi using Devanagari.
- Marathi question -> answer in natural Marathi using Devanagari.
- Mixed-language question -> answer naturally in the same mix.
- If the language is ambiguous, use the dominant language of the question.

Important:
- Preserve every factual detail, price, duration, course code, and condition.
- Do not add facts, policies, discounts, guarantees, or information absent
  from the draft answer.
- Do not translate course codes, URLs, email addresses, or proper names.
- Return only the rewritten answer, with no language label or explanation.

USER QUESTION:
{query}

DRAFT ANSWER:
{answer}
""".strip()

    response = client.models.generate_content(
        model = os.getenv(
            
            "GEMINI_LANGUAGE_MODEL",
            "gemini-3.8-flash",
        ).strip(),
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0),
    )
    rewritten = (response.text or "").strip()
    return rewritten if rewritten else answer


async def send_voice_reply(
    message: Message,
    answer: str,
) -> None:
    """Generate and send an OGG/Opus voice reply."""
    with tempfile.TemporaryDirectory(
        prefix="ai_lead_desk_voice_",
    ) as temp_dir:
        ogg_path = str(Path(temp_dir) / "reply.ogg")

        await asyncio.to_thread(
            generate_telegram_voice,
            answer,
            ogg_path,
        )

        with open(ogg_path, "rb") as voice_file:
            await message.reply_voice(
                voice=voice_file,
                caption="AI Lead Desk",
                connect_timeout=30,
                read_timeout=120,
                write_timeout=120,
                pool_timeout=30,
            )


async def answer_question(
    message: Message,
    query: str,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    audio_input: bool = False,
    status_message: Message | None = None,
) -> None:
    """Answer a question; audio inputs receive only a voice answer."""
    query = query.strip()

    if not query:
        if status_message:
            await status_message.edit_text("I couldn't detect a question in that audio.")
        else:
            await message.reply_text("Please send a question.")
        return

    try:
        if status_message:
            await status_message.edit_text("â³ Please wait... I'm preparing your answer.")
        else:
            await message.chat.send_action("typing")

        user = message.from_user
        if user:
            recent = lead_store.get_recent_messages(
                "telegram", user.id, limit=13
            )
            # Text messages are already saved by handle_text; audio
            # transcriptions may not have been saved yet.
            if not recent or not (
                recent[-1].get("direction") == "inbound"
                and recent[-1].get("content", "").strip() == query
            ):
                lead_store.add_message(
                    "telegram", user.id, "inbound", query
                )
                recent = lead_store.get_recent_messages(
                    "telegram", user.id, limit=13
                )
            # Remove the current question; Groq appends it once itself.
            history = list(recent)
            if history and (
                history[-1].get("direction") == "inbound"
                and history[-1].get("content", "").strip() == query
            ):
                history.pop()
        else:
            history = []

        mode = context.user_data.get("assistant_mode", "institute")
        if mode == "guidance":
            answer = await get_guidance_answer(query, history)
        else:
            prior_turns = []
            for item in history[-6:]:
                content = str(item.get("content", "")).strip()
                if content:
                    speaker = (
                        "Student" if item.get("direction") == "inbound"
                        else "Assistant"
                    )
                    prior_turns.append(f"{speaker}: {content[:1000]}")
            rag_query = query
            if prior_turns:
                rag_query = (
                    "Use this recent conversation only to resolve references "
                    "in the latest question. Answer institute facts only from "
                    "retrieved institute documents.\n\n"
                    "Recent conversation:\n"
                    + "\n".join(prior_turns)
                    + "\n\nLatest student question: "
                    + query
                )
            answer = await get_ai_answer(rag_query)

        # Match the response language to the user's original question.
        # If language adaptation fails, keep the original RAG answer.
        if mode != "guidance":
            try:
                answer = await asyncio.to_thread(
                    adapt_answer_to_question_language,
                    query,
                    answer,
                )
            except Exception:
                logger.exception(
                    "Could not adapt the institute answer language; "
                    "using the original answer."
                )

        if message.from_user:
            lead_store.add_message(
                "telegram", message.from_user.id, "outbound", answer
            )

        if not audio_input:
            await send_long_message(message, answer)

            voice_enabled = context.user_data.get("voice_replies", False)
            if voice_enabled:
                await message.chat.send_action("record_voice")
                try:
                    await send_voice_reply(message, answer)
                except Exception:
                    logger.exception("Voice generation or delivery failed.")
                    await message.reply_text(
                        "I sent the answer as text, but couldn't "
                        "generate the voice reply this time."
                    )
            return

        # Audio input always gets audio output, independent of /voice setting.
        if status_message:
            await status_message.edit_text("â³ Please wait... Generating your voice reply.")
        await message.chat.send_action("record_voice")
        await send_voice_reply(message, answer)

        if status_message:
            try:
                await status_message.delete()
            except Exception:
                logger.debug("Could not remove completed processing status.", exc_info=True)

    except Exception:
        logger.exception("Failed to generate or deliver an AI Lead Desk answer.")
        error_text = (
            "Sorry, I couldn't process that audio and generate a voice reply. "
            "Please try again or send your question as text."
            if audio_input
            else "Sorry, I couldn't process that question right now. Please try again shortly."
        )
        if status_message:
            try:
                await status_message.edit_text(error_text)
            except Exception:
                await message.reply_text(error_text)
        else:
            await message.reply_text(error_text)


# ============================================================
# TEXT MESSAGE HANDLER
# ============================================================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Collect the student's name or route their text question."""
    message = update.effective_message
    user = update.effective_user

    if not message or not message.text or not user:
        return

    text = " ".join(message.text.strip().split())
    if not text:
        return

    lead = lead_store.get_or_create_lead("telegram", user.id)

    if lead["awaiting_name"]:
        if len(text) < 2 or len(text) > 100 or len(text.split()) > 5:
            await message.reply_text("Please enter a valid name (2-100 characters).")
            return

        lead_store.update_lead_name("telegram", user.id, text)
        lead_store.add_message("telegram", user.id, "inbound", text)

        await message.reply_text(
            f"Nice to meet you, {text}! Your name has been saved.\\n\\n"
            "What would you like help with?",
            reply_markup=mode_keyboard(),
        )
        return

    lead_store.add_message("telegram", user.id, "inbound", text)
    await answer_question(message, text, context)



# ============================================================
# VOICE / AUDIO MESSAGE HANDLER
# ============================================================

async def handle_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Transcribe audio and respond with voice only, showing processing status."""
    message = update.effective_message

    if not message:
        return

    telegram_file = None

    if message.voice:
        telegram_file = await message.voice.get_file()
    elif message.audio:
        telegram_file = await message.audio.get_file()

    if telegram_file is None:
        await message.reply_text("I couldn't find an audio file in that message.")
        return

    status_message = await message.reply_text("â³ Please wait... Transcribing your audio.")

    try:
        with tempfile.TemporaryDirectory(
            prefix="ai_lead_desk_input_audio_",
        ) as temp_dir:
            audio_path = Path(temp_dir) / "input_audio"

            await telegram_file.download_to_drive(
                custom_path=str(audio_path),
            )

            transcript = await asyncio.to_thread(
                transcribe_audio,
                str(audio_path),
            )

        if not transcript or not transcript.strip():
            await status_message.edit_text(
                "I couldn't understand that audio. Please try recording it again."
            )
            return

        # Deliberately do not send the transcript as a text message.
        await answer_question(
            message,
            transcript,
            context,
            audio_input=True,
            status_message=status_message,
        )

    except Exception:
        logger.exception("Failed to process incoming audio.")
        try:
            await status_message.edit_text(
                "Sorry, I couldn't process that audio. Please try a shorter recording "
                "or send your question as text."
            )
        except Exception:
            await message.reply_text(
                "Sorry, I couldn't process that audio. Please try again."
            )


# ============================================================
# ERROR HANDLER
# ============================================================

async def handle_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log unexpected Telegram handler errors."""
    logger.error(
        "Unhandled Telegram bot error.",
        exc_info=(
            type(context.error),
            context.error,
            context.error.__traceback__
            if context.error
            else None,
        ),
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main() -> None:
    """Configure and start the Telegram polling bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing from the project's .env file."
        )

    # Use explicit network timeouts for Telegram API calls.
    request = HTTPXRequest(
        connection_pool_size=10,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=30,
    )

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )
    application.add_handler(
        CommandHandler("help", help_command)
    )
    application.add_handler(
        CommandHandler("voice", voice_command)
    )
    application.add_handler(
        CallbackQueryHandler(handle_mode_callback, pattern=r"^mode:")
    )

    application.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO,
            handle_audio,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text,
        )
    )

    application.add_error_handler(
        handle_error
    )

    logger.info("Starting AI Lead Desk Telegram bot...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()

