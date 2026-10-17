import base64
import re
import time
from pathlib import Path

from google import genai


AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".ogg", ".flac",
    ".mp4", ".mpeg", ".mpga", ".webm"
}

MAX_AUDIO_BYTES = 25 * 1024 * 1024

LANGUAGE_INSTRUCTIONS = {
    "en": (
        "Speak the supplied text naturally in English. "
        "Do not translate or paraphrase it."
    ),
    "hi": (
        "Speak the supplied text naturally in Hindi. "
        "Do not translate or paraphrase it."
    ),
    "mr": (
        "Speak the supplied text naturally in Marathi. "
        "Do not translate or paraphrase it."
    ),
}


def _normalize_language(raw_language):
    """Normalize the language identifier returned by the audio model."""
    value = (raw_language or "").strip().lower()

    if "marathi" in value or re.search(r"(?<!\w)mr(?!\w)", value):
        return "mr"

    if "hindi" in value or re.search(r"(?<!\w)hi(?!\w)", value):
        return "hi"

    if "english" in value or re.search(r"(?<!\w)en(?!\w)", value):
        return "en"

    return None


def identify_audio_language(gemini_client, uploaded_audio):
    """Identify the dominant spoken language from the original recording."""
    response = gemini_client.interactions.create(
        model="gemini-3.8-flash",
        input=[
            {
                "type": "text",
                "text": (
                    "Identify the dominant language actually spoken in "
                    "this audio. Choose exactly one: en, hi, or mr. "
                    "en means English, hi means Hindi, and mr means "
                    "Marathi. Distinguish Hindi from Marathi by listening "
                    "to the speech, not merely by identifying the script. "
                    "If English words are mixed into Hindi or Marathi, "
                    "choose the dominant language. Return only the code."
                ),
            },
            {
                "type": "audio",
                "uri": uploaded_audio.uri,
                "mime_type": uploaded_audio.mime_type,
            },
        ],
    )

    raw_language = (response.output_text or "").strip()
    language = _normalize_language(raw_language)

    if language is None:
        raise ValueError(
            "Could not confidently identify the spoken language. "
            f"Model response: {raw_language!r}"
        )

    return language


def transcribe_uploaded_audio(gemini_client, uploaded_audio):
    """Transcribe speech without translating it into another language."""
    response = gemini_client.interactions.create(
        model="gemini-3.5-transcribe",
        input=[
            {
                "type": "audio",
                "uri": uploaded_audio.uri,
                "mime_type": uploaded_audio.mime_type,
            }
        ],
        generation_config={
            "transcription_config": {
                "language_codes": [],
                "custom_vocabulary": [
                    "Python Programming",
                    "Data Science Foundations",
                    "Web Development",
                    "AI Lead Desk",
                ],
            }
        },
    )

    transcript = (response.output_text or "").strip()

    if not transcript:
        raise ValueError("The transcription model returned no text.")

    return transcript


def synthesize_speech(
    gemini_client,
    text,
    language,
    output_path,
):
    """Generate audio locally nowhere: this uses the Gemini TTS API."""
    if language not in LANGUAGE_INSTRUCTIONS:
        raise ValueError("Language must be 'en', 'hi', or 'mr'.")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text to speak cannot be empty.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = gemini_client.interactions.create(
        model="gemini-3.8-flash-lite-tts",
        input=[
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": text.strip(),
                        "annotations": [
                            {
                                "type": "speech_metadata",
                                "style": LANGUAGE_INSTRUCTIONS[language],
                            }
                        ],
                    }
                ],
            }
        ],
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [{"voice": "Kore"}]
        },
    )

    audio_data = response.output_audio.data

    if not audio_data:
        raise RuntimeError("The TTS model returned no audio.")

    if isinstance(audio_data, str):
        audio_bytes = base64.b64decode(audio_data)
    else:
        audio_bytes = bytes(audio_data)

    output_path.write_bytes(audio_bytes)

    if output_path.stat().st_size == 0:
        raise RuntimeError("The generated audio file is empty.")

    return output_path


def process_voice_message(
    audio_path,
    rag_service,
    gemini_client,
    output_dir,
):
    """
    Process a voice message through:
    upload -> language detection -> transcription ->
    grounded counselling -> speech generation.

    Returns transcript, language, answer, provenance,
    audio path, and stage timings.
    """
    audio_path = Path(audio_path)

    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if audio_path.suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError(f"Unsupported audio format: {audio_path.suffix}")

    if audio_path.stat().st_size > MAX_AUDIO_BYTES:
        raise ValueError("Audio recording exceeds 25 MB.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timings = {}

    started = time.perf_counter()
    uploaded_audio = gemini_client.files.upload(file=str(audio_path))
    timings["upload_seconds"] = round(
        time.perf_counter() - started, 2
    )

    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    def _timed_voice_call(function, *args):
        call_started = time.perf_counter()
        value = function(*args)
        return value, time.perf_counter() - call_started

    def _fallback_language(transcript):
        # Best-effort fallback. Audio-based Gemini detection remains preferred.
        text = transcript.lower()

        marathi_markers = [
            "आहे", "आहेत", "काय", "किती", "मला",
            "माझा", "माझी", "माझे", "मध्ये", "साठी",
            "सांगा", "पाहिजे", "aahe", "ahet", "kay",
            "kiti", "mala", "majha", "majhi", "madhe",
            "sathi", "sanga", "pahije",
        ]

        hindi_markers = [
            "क्या", "है", "हैं", "मुझे", "मेरा",
            "मेरी", "में", "कितना", "कितनी", "बताओ",
            "चाहिए", "कहाँ", "kya", "hai", "hain",
            "mujhe", "mera", "meri", "mein", "kitna",
            "kitni", "batao", "chahiye", "kahan",
        ]

        mr_score = sum(text.count(word) for word in marathi_markers)
        hi_score = sum(text.count(word) for word in hindi_markers)

        if mr_score > hi_score and mr_score > 0:
            return "mr"

        if hi_score > mr_score and hi_score > 0:
            return "hi"

        if re.search(r"[\\u0900-\\u097F]", text):
            return "hi"

        return "en"

    executor = ThreadPoolExecutor(max_workers=2)

    try:
        language_future = executor.submit(
            _timed_voice_call,
            identify_audio_language,
            gemini_client,
            uploaded_audio,
        )

        transcript_future = executor.submit(
            _timed_voice_call,
            transcribe_uploaded_audio,
            gemini_client,
            uploaded_audio,
        )

        # Obtain the transcript while language detection runs in parallel.
        transcript, transcription_elapsed = transcript_future.result()
        timings["transcription_seconds"] = round(
            transcription_elapsed, 2
        )

        language_wait_started = time.perf_counter()

        try:
            language, language_elapsed = language_future.result(
                timeout=8
            )
            timings["language_detection_seconds"] = round(
                language_elapsed, 2
            )
            timings["language_detection_method"] = "audio"

        except (TimeoutError, Exception) as exc:
            language = _fallback_language(transcript)
            timings["language_detection_seconds"] = round(
                time.perf_counter() - language_wait_started, 2
            )
            timings["language_detection_method"] = "transcript_fallback"

            print(
                "Warning: audio-based language detection did not finish "
                f"successfully ({type(exc).__name__}). "
                f"Using best-effort transcript fallback: {language}"
            )

    finally:
        # Don't make the user wait for a slow detector after fallback.
        executor.shutdown(wait=False, cancel_futures=True)

    started = time.perf_counter()
    result = rag_service.answer(
        transcript,
        response_language=language,
    )
    timings["answer_seconds"] = round(
        time.perf_counter() - started, 2
    )

    output_path = output_dir / f"voice_response_{time.time_ns()}.wav"

    started = time.perf_counter()
    audio_path_out = synthesize_speech(
        gemini_client=gemini_client,
        text=result["answer"],
        language=language,
        output_path=output_path,
    )
    timings["tts_seconds"] = round(
        time.perf_counter() - started, 2
    )

    return {
        "transcript": transcript,
        "language": language,
        "answer": result["answer"],
        "grounded": result["grounded"],
        "answer_mode": result["answer_mode"],
        "sources": result["sources"],
        "audio_path": str(audio_path_out),
        "timings": timings,
    }
