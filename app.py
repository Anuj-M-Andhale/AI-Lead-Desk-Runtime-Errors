import os
import sys
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai


# =========================================================
# 1. PROJECT CONFIGURATION
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
DOCUMENTS_DIR = PROJECT_DIR / "data" / "institute_documents"
VOICE_OUTPUT_DIR = PROJECT_DIR / "data" / "voice_outputs"

# Make the existing project modules importable.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Load API keys from the project .env file.
load_dotenv(PROJECT_DIR / ".env")

from ai_lead_desk.rag_service import DocumentRAGService
from ai_lead_desk.voice_service import process_voice_message


# =========================================================
# 2. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Lead Desk",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎓 AI Lead Desk")

st.caption(
    "AI Admissions Counselor | "
    "Document-Grounded Answers | Multilingual Voice Support"
)


# =========================================================
# 3. INITIALIZE REUSABLE AI SERVICES
# =========================================================

@st.cache_resource(show_spinner="Loading institute knowledge base...")
def get_rag_service(project_dir: str) -> DocumentRAGService:
    """Initialize and cache the existing document RAG service."""
    return DocumentRAGService(project_dir=project_dir)


@st.cache_resource
def get_gemini_client():
    """Create and cache the Gemini client."""
    load_dotenv(PROJECT_DIR / ".env")

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


try:
    rag_service = get_rag_service(str(PROJECT_DIR))

except Exception as exc:
    st.error("The document RAG service could not be initialized.")

    st.code(f"{type(exc).__name__}: {exc}")

    st.info(
        "Check your .env file, GROQ_API_KEY, Ollama availability, "
        "and the local embedding model."
    )

    st.stop()


try:
    gemini_client = get_gemini_client()

except Exception as exc:
    gemini_client = None

    st.sidebar.warning(
        f"Gemini initialization failed: {type(exc).__name__}"
    )


# =========================================================
# 4. SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! Welcome to AI Lead Desk. Ask me about courses, "
                "fees, duration, schedules, syllabus, or institute "
                "policies covered by the available documents."
            ),
            "answer_mode": "welcome",
            "grounded": None,
            "sources": [],
        }
    ]


if "followups" not in st.session_state:
    st.session_state.followups = []


if "last_voice_result" not in st.session_state:
    st.session_state.last_voice_result = None


# =========================================================
# 5. KNOWLEDGE BASE STATUS
# =========================================================

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
VOICE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
}


def get_document_files():
    """Return supported files in the institute documents directory."""
    return sorted(
        path
        for path in DOCUMENTS_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    )


document_files = get_document_files()


# =========================================================
# 6. SIDEBAR
# =========================================================

st.sidebar.title("Counselor Workspace")

st.sidebar.metric(
    "Indexed Document Chunks",
    len(rag_service.document_chunks),
)

st.sidebar.metric(
    "Institute Documents",
    len(document_files),
)

st.sidebar.metric(
    "Counselor Follow-ups",
    len(st.session_state.followups),
)

st.sidebar.divider()

language_label = st.sidebar.selectbox(
    "Preferred Answer Language",
    [
        "Auto-detect",
        "English",
        "Hindi",
        "Marathi",
    ],
)

LANGUAGE_MAP = {
    "Auto-detect": None,
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
}

response_language = LANGUAGE_MAP[language_label]

st.sidebar.divider()

st.sidebar.success("Document RAG initialized")

if gemini_client is not None:
    st.sidebar.success("Voice service configured")
else:
    st.sidebar.warning(
        "Voice service unavailable. Check GEMINI_API_KEY in .env."
    )

st.sidebar.caption(
    "Development prototype. WhatsApp and Instagram integrations "
    "are not connected yet."
)


# =========================================================
# 7. SOURCE EVIDENCE DISPLAY
# =========================================================

def show_sources(record: dict):
    """Display grounding status and retrieved document sources."""

    with st.expander("Evidence and Sources"):

        if record.get("grounded") is True:
            st.write(
                "The RAG service marked this answer as grounded. "
                "This does not guarantee that every generated claim "
                "has been independently verified."
            )

        else:
            st.warning(
                "This answer was not marked as grounded in "
                "retrieved document evidence."
            )

        st.write(
            "Answer Mode:",
            record.get("answer_mode", "unknown"),
        )

        sources = record.get("sources") or []

        if not sources:
            st.write("No retrieved sources were returned.")
            return

        for source in sources:

            st.write(
                "**Document:**",
                source.get("source", "Unknown"),
            )

            st.write(
                "**Chunk ID:**",
                source.get("chunk_id", "N/A"),
            )

            similarity = source.get("similarity")

            if similarity is not None:
                st.write(
                    "**Retrieval Similarity:**",
                    similarity,
                )

            st.divider()


# =========================================================
# 8. COUNSELOR FOLLOW-UP HELPER
# =========================================================

def add_followup(
    question: str,
    answer: str,
    sources: list,
    answer_mode: str,
):
    """Add a question to the current session's counselor queue."""

    if not question:
        return False

    already_exists = any(
        item["question"] == question
        for item in st.session_state.followups
    )

    if already_exists:
        return False

    st.session_state.followups.append(
        {
            "question": question,
            "answer": answer,
            "sources": sources or [],
            "answer_mode": answer_mode,
        }
    )

    return True


# =========================================================
# 9. MAIN DASHBOARD TABS
# =========================================================

text_tab, voice_tab, knowledge_tab, followup_tab = st.tabs(
    [
        "💬 Text Inquiries",
        "🎙️ Voice Inquiries",
        "📚 Knowledge Base",
        "🧑‍💼 Counselor Follow-ups",
    ]
)


# =========================================================
# 10. TEXT INQUIRIES
# =========================================================

with text_tab:

    st.subheader("Student Conversation")

    st.write(
        "Ask questions about available institute courses and policies. "
        "Answers use the existing document RAG service."
    )

    # Display the conversation history.
    for index, message in enumerate(st.session_state.messages):

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if (
                message["role"] == "assistant"
                and message.get("answer_mode") != "welcome"
            ):

                show_sources(message)

                question = message.get("question")

                if question:

                    if st.button(
                        "Flag for Counselor Follow-up",
                        key=f"text_followup_{index}",
                    ):

                        added = add_followup(
                            question=question,
                            answer=message["content"],
                            sources=message.get("sources", []),
                            answer_mode=message.get(
                                "answer_mode",
                                "unknown",
                            ),
                        )

                        if added:
                            st.success(
                                "Added to the counselor follow-up queue."
                            )

                        else:
                            st.info(
                                "This question is already in the queue."
                            )

    # Accept a new student question.
    question = st.chat_input(
        "Enter the student's question...",
        key="student_question",
    )

    if question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        try:
            with st.spinner(
                "Searching institute documents and preparing an answer..."
            ):

                result = rag_service.answer(
                    question,
                    response_language=response_language,
                )

            assistant_message = {
                "role": "assistant",
                "content": str(result["answer"]),
                "question": question,
                "grounded": result.get("grounded", False),
                "sources": result.get("sources", []),
                "answer_mode": result.get(
                    "answer_mode",
                    "unknown",
                ),
            }

        except Exception as exc:

            st.error(
                f"Question processing failed: "
                f"{type(exc).__name__}: {exc}"
            )

            assistant_message = {
                "role": "assistant",
                "content": (
                    "I couldn't process this inquiry right now. "
                    "Please refer it to an admissions counselor."
                ),
                "question": question,
                "grounded": False,
                "sources": [],
                "answer_mode": "processing_error",
            }

        st.session_state.messages.append(assistant_message)

        # Rerun so the new response appears in the conversation.
        st.rerun()


# =========================================================
# 11. VOICE INQUIRIES
# =========================================================

with voice_tab:

    st.subheader("Student Voice Message")

    st.write(
        "Upload a recording to transcribe the question, identify the "
        "spoken language, retrieve institute information, and generate "
        "a spoken reply."
    )

    audio_file = st.file_uploader(
        "Choose an audio recording",
        type=[
            "wav",
            "mp3",
            "m4a",
            "ogg",
            "webm",
            "mp4",
        ],
        max_upload_size=25,
        key="voice_upload",
    )

    if audio_file is not None:
        st.audio(audio_file)

    if gemini_client is None:
        st.warning(
            "Voice processing requires GEMINI_API_KEY in your .env file."
        )

    process_disabled = (
        audio_file is None
        or gemini_client is None
    )

    if st.button(
        "Process Voice Message",
        type="primary",
        disabled=process_disabled,
        key="process_voice_message",
    ):

        temporary_audio_path = None

        try:

            # Enforce the 25 MB limit.
            if audio_file.size > 25 * 1024 * 1024:

                st.error(
                    "The audio file exceeds the 25 MB limit."
                )

            else:

                audio_suffix = (
                    Path(audio_file.name).suffix.lower()
                    or ".wav"
                )

                # Save the upload temporarily so the existing
                # voice service can process it.
                with tempfile.NamedTemporaryFile(
                    suffix=audio_suffix,
                    prefix="lead-desk-",
                    delete=False,
                ) as temporary_audio:

                    temporary_audio.write(
                        audio_file.getvalue()
                    )

                    temporary_audio_path = Path(
                        temporary_audio.name
                    )

                with st.spinner(
                    "Transcribing, answering, and generating speech..."
                ):

                    result = process_voice_message(
                        audio_path=temporary_audio_path,
                        rag_service=rag_service,
                        gemini_client=gemini_client,
                        output_dir=VOICE_OUTPUT_DIR,
                    )

                st.session_state.last_voice_result = result

                st.success(
                    "Voice message processed successfully."
                )

        except Exception as exc:

            st.error(
                f"Voice processing failed: "
                f"{type(exc).__name__}: {exc}"
            )

        finally:

            if (
                temporary_audio_path is not None
                and temporary_audio_path.exists()
            ):

                temporary_audio_path.unlink()

    # Display the last successfully processed voice inquiry.
    voice_result = st.session_state.last_voice_result

    if voice_result:

        st.divider()

        st.markdown("**Transcription**")

        st.write(
            voice_result.get("transcript", "")
        )

        st.markdown("**Detected Language**")

        st.write(
            voice_result.get("language", "unknown")
        )

        st.markdown("**Counselor Answer**")

        st.markdown(
            voice_result.get("answer", "")
        )

        show_sources(voice_result)

        # Play the generated spoken answer.
        audio_path_value = voice_result.get("audio_path")

        if audio_path_value:

            generated_audio_path = Path(audio_path_value)

            if generated_audio_path.is_file():

                st.markdown("**Generated Voice Reply**")

                st.audio(
                    generated_audio_path.read_bytes(),
                    format="audio/wav",
                )

        with st.expander("Processing Timings"):

            st.json(
                voice_result.get("timings", {})
            )

        if st.button(
            "Flag Voice Inquiry for Counselor Follow-up",
            key="voice_followup",
        ):

            added = add_followup(
                question=voice_result.get(
                    "transcript",
                    "",
                ),
                answer=voice_result.get(
                    "answer",
                    "",
                ),
                sources=voice_result.get(
                    "sources",
                    [],
                ),
                answer_mode=voice_result.get(
                    "answer_mode",
                    "unknown",
                ),
            )

            if added:

                st.success(
                    "Voice inquiry added to the counselor queue."
                )

            else:

                st.info(
                    "This inquiry is already in the queue."
                )


# =========================================================
# 12. KNOWLEDGE BASE
# =========================================================

with knowledge_tab:

    st.subheader("Institute Knowledge Base")

    st.write(
        "The RAG service reads supported document files from:"
    )

    st.code(str(DOCUMENTS_DIR))

    # Refresh the visible file list.
    current_document_files = get_document_files()

    if current_document_files:

        for document_path in current_document_files:
            st.write(f"📄 {document_path.name}")

    else:

        st.info(
            "No supported institute documents were found."
        )

    st.metric(
        "Currently Indexed Chunks",
        len(rag_service.document_chunks),
    )

    st.caption(
        "This version displays document status. Document uploading, "
        "approval, and re-indexing controls have not been implemented yet."
    )

    st.info(
        "Adding a new file to the folder does not automatically rebuild "
        "the existing RAG index. Re-indexing must be implemented separately."
    )


# =========================================================
# 13. COUNSELOR FOLLOW-UP QUEUE
# =========================================================

with followup_tab:

    st.subheader("Counselor Review Queue")

    st.caption(
        "This queue is stored in Streamlit session state only. "
        "It is not a persistent lead database."
    )

    if not st.session_state.followups:

        st.info(
            "No inquiries have been flagged. Use the follow-up button "
            "under a text or voice answer to add an inquiry."
        )

    else:

        if st.button(
            "Clear Session Follow-up Queue",
            key="clear_followups",
        ):

            st.session_state.followups = []

            st.rerun()

        for index, item in enumerate(
            st.session_state.followups,
            start=1,
        ):

            question_preview = item["question"][:80]

            with st.expander(
                f"Inquiry {index}: {question_preview}"
            ):

                st.markdown("**Student Question**")

                st.write(item["question"])

                st.markdown("**AI Answer**")

                st.write(item["answer"])

                st.write(
                    "Answer Mode:",
                    item.get("answer_mode", "unknown"),
                )

                st.markdown("**Retrieved Sources**")

                sources = item.get("sources") or []

                if sources:

                    for source in sources:

                        st.write(
                            f"Document: "
                            f"{source.get('source', 'Unknown')}"
                        )

                        st.write(
                            f"Chunk ID: "
                            f"{source.get('chunk_id', 'N/A')}"
                        )

                else:

                    st.write(
                        "No retrieved source documents were recorded."
                    )