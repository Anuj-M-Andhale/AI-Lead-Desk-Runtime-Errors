import os
import requests
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
# COUNSELOR BACKEND API
# =========================================================

COUNSELOR_API_URL = (
    os.getenv(
        "AI_LEAD_DESK_API_URL",
        "http://127.0.0.1:8001",
    ).strip()
    or "http://127.0.0.1:8001"
).rstrip("/")


def get_counselor_api_headers():
    """Return authenticated API headers without exposing the key."""
    api_key = os.getenv("COUNSELOR_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "COUNSELOR_API_KEY is missing. Configure it in the project .env "
            "with the same key used by the backend API."
        )

    return {"X-API-Key": api_key}


def get_counselor_api_error(response):
    """Extract a concise message from an API error response."""
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    detail = payload.get("detail") or payload.get("message")

    if not detail:
        detail = f"HTTP {response.status_code}"

    return str(detail)[:350]



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
        for path in DOCUMENTS_DIR.rglob('*')
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
    "Counselor Inbox",
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

text_tab, voice_tab, knowledge_tab, inbox_tab, followup_tab = st.tabs(
    [
        "💬 Text Inquiries",
        "🎙️ Voice Inquiries",
        "📚 Knowledge Base",
        "Counselor Inbox",
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
        "Upload institute reference documents here. The backend accepts "
        "PDF and DOCX files up to 15 MB and attempts to index each upload."
    )

    st.caption(f"Backend API: {COUNSELOR_API_URL}")

    # Display the result of the most recent explicit re-index operation.
    kb_notice = st.session_state.pop("kb_notice", None)

    if kb_notice:
        st.success(kb_notice)

    uploaded_document = st.file_uploader(
        "Upload institute document",
        type=["pdf", "docx"],
        help="Select a PDF or Word document, maximum 15 MB.",
        key="kb_document_uploader",
    )

    upload_column, reindex_column = st.columns(2)

    with upload_column:
        upload_clicked = st.button(
            "Upload and index",
            key="kb_upload_button",
            disabled=uploaded_document is None,
            use_container_width=True,
        )

    with reindex_column:
        reindex_clicked = st.button(
            "Re-index all documents",
            key="kb_reindex_button",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # UPLOAD DOCUMENT
    # -----------------------------------------------------

    if upload_clicked and uploaded_document is not None:

        if uploaded_document.size > 15 * 1024 * 1024:
            st.error("The document exceeds the backend's 15 MB file limit.")

        else:
            try:
                response = requests.post(
                    f"{COUNSELOR_API_URL}/api/documents/upload",
                    headers=get_counselor_api_headers(),
                    files={
                        "file": (
                            uploaded_document.name,
                            uploaded_document.getvalue(),
                            uploaded_document.type
                            or "application/octet-stream",
                        )
                    },
                    timeout=(10, 300),
                )

                if not response.ok:
                    st.error(
                        "Upload failed: "
                        + get_counselor_api_error(response)
                    )

                else:
                    result = response.json()

                    filename = result.get(
                        "filename",
                        uploaded_document.name,
                    )

                    index_status = result.get(
                        "index_status",
                        "unknown",
                    )

                    if index_status == "indexed":
                        st.success(
                            f"{filename} was uploaded. "
                            "The backend reports it as indexed."
                        )
                    else:
                        st.warning(
                            f"{filename} was stored, but indexing is pending. "
                            "Check the backend logs and embedding service, "
                            "then retry re-indexing."
                        )

                    # Update the RAG instance used by this Streamlit process.
                    try:
                        refreshed = rag_service.refresh_index_if_changed()

                        if refreshed:
                            st.info(
                                "The dashboard's local RAG index was refreshed."
                            )

                    except Exception as refresh_exc:
                        st.warning(
                            "The upload response was received, but the "
                            "dashboard's local RAG index could not refresh. "
                            "Check the local embedding service. "
                            f"Error type: {type(refresh_exc).__name__}."
                        )

            except RuntimeError as exc:
                st.error(str(exc))

            except requests.RequestException as exc:
                st.error(
                    "Could not reach the document API. Confirm that the "
                    "backend is running on the configured URL. "
                    f"Error type: {type(exc).__name__}."
                )

            except ValueError:
                st.error(
                    "The document API returned an unreadable response."
                )

    # -----------------------------------------------------
    # RE-INDEX ALL DOCUMENTS
    # -----------------------------------------------------

    if reindex_clicked:

        try:
            response = requests.post(
                f"{COUNSELOR_API_URL}/api/documents/reindex",
                headers=get_counselor_api_headers(),
                timeout=(10, 900),
            )

            if not response.ok:
                st.error(
                    "Re-index failed: "
                    + get_counselor_api_error(response)
                )

            else:
                result = response.json()

                document_count = result.get("documents")
                chunk_count = result.get("chunks")

                summary = "Backend re-index completed."

                if document_count is not None:
                    summary += f" Documents: {document_count}."

                if chunk_count is not None:
                    summary += f" Chunks: {chunk_count}."

                st.session_state["kb_notice"] = summary

                # Recreate Streamlit's own cached RAG instance on rerun.
                get_rag_service.clear()
                st.rerun()

        except RuntimeError as exc:
            st.error(str(exc))

        except requests.RequestException as exc:
            st.error(
                "Could not complete the re-index request. Check the backend "
                "and embedding service. "
                f"Error type: {type(exc).__name__}."
            )

        except ValueError:
            st.error(
                "The re-index endpoint returned an unreadable response."
            )

    # -----------------------------------------------------
    # DOCUMENT STATUS TABLE
    # -----------------------------------------------------

    st.divider()
    st.subheader("Stored Documents")

    st.metric(
        "Dashboard Indexed Chunks",
        len(rag_service.document_chunks),
    )

    try:
        listing_response = requests.get(
            f"{COUNSELOR_API_URL}/api/documents",
            headers=get_counselor_api_headers(),
            timeout=(5, 20),
        )

        if not listing_response.ok:
            st.warning(
                "Could not load the document list: "
                + get_counselor_api_error(listing_response)
            )

        else:
            listing_payload = listing_response.json()
            documents = listing_payload.get("documents", [])

            st.metric("Stored Documents", len(documents))

            if documents:
                table_rows = []

                for document in documents:
                    filename = document.get("filename", "Unknown")

                    # Support either size_bytes or size in the API response.
                    size_bytes = document.get(
                        "size_bytes",
                        document.get("size", 0),
                    ) or 0

                    try:
                        size_mb = round(float(size_bytes) / (1024 * 1024), 2)
                    except (TypeError, ValueError):
                        size_mb = 0.0

                    table_rows.append({
                        "Document": filename,
                        "Type": document.get(
                            "extension",
                            Path(filename).suffix.lower(),
                        ),
                        "Size (MB)": size_mb,
                        "Index Status": document.get(
                            "index_status",
                            document.get("status", "unknown"),
                        ),
                        "Stored Path": document.get("relative_path", ""),
                    })

                st.dataframe(
                    table_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:
                st.info(
                    "No supported documents are currently listed by the API."
                )

    except RuntimeError as exc:
        st.error(str(exc))

    except requests.RequestException as exc:
        st.warning(
            "The document list is currently unavailable. "
            f"Error type: {type(exc).__name__}."
        )

    except ValueError:
        st.warning(
            "The document API returned an unreadable list response."
        )



# =========================================================

# =========================================================
# 13. COUNSELOR INBOX
# =========================================================

with inbox_tab:

    st.subheader("Telegram Counselor Inbox")
    st.caption(
        "Review conversations, take over from AI, and reply in the "
        "student's existing Telegram chat."
    )

    inbox_notice = st.session_state.pop("inbox_notice", None)
    if inbox_notice:
        st.success(inbox_notice)

    if st.button("Refresh inbox", key="counselor_refresh_inbox"):
        st.rerun()

    try:
        inbox_response = requests.get(
            f"{COUNSELOR_API_URL}/api/conversations",
            params={"platform": "telegram", "limit": 200},
            headers=get_counselor_api_headers(),
            timeout=(5, 20),
        )

        if not inbox_response.ok:
            st.error(
                "Could not load conversations: "
                + get_counselor_api_error(inbox_response)
            )
            conversations = []

        else:
            conversations = inbox_response.json().get(
                "conversations", []
            )

    except RuntimeError as exc:
        st.error(str(exc))
        conversations = []

    except requests.RequestException as exc:
        st.error(
            "The conversation API is unavailable. Make sure the backend "
            "has been restarted with the latest code. "
            f"Error type: {type(exc).__name__}."
        )
        conversations = []

    except ValueError:
        st.error("The conversation API returned an invalid response.")
        conversations = []

    if not conversations:
        st.info(
            "No Telegram conversations were found yet. Start the Telegram "
            "bot, send it a message from a student account, then refresh."
        )

    else:
        # Telegram user IDs are unique in the existing leads table.
        conversation_by_id = {
            str(item["platform_user_id"]): item
            for item in conversations
        }
        conversation_ids = list(conversation_by_id)

        def _inbox_label(user_id):
            item = conversation_by_id[user_id]
            student_name = item.get("name") or "Student"
            mode = (item.get("handling_mode") or "ai").upper()
            unread = item.get("unread_count", 0) or 0
            last_message = str(item.get("last_message") or "").replace(
                "\n", " "
            )[:48]

            return (
                f"{student_name} | ID {user_id} | {mode} | "
                f"{unread} unread | {last_message}"
            )

        previous_selection = st.session_state.get(
            "counselor_selected_telegram_uid"
        )
        selected_index = (
            conversation_ids.index(previous_selection)
            if previous_selection in conversation_ids
            else 0
        )

        selected_uid = st.selectbox(
            "Select conversation",
            options=conversation_ids,
            index=selected_index,
            format_func=_inbox_label,
            key="counselor_selected_telegram_uid",
        )

        selected = conversation_by_id[selected_uid]
        current_mode = selected.get("handling_mode") or "ai"

        st.divider()

        student_col, mode_col, unread_col = st.columns(3)

        with student_col:
            st.metric("Student", selected.get("name") or "Unknown")

        with mode_col:
            st.metric("Handling mode", current_mode.upper())

        with unread_col:
            st.metric(
                "Unread messages",
                selected.get("unread_count", 0) or 0,
            )

        if not selected.get("chat_id"):
            st.warning(
                "This conversation has no stored Telegram chat destination. "
                "Ask the student to send a new message to the bot after "
                "the updated bot has been restarted."
            )

        action_col, resume_col = st.columns(2)

        with action_col:
            if current_mode != "human":
                if st.button(
                    "Take over conversation",
                    key=f"takeover_{selected_uid}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        action_response = requests.post(
                            f"{COUNSELOR_API_URL}/api/conversations/"
                            f"telegram/{selected_uid}/takeover",
                            headers=get_counselor_api_headers(),
                            timeout=(5, 20),
                        )

                        if action_response.ok:
                            result = action_response.json()
                            st.session_state["inbox_notice"] = result.get(
                                "message", "Human takeover enabled."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Takeover failed: "
                                + get_counselor_api_error(action_response)
                            )

                    except RuntimeError as exc:
                        st.error(str(exc))
                    except requests.RequestException as exc:
                        st.error(
                            f"Takeover request failed: {type(exc).__name__}."
                        )

        with resume_col:
            if current_mode == "human":
                if st.button(
                    "Resume AI",
                    key=f"resume_{selected_uid}",
                    use_container_width=True,
                ):
                    try:
                        action_response = requests.post(
                            f"{COUNSELOR_API_URL}/api/conversations/"
                            f"telegram/{selected_uid}/resume",
                            headers=get_counselor_api_headers(),
                            timeout=(5, 20),
                        )

                        if action_response.ok:
                            st.session_state["inbox_notice"] = (
                                "AI handling resumed."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Resume failed: "
                                + get_counselor_api_error(action_response)
                            )

                    except RuntimeError as exc:
                        st.error(str(exc))
                    except requests.RequestException as exc:
                        st.error(
                            f"Resume request failed: {type(exc).__name__}."
                        )

        st.divider()
        st.subheader("Conversation History")

        try:
            history_response = requests.get(
                f"{COUNSELOR_API_URL}/api/conversations/"
                f"telegram/{selected_uid}/messages",
                params={"limit": 300},
                headers=get_counselor_api_headers(),
                timeout=(5, 20),
            )

            if not history_response.ok:
                st.error(
                    "Could not load message history: "
                    + get_counselor_api_error(history_response)
                )
                history_data = {}
            else:
                history_data = history_response.json()

        except RuntimeError as exc:
            st.error(str(exc))
            history_data = {}
        except requests.RequestException as exc:
            st.error(
                f"Message history request failed: {type(exc).__name__}."
            )
            history_data = {}
        except ValueError:
            st.error("Message history was returned in an invalid format.")
            history_data = {}

        conversation_details = history_data.get("conversation", {})
        messages = history_data.get("messages", [])

        if conversation_details.get("handling_mode"):
            current_mode = conversation_details["handling_mode"]

        if not messages:
            st.info("No messages are available for this conversation yet.")

        else:
            for chat_message in messages:
                direction = chat_message.get("direction", "")
                sender_type = chat_message.get("sender_type", "")

                if direction == "inbound":
                    role = "user"
                    sender_label = "Student"
                else:
                    role = "assistant"
                    sender_label = {
                        "counselor": "Human Counselor",
                        "system": "System",
                        "ai": "AI Counselor",
                    }.get(sender_type, "Outgoing message")

                with st.chat_message(role):
                    st.caption(
                        f"{sender_label} ? "
                        f"{chat_message.get('created_at', '')}"
                    )
                    # Plain text avoids rendering student messages as Markdown.
                    st.text(str(chat_message.get("content", "")))

        # Mark the messages currently shown as read.
        try:
            requests.post(
                f"{COUNSELOR_API_URL}/api/conversations/"
                f"telegram/{selected_uid}/read",
                headers=get_counselor_api_headers(),
                timeout=(5, 10),
            )
        except (RuntimeError, requests.RequestException):
            pass

        st.divider()

        if current_mode == "human":

            st.subheader("Reply to Student")

            with st.form(key=f"counselor_reply_form_{selected_uid}"):
                reply_text = st.text_area(
                    "Your message",
                    max_chars=4000,
                    height=100,
                    key=f"counselor_reply_text_{selected_uid}",
                    placeholder="Write your reply...",
                )

                send_clicked = st.form_submit_button(
                    "Send reply to Telegram",
                    type="primary",
                    use_container_width=True,
                )

            if send_clicked:
                if not reply_text.strip():
                    st.error("Write a message before sending.")
                else:
                    try:
                        reply_response = requests.post(
                            f"{COUNSELOR_API_URL}/api/conversations/"
                            f"telegram/{selected_uid}/reply",
                            headers=get_counselor_api_headers(),
                            json={
                                "content": reply_text.strip(),
                                "counselor": os.getenv(
                                    "COUNSELOR_NAME", "counselor"
                                ).strip() or "counselor",
                            },
                            timeout=(5, 30),
                        )

                        if reply_response.ok:
                            st.session_state["inbox_notice"] = (
                                "Reply sent to Telegram."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Reply failed: "
                                + get_counselor_api_error(reply_response)
                            )

                    except RuntimeError as exc:
                        st.error(str(exc))
                    except requests.RequestException as exc:
                        st.error(
                            f"Reply request failed: {type(exc).__name__}."
                        )

        else:
            st.info(
                "AI is handling this conversation. Click "
                "'Take over conversation' before sending a counselor reply."
            )

        with st.expander("Conversation Activity / Audit Trail"):
            try:
                events_response = requests.get(
                    f"{COUNSELOR_API_URL}/api/conversations/"
                    f"telegram/{selected_uid}/events",
                    params={"limit": 100},
                    headers=get_counselor_api_headers(),
                    timeout=(5, 15),
                )

                if events_response.ok:
                    events = events_response.json().get("events", [])
                    if events:
                        st.dataframe(
                            [
                                {
                                    "Event": event.get("event_type", ""),
                                    "Actor": event.get("actor", ""),
                                    "Details": event.get("details", ""),
                                    "Time": event.get("created_at", ""),
                                }
                                for event in events
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.caption("No counselor actions recorded yet.")
                else:
                    st.warning("Could not load the activity history.")

            except (RuntimeError, requests.RequestException):
                st.warning("The activity history is currently unavailable.")


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