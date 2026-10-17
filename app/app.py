import html
import os
import sys
import tempfile
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai

# ============================================================
# 1. CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
DOCUMENTS_DIR = PROJECT_DIR / "data" / "institute_documents"
VOICE_OUTPUT_DIR = PROJECT_DIR / "data" / "voice_outputs"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(PROJECT_DIR / ".env")

from ai_lead_desk.rag_service import DocumentRAGService
from ai_lead_desk.voice_service import process_voice_message

COUNSELOR_API_URL = (
    os.getenv(
        "AI_LEAD_DESK_API_URL",
        "http://127.0.0.1:8001",
    ).strip()
    or "http://127.0.0.1:8001"
).rstrip("/")

MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_DOCUMENT_BYTES = 15 * 1024 * 1024

SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

st.set_page_config(
    page_title="AI Lead Desk",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 2. COMPLETE THEME — MATCHING REFERENCE DESIGN
# ============================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap'
    );

    :root {
        --navy-primary: #12345A;
        --navy-dark: #0B1F3A;
        --blue-secondary: #245A8D;
        --blue-accent: #3B82F6;
        --blue-brand: #2563EB;
        --blue-hover: #1D4ED8;
        --teal-accent: #14B8A6;
        --page-bg: #F4F7FB;
        --card-bg: #FFFFFF;
        --text-main: #172B4D;
        --text-secondary: #64748B;
        --text-muted: #94A3B8;
        --border-subtle: #DCE5EF;
        --border-light: #F1F5F9;
        --soft-blue: #EFF6FF;
        --soft-green: #CCFBF1;
        --soft-amber: #FFF7ED;
        --soft-red: #FFE4E6;
        --soft-purple: #EDE9FE;
    }

    /* ---------- GLOBAL ---------- */

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont,
                     'Segoe UI', Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background-color: var(--page-bg);
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1550px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    [data-testid="stHeader"] {
        background-color: var(--page-bg);
    }

    /* Custom scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--page-bg); }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ---------- MAIN CONTENT TEXT ---------- */

    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] em,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] h4 {
        color: var(--text-main);
    }

    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
        color: var(--text-secondary) !important;
    }

    [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
        color: var(--text-main) !important;
    }

    /* ---------- SIDEBAR ---------- */

    [data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 16rem !important;
        min-width: 16rem !important;
        flex-shrink: 0 !important;
    }

    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background-color: var(--navy-dark) !important;
    }

    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 1000000 !important;
    }

    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] button {
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: var(--text-muted) !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #1A3358 !important;
    }

    /* Sidebar brand lockup */
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 16px 16px 16px;
        border-bottom: 1px solid #1A3358;
        margin-bottom: 8px;
    }

    .brand-icon-wrap {
        color: #FFFFFF;
        flex-shrink: 0;
        font-size: 24px;
        line-height: 1;
    }

    .brand-text-wrap {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .brand-name {
        color: #FFFFFF !important;
        font-size: 17px;
        font-weight: 700;
        letter-spacing: -0.3px;
        line-height: 1;
    }

    .brand-chevron {
        color: var(--text-secondary) !important;
        font-size: 11px;
        opacity: 0.7;
    }

    /* Sidebar nav radio buttons */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
        display: none;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 3px;
        padding: 4px 12px;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label {
        background: transparent !important;
        color: var(--text-muted) !important;
        border-radius: 12px;
        padding: 10px 14px;
        margin: 0;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.15s ease;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] label span {
        color: inherit !important;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: #132B4F !important;
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"]
    [data-testid="stRadio"] label:has(input:checked) {
        background: var(--blue-brand) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        font-weight: 600;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] input {
        display: none;
    }

    /* Sidebar status panel */
    .sidebar-status {
        margin: 12px 12px 0;
        padding: 14px;
        background: #08182E;
        border: 1px solid #1A3358;
        border-radius: 14px;
    }

    .sidebar-status-title {
        color: #FFFFFF !important;
        font-size: 12px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .sidebar-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }

    .sidebar-status-dot-ok { background: #22C55E; }
    .sidebar-status-dot-warn { background: #F59E0B; }

    .sidebar-status-copy {
        color: #94A3B8 !important;
        font-size: 11.5px;
        line-height: 1.7;
        margin-top: 8px;
        overflow-wrap: anywhere;
    }

    /* ---------- PAGE HEADER ---------- */

    .page-header-wrap {
        margin-bottom: 20px;
    }

    .page-heading {
        color: var(--text-main) !important;
        font-size: 26px;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.6px;
        margin: 0;
    }

    .page-subtitle {
        color: var(--text-secondary) !important;
        font-size: 14px;
        font-weight: 500;
        line-height: 1.5;
        margin-top: 4px;
    }

    /* ---------- SECTION HEADINGS ---------- */

    .section-heading {
        color: var(--text-main) !important;
        font-size: 17px;
        font-weight: 700;
        letter-spacing: -0.2px;
        line-height: 1.4;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .section-heading-icon {
        font-size: 16px;
        opacity: 0.85;
    }

    .section-subtitle {
        color: var(--text-secondary) !important;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.5;
        margin-top: 2px;
        margin-bottom: 14px;
    }

    /* ---------- METRIC CARDS (REFERENCE DESIGN) ---------- */

    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 20px;
        min-height: 140px;
        box-shadow: 0 2px 8px rgba(18, 52, 90, 0.04);
        overflow-wrap: anywhere;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -4px rgba(18, 52, 90, 0.08);
    }

    .metric-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
    }

    .metric-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .metric-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
        transition: transform 0.2s ease;
    }

    .metric-card:hover .metric-icon {
        transform: scale(1.05);
    }

    .metric-label {
        color: var(--text-secondary) !important;
        font-size: 13.5px;
        font-weight: 600;
    }

    .metric-value {
        color: var(--text-main) !important;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
        line-height: 1;
        margin-top: 4px;
    }

    .metric-chevron {
        color: var(--text-muted);
        font-size: 14px;
        margin-top: 2px;
        transition: all 0.2s ease;
    }

    .metric-card:hover .metric-chevron {
        color: var(--blue-brand);
        transform: translateX(2px);
    }

    .metric-foot {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--border-light);
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
    }

    .metric-trend-up {
        color: #16A34A !important;
        font-weight: 600;
    }

    .metric-trend-down {
        color: #16A34A !important;
        font-weight: 600;
    }

    .metric-trend-text {
        color: var(--text-muted) !important;
    }

    /* ---------- PANELS ---------- */

    .panel {
        background: var(--card-bg);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(18, 52, 90, 0.04);
    }

    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--border-light);
        margin-bottom: 14px;
    }

    .panel-header-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .panel-header-icon {
        font-size: 18px;
        color: var(--blue-brand);
    }

    .panel-title {
        font-size: 17px;
        font-weight: 700;
        color: var(--text-main) !important;
        letter-spacing: -0.2px;
    }

    /* ---------- PILL BADGES ---------- */

    .pill {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.2px;
    }

    .pill-blue {
        background: #EFF6FF;
        color: #2563EB !important;
        border: 1px solid #BFDBFE;
    }

    .pill-green {
        background: #ECFDF5;
        color: #047857 !important;
        border: 1px solid #A7F3D0;
    }

    .pill-amber {
        background: #FFFBEB;
        color: #92400E !important;
        border: 1px solid #FDE68A;
    }

    .pill-red {
        background: #FEF2F2;
        color: #DC2626 !important;
        border: 1px solid #FECACA;
    }

    .pill-live {
        background: #ECFDF5;
        color: #047857 !important;
        border: 1px solid #A7F3D0;
        animation: pulse-live 2s infinite;
    }

    @keyframes pulse-live {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* ---------- INSIGHT ROWS ---------- */

    .insight-row {
        padding: 14px 16px;
        border: 1px solid var(--border-light);
        background: #F8FAFC;
        border-radius: 12px;
        margin-bottom: 8px;
        transition: border-color 0.2s ease;
    }

    .insight-row:hover {
        border-color: #CBD5E1;
    }

    .insight-title {
        color: var(--text-main) !important;
        font-size: 13.5px;
        font-weight: 700;
        line-height: 1.5;
    }

    .insight-copy {
        color: #475569 !important;
        font-size: 12.5px;
        line-height: 1.6;
        margin-top: 4px;
    }

    /* ---------- INPUTS ---------- */

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        color: var(--text-main) !important;
        background-color: #FFFFFF !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        caret-color: var(--blue-accent);
        font-size: 13.5px !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: var(--blue-accent) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12) !important;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: var(--text-muted) !important;
        opacity: 1;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-color: var(--border-subtle) !important;
        color: var(--text-main) !important;
        border-radius: 12px !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] span,
    [data-testid="stMultiSelect"] [data-baseweb="select"] span {
        color: var(--text-main) !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-subtle) !important;
        box-shadow: 0 10px 25px -5px rgba(18, 52, 90, 0.1) !important;
    }

    [role="option"],
    [role="option"] * {
        color: var(--text-main) !important;
    }

    [role="option"][aria-selected="true"] {
        background-color: var(--soft-blue) !important;
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background-color: #FFFFFF;
        color: var(--text-main) !important;
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        min-height: 40px;
        font-weight: 600;
        font-size: 13.5px;
        transition: all 0.15s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        border-color: var(--blue-brand);
        color: var(--blue-hover) !important;
        background: #F8FAFC;
    }

    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, var(--navy-primary), #1A4574) !important;
        border-color: var(--navy-primary) !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(18, 52, 90, 0.2);
    }

    .stButton > button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1A4574, var(--navy-primary)) !important;
        border-color: #1A4574 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(18, 52, 90, 0.3);
    }

    /* ---------- DATA TABLES ---------- */

    [data-testid="stDataFrame"] {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(18, 52, 90, 0.04);
    }

    /* ---------- CHAT MESSAGES ---------- */

    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(18, 52, 90, 0.03);
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] em,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] blockquote {
        color: var(--text-main) !important;
        opacity: 1 !important;
        -webkit-text-fill-color: var(--text-main) !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] a {
        color: var(--blue-hover) !important;
        -webkit-text-fill-color: var(--blue-hover) !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
        background-color: var(--border-light) !important;
        border-radius: 6px;
        padding: 2px 6px;
    }

    /* ---------- EXPANDERS ---------- */

    [data-testid="stExpander"] {
        background: #FFFFFF;
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
    }

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        color: var(--text-main) !important;
    }

    /* ---------- ALERTS ---------- */

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* ---------- METRICS (st.metric) ---------- */

    [data-testid="stMetric"] {
        background: var(--card-bg);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 16px !important;
        box-shadow: 0 2px 8px rgba(18, 52, 90, 0.04);
    }

    [data-testid="stMetricLabel"] p {
        color: var(--text-secondary) !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text-main) !important;
        font-weight: 700 !important;
    }

    /* ---------- FOOTER ---------- */

    .footer-note {
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid var(--border-subtle);
        color: var(--text-secondary) !important;
        font-size: 11px;
        text-align: center;
        font-weight: 500;
    }

    /* ---------- RESPONSIVE ---------- */

    @media (max-width: 800px) {
        .page-heading {
            font-size: 22px;
        }

        .metric-card {
            min-height: 120px;
            padding: 16px;
        }

        .metric-value {
            font-size: 24px;
        }

        .metric-icon {
            width: 40px;
            height: 40px;
            font-size: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 3. BACKEND API HELPERS
# ============================================================


def get_api_headers():
    api_key = os.getenv("COUNSELOR_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "COUNSELOR_API_KEY is missing from .env."
        )

    return {"X-API-Key": api_key}


def api_error(response):
    try:
        data = response.json()
    except ValueError:
        data = {}

    return str(
        data.get("detail")
        or data.get("message")
        or f"HTTP {response.status_code}"
    )[:350]


def api_get(path, params=None, timeout=(5, 20)):
    return requests.get(
        f"{COUNSELOR_API_URL}{path}",
        params=params,
        headers=get_api_headers(),
        timeout=timeout,
    )


def api_post(path, json_body=None, files=None, timeout=(5, 30)):
    kwargs = {
        "headers": get_api_headers(),
        "timeout": timeout,
    }

    if json_body is not None:
        kwargs["json"] = json_body

    if files is not None:
        kwargs["files"] = files

    return requests.post(
        f"{COUNSELOR_API_URL}{path}",
        **kwargs,
    )


def load_conversations(platform="telegram", limit=200):
    response = api_get(
        "/api/conversations",
        params={"platform": platform, "limit": limit},
    )

    if not response.ok:
        raise RuntimeError(api_error(response))

    return response.json().get("conversations", [])


def load_documents():
    response = api_get("/api/documents")

    if not response.ok:
        raise RuntimeError(api_error(response))

    return response.json().get("documents", [])


# ============================================================
# 4. AI SERVICE INITIALIZATION
# ============================================================


@st.cache_resource(show_spinner="Loading institute knowledge base...")
def get_rag_service(project_dir):
    return DocumentRAGService(project_dir=project_dir)


@st.cache_resource
def get_gemini_client():
    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key) if api_key else None


DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
VOICE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    rag_service = get_rag_service(str(PROJECT_DIR))
    rag_error = ""
except Exception as exc:
    rag_service = None
    rag_error = f"{type(exc).__name__}: {exc}"

try:
    gemini_client = get_gemini_client()
    gemini_error = ""
except Exception as exc:
    gemini_client = None
    gemini_error = type(exc).__name__

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

if "last_voice_result" not in st.session_state:
    st.session_state.last_voice_result = None

PAGES = [
    "Overview",
    "Text Inquiries",
    "Voice Inquiries",
    "Counselor Inbox",
    "Knowledge Base",
]

if (
    "navigation_page" not in st.session_state
    or st.session_state.navigation_page not in PAGES
):
    st.session_state.navigation_page = "Overview"


# ============================================================
# 5. REUSABLE UI COMPONENTS
# ============================================================


def page_header(section, title, subtitle):
    st.markdown(
        f"""
        <div class="page-header-wrap">
            <h1 class="page-heading">{html.escape(title)}</h1>
            <div class="page-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_heading(title, subtitle=None, badge=None):
    badge_html = ""

    if badge:
        pill_class = "pill-live" if badge == "LIVE" else "pill-blue"
        badge_html = (
            f' <span class="pill {pill_class}">'
            f'{html.escape(str(badge))}</span>'
        )

    st.markdown(
        f'<div class="section-heading">'
        f'{html.escape(title)}{badge_html}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">'
            f'{html.escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def metric_card(label, value, icon, note, bg, fg):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-left">
                    <span class="metric-icon"
                        style="background:{bg};color:{fg}">
                        {icon}
                    </span>
                    <div>
                        <div class="metric-label">
                            {html.escape(str(label))}
                        </div>
                        <div class="metric-value">
                            {html.escape(str(value))}
                        </div>
                    </div>
                </div>
                <span class="metric-chevron">›</span>
            </div>
            <div class="metric-foot">
                <span class="metric-trend-text">
                    {html.escape(str(note))}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_sources(record):
    with st.expander("Evidence and retrieved sources"):
        if record.get("grounded") is True:
            st.write(
                "The RAG service marked this answer as grounded. "
                "This does not independently verify every generated claim."
            )
        else:
            st.warning(
                "This answer was not marked as grounded in retrieved evidence."
            )

        st.write("Answer mode:", record.get("answer_mode", "unknown"))

        sources = record.get("sources") or []

        if not sources:
            st.write("No retrieved sources were returned.")
            return

        for source in sources:
            st.write("**Document:**", source.get("source", "Unknown"))
            st.write("**Chunk ID:**", source.get("chunk_id", "N/A"))

            if source.get("similarity") is not None:
                st.write(
                    "**Retrieval similarity:**",
                    source["similarity"],
                )

            st.divider()


def get_local_document_files():
    return sorted(
        path
        for path in DOCUMENTS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    )


def navigate_to(page_name):
    st.session_state.navigation_page = page_name


# ============================================================
# 6. SIDEBAR
# ============================================================

with st.sidebar:
    rag_dot = "sidebar-status-dot-ok" if rag_service else "sidebar-status-dot-warn"

    st.markdown(
        f"""
        <div class="brand-lockup">
            <div class="brand-icon-wrap">🎓</div>
            <div class="brand-text-wrap">
                <span class="brand-name">AI Lead Desk</span>
                <span class="brand-chevron">⇅</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        PAGES,
        key="navigation_page",
        label_visibility="collapsed",
        format_func=lambda value: {
            "Overview": "⌂   Overview",
            "Text Inquiries": "💬   Text Inquiries",
            "Voice Inquiries": "🎙   Voice Inquiries",
            "Counselor Inbox": "📥   Counselor Inbox",
            "Knowledge Base": "📚   Knowledge Base",
        }.get(value, value),
    )

    st.markdown("---")

    st.markdown(
        f"""
        <div class="sidebar-status">
            <div class="sidebar-status-title">
                <span class="sidebar-status-dot {rag_dot}"></span>
                System status
            </div>
            <div class="sidebar-status-copy">
                RAG: {"Ready" if rag_service else "Needs attention"}<br>
                Voice: {"Configured" if gemini_client else "Not configured"}<br>
                API: {html.escape(COUNSELOR_API_URL)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Prototype · AI-assisted admissions")


local_documents = get_local_document_files()
document_chunks = (
    len(rag_service.document_chunks)
    if rag_service
    else 0
)

if not rag_service:
    st.warning(
        "RAG initialization failed. Text and voice answering will not "
        "work until the configuration is fixed."
    )

    with st.expander("RAG initialization details"):
        st.code(rag_error)


# ============================================================
# 7. OVERVIEW
# ============================================================

if page == "Overview":
    page_header(
        "Overview",
        "Overview",
        "Welcome back! Here's your admissions overview.",
    )

    api_online = False
    conversations = []
    api_problem = ""

    try:
        conversations = load_conversations()
        api_online = True
    except (
        RuntimeError,
        requests.RequestException,
        ValueError,
    ) as exc:
        api_problem = f"{type(exc).__name__}: {str(exc)[:180]}"

    total = len(conversations)

    human_count = sum(
        1
        for item in conversations
        if (item.get("handling_mode") or "ai").lower() == "human"
    )

    ai_count = max(total - human_count, 0)

    unread_count = sum(
        int(item.get("unread_count", 0) or 0)
        for item in conversations
    )

    columns = st.columns(4, gap="medium")

    cards = [
        (
            "Conversations",
            total if api_online else "—",
            "👥",
            "Live Telegram records",
            "#EFF6FF",
            "#2563EB",
        ),
        (
            "AI handling",
            ai_count if api_online else "—",
            "🔥",
            "Conversations in AI mode",
            "#CCFBF1",
            "#0D9488",
        ),
        (
            "Counselor handling",
            human_count if api_online else "—",
            "🗓",
            "Manual takeover active",
            "#FFF7ED",
            "#EA580C",
        ),
        (
            "Indexed chunks",
            document_chunks if rag_service else "—",
            "📄",
            f"{len(local_documents)} local document files",
            "#FFE4E6",
            "#EF4444",
        ),
    ]

    for column, values in zip(columns, cards):
        with column:
            metric_card(*values)

    st.write("")

    left, right = st.columns([1.65, 1], gap="large")

    with left:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-header-left">
                        <span class="panel-header-icon">👥</span>
                        <span class="panel-title">Recent conversations</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        panel_heading(
            "",
            "Latest records returned by the backend",
            "LIVE" if api_online else "API OFFLINE",
        )

        query = st.text_input(
            "Search conversations",
            placeholder="Search name, Telegram ID, mode, or message...",
            key="overview_search",
        )

        visible = conversations

        if query.strip():
            term = query.strip().lower()

            visible = [
                item
                for item in conversations
                if term in " ".join(
                    str(item.get(key, ""))
                    for key in (
                        "name",
                        "platform_user_id",
                        "handling_mode",
                        "last_message",
                    )
                ).lower()
            ]

        if not api_online:
            st.warning(
                "The conversation API is unavailable. Start FastAPI "
                "to display live conversations."
            )
            st.caption(api_problem)

        elif not visible:
            st.info(
                "No matching conversations."
                if conversations
                else "No conversations yet. Send a message to your Telegram bot."
            )

        else:
            rows = [
                {
                    "Student": item.get("name") or "Student",
                    "Telegram ID": str(
                        item.get("platform_user_id") or "—"
                    ),
                    "Last message": str(
                        item.get("last_message") or "—"
                    ).replace("\n", " ")[:65],
                    "Mode": (
                        item.get("handling_mode") or "ai"
                    ).upper(),
                    "Unread": int(
                        item.get("unread_count", 0) or 0
                    ),
                }
                for item in visible[:12]
            ]

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
                height=360,
            )

        st.button(
            "Open counselor inbox →",
            use_container_width=True,
            key="overview_to_inbox",
            on_click=navigate_to,
            args=("Counselor Inbox",),
        )

    with right:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-header-left">
                        <span class="panel-header-icon">⚡</span>
                        <span class="panel-title">Attention & readiness</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        panel_heading(
            "",
            "Signals based on current system data",
        )

        if not api_online:
            st.markdown(
                """
                <div class="insight-row">
                    <div class="insight-title">Backend disconnected</div>
                    <div class="insight-copy">
                        Start FastAPI to view conversation counts,
                        unread messages, and handling modes.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            if human_count:
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-title">
                            🟠 {human_count} conversation(s) in counselor mode
                        </div>
                        <div class="insight-copy">
                            AI replies are paused until a counselor selects Resume AI.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if unread_count:
                st.markdown(
                    f"""
                    <div class="insight-row">
                        <div class="insight-title">
                            🔔 {unread_count} unread message(s)
                        </div>
                        <div class="insight-copy">
                            Review the counselor inbox to read and respond.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if not human_count and not unread_count:
                st.markdown(
                    """
                    <div class="insight-row">
                        <div class="insight-title">✅ No pending signals</div>
                        <div class="insight-copy">
                            No unread messages or active counselor takeovers
                            are currently reported.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        knowledge_status = (
            f"RAG initialized with {document_chunks} chunks."
            if rag_service
            else "RAG initialization requires attention."
        )

        st.markdown(
            f"""
            <div class="insight-row">
                <div class="insight-title">📚 Knowledge base</div>
                <div class="insight-copy">
                    {html.escape(knowledge_status)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.button(
            "Open knowledge base →",
            use_container_width=True,
            key="overview_to_kb",
            on_click=navigate_to,
            args=("Knowledge Base",),
        )


# ============================================================
# 8. TEXT INQUIRIES
# ============================================================

elif page == "Text Inquiries":
    page_header(
        "Text Inquiries",
        "AI admissions assistant",
        "Ask institute-related questions and inspect retrieved evidence.",
    )

    language = st.selectbox(
        "Preferred answer language",
        ["Auto-detect", "English", "Hindi", "Marathi"],
        key="text_language",
    )

    language_map = {
        "Auto-detect": None,
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr",
    }

    if not rag_service:
        st.error("The RAG service is not available.")

    else:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-header-left">
                        <span class="panel-header-icon">💬</span>
                        <span class="panel-title">Student conversation</span>
                    </div>
                </div>
                <div class="section-subtitle">
                    Answers use the configured institute document index.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if (
                    message["role"] == "assistant"
                    and message.get("answer_mode") != "welcome"
                ):
                    show_sources(message)

        question = st.chat_input(
            "Ask about courses, fees, schedules, or institute policies...",
            key="student_question",
        )

        if question:
            st.session_state.messages.append(
                {"role": "user", "content": question}
            )

            try:
                with st.spinner("Searching institute documents..."):
                    result = rag_service.answer(
                        question,
                        response_language=language_map[language],
                    )

                assistant_message = {
                    "role": "assistant",
                    "content": str(result.get("answer", "")),
                    "question": question,
                    "grounded": result.get("grounded", False),
                    "sources": result.get("sources", []),
                    "answer_mode": result.get("answer_mode", "unknown"),
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
            st.rerun()


# ============================================================
# 9. VOICE INQUIRIES
# ============================================================

elif page == "Voice Inquiries":
    page_header(
        "Voice Inquiries",
        "Voice admissions assistant",
        "Transcribe a recording and generate a spoken reply.",
    )

    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-header-left">
                        <span class="panel-header-icon">🎙</span>
                        <span class="panel-title">Upload voice recording</span>
                    </div>
                </div>
                <div class="section-subtitle">
                    WAV, MP3, M4A, OGG, WEBM, MP4 · maximum 25 MB
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        audio_file = st.file_uploader(
            "Choose an audio file",
            type=["wav", "mp3", "m4a", "ogg", "webm", "mp4"],
            max_upload_size=25,
            key="voice_upload",
        )

        if audio_file:
            st.audio(audio_file)

        if not gemini_client:
            st.warning(
                "Voice processing requires GEMINI_API_KEY in .env."
            )

        disabled = (
            audio_file is None
            or gemini_client is None
            or rag_service is None
        )

        if st.button(
            "Process voice message",
            type="primary",
            disabled=disabled,
            use_container_width=True,
            key="process_voice_message",
        ):
            temporary_audio_path = None

            try:
                if audio_file.size > MAX_AUDIO_BYTES:
                    st.error("Audio file exceeds the 25 MB limit.")

                else:
                    suffix = (
                        Path(audio_file.name).suffix.lower() or ".wav"
                    )

                    with tempfile.NamedTemporaryFile(
                        suffix=suffix,
                        prefix="lead-desk-",
                        delete=False,
                    ) as temp_file:
                        temp_file.write(audio_file.getvalue())
                        temporary_audio_path = Path(temp_file.name)

                    with st.spinner(
                        "Transcribing and generating a response..."
                    ):
                        result = process_voice_message(
                            audio_path=temporary_audio_path,
                            rag_service=rag_service,
                            gemini_client=gemini_client,
                            output_dir=VOICE_OUTPUT_DIR,
                        )

                    st.session_state.last_voice_result = result
                    st.success("Voice message processed successfully.")

            except Exception as exc:
                st.error(
                    f"Voice processing failed: "
                    f"{type(exc).__name__}: {exc}"
                )

            finally:
                if (
                    temporary_audio_path
                    and temporary_audio_path.exists()
                ):
                    try:
                        temporary_audio_path.unlink()
                    except OSError:
                        pass

    with right:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-header-left">
                        <span class="panel-header-icon">📋</span>
                        <span class="panel-title">Latest result</span>
                    </div>
                </div>
                <div class="section-subtitle">
                    Transcription, answer, evidence, and audio
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        result = st.session_state.last_voice_result

        if not result:
            st.info("Process a recording to view its result.")

        else:
            st.markdown("**Transcription**")
            st.write(result.get("transcript", ""))

            st.markdown("**Detected language**")
            st.write(result.get("language", "unknown"))

            st.markdown("**Answer**")
            st.markdown(result.get("answer", ""))

            show_sources(result)

            audio_path = result.get("audio_path")

            if audio_path:
                output_audio = Path(audio_path)

                if output_audio.is_file():
                    st.markdown("**Generated voice reply**")
                    st.audio(
                        output_audio.read_bytes(),
                        format="audio/wav",
                    )

            with st.expander("Processing timings"):
                st.json(result.get("timings", {}))


# ============================================================
# 10. COUNSELOR INBOX
# ============================================================

elif page == "Counselor Inbox":
    page_header(
        "Counselor Inbox",
        "Conversations",
        "Review Telegram messages, take over from AI, reply, or resume AI.",
    )

    try:
        conversations = load_conversations()
        api_ready = True

    except RuntimeError as exc:
        conversations = []
        api_ready = False
        st.error(str(exc))

    except requests.RequestException as exc:
        conversations = []
        api_ready = False
        st.error(
            f"Conversation API unavailable ({type(exc).__name__}). "
            "Start FastAPI and refresh."
        )

    except ValueError:
        conversations = []
        api_ready = False
        st.error("Conversation API returned an invalid response.")

    notice = st.session_state.pop("inbox_notice", None)

    if notice:
        st.success(notice)

    search = st.text_input(
        "Find conversation",
        placeholder="Search student, ID, message, or mode...",
        key="inbox_search",
    )

    if search.strip():
        term = search.strip().lower()

        conversations = [
            item
            for item in conversations
            if term in " ".join(
                str(item.get(key, ""))
                for key in (
                    "name",
                    "platform_user_id",
                    "last_message",
                    "handling_mode",
                )
            ).lower()
        ]

    if not conversations:
        if api_ready:
            st.info(
                "No matching conversations."
                if search.strip()
                else (
                    "No Telegram conversations yet. Send a message "
                    "to your bot and refresh."
                )
            )
        else:
            st.info("The conversation list is unavailable.")

    else:
        by_id = {
            str(item["platform_user_id"]): item
            for item in conversations
        }

        conversation_ids = list(by_id)

        def conversation_label(user_id):
            item = by_id[user_id]
            name = item.get("name") or "Student"
            mode_value = (
                item.get("handling_mode") or "ai"
            ).upper()
            unread = int(item.get("unread_count", 0) or 0)
            last_message = str(
                item.get("last_message") or ""
            ).replace("\n", " ")[:40]

            return (
                f"{name} · {user_id} · {mode_value} · "
                f"{unread} unread · {last_message}"
            )

        previous = st.session_state.get(
            "counselor_selected_telegram_uid"
        )

        default_index = (
            conversation_ids.index(previous)
            if previous in conversation_ids
            else 0
        )

        selected_uid = st.selectbox(
            "Select conversation",
            conversation_ids,
            index=default_index,
            format_func=conversation_label,
            key="counselor_selected_telegram_uid",
        )

        selected = by_id[selected_uid]
        mode = (
            selected.get("handling_mode") or "ai"
        ).lower()

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Student",
                selected.get("name") or "Unknown",
            )

        with c2:
            st.metric("Handling mode", mode.upper())

        with c3:
            st.metric(
                "Unread messages",
                int(selected.get("unread_count", 0) or 0),
            )

        if not selected.get("chat_id"):
            st.warning(
                "No Telegram chat destination is stored for this "
                "conversation. Ask the student to message the bot again."
            )

        takeover_col, resume_col = st.columns(2)

        with takeover_col:
            if mode != "human" and st.button(
                "Take over conversation",
                type="primary",
                use_container_width=True,
                key=f"takeover_{selected_uid}",
            ):
                try:
                    response = api_post(
                        f"/api/conversations/telegram/"
                        f"{selected_uid}/takeover"
                    )

                    if response.ok:
                        st.session_state["inbox_notice"] = (
                            response.json().get(
                                "message",
                                "Human takeover enabled.",
                            )
                        )
                        st.rerun()

                    st.error("Takeover failed: " + api_error(response))

                except (
                    RuntimeError,
                    requests.RequestException,
                ) as exc:
                    st.error(
                        f"Takeover failed: {type(exc).__name__}: {exc}"
                    )

        with resume_col:
            if mode == "human" and st.button(
                "Resume AI",
                use_container_width=True,
                key=f"resume_{selected_uid}",
            ):
                try:
                    response = api_post(
                        f"/api/conversations/telegram/"
                        f"{selected_uid}/resume"
                    )

                    if response.ok:
                        st.session_state["inbox_notice"] = (
                            "AI handling resumed."
                        )
                        st.rerun()

                    st.error("Resume failed: " + api_error(response))

                except (
                    RuntimeError,
                    requests.RequestException,
                ) as exc:
                    st.error(
                        f"Resume failed: {type(exc).__name__}: {exc}"
                    )

        st.divider()

        st.markdown(
            """
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-header-left">
                        <span class="panel-header-icon">💬</span>
                        <span class="panel-title">Conversation history</span>
                    </div>
                </div>
                <div class="section-subtitle">
                    Student messages and outbound replies
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            response = api_get(
                f"/api/conversations/telegram/"
                f"{selected_uid}/messages",
                params={"limit": 300},
            )

            if response.ok:
                history = response.json()
            else:
                history = {}
                st.error(
                    "Could not load history: " + api_error(response)
                )

        except (
            RuntimeError,
            requests.RequestException,
            ValueError,
        ) as exc:
            history = {}
            st.error(
                f"History request failed: {type(exc).__name__}."
            )

        details = history.get("conversation", {})
        messages = history.get("messages", [])

        mode = (
            details.get("handling_mode") or mode
        ).lower()

        if not messages:
            st.info("No messages are available for this conversation.")

        else:
            for message in messages:
                inbound = message.get("direction") == "inbound"
                sender_type = message.get("sender_type", "")

                sender = (
                    "Student"
                    if inbound
                    else {
                        "counselor": "Human Counselor",
                        "system": "System",
                        "ai": "AI Counselor",
                    }.get(sender_type, "Outgoing message")
                )

                with st.chat_message(
                    "user" if inbound else "assistant"
                ):
                    st.caption(
                        f"{sender} · {message.get('created_at', '')}"
                    )
                    st.text(str(message.get("content", "")))

        try:
            api_post(
                f"/api/conversations/telegram/{selected_uid}/read",
                timeout=(5, 10),
            )
        except (RuntimeError, requests.RequestException):
            pass

        st.divider()

        if mode == "human":
            st.markdown(
                """
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-header-left">
                            <span class="panel-header-icon">✍️</span>
                            <span class="panel-title">Reply to student</span>
                        </div>
                    </div>
                    <div class="section-subtitle">
                        Your reply is sent to this Telegram chat
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form(
                key=f"counselor_reply_form_{selected_uid}"
            ):
                reply_text = st.text_area(
                    "Message",
                    max_chars=4000,
                    height=100,
                    key=f"counselor_reply_text_{selected_uid}",
                    placeholder="Write your reply...",
                )

                send = st.form_submit_button(
                    "Send reply to Telegram",
                    type="primary",
                    use_container_width=True,
                )

            if send:
                if not reply_text.strip():
                    st.error("Write a message before sending.")

                else:
                    try:
                        response = api_post(
                            f"/api/conversations/telegram/"
                            f"{selected_uid}/reply",
                            json_body={
                                "content": reply_text.strip(),
                                "counselor": (
                                    os.getenv(
                                        "COUNSELOR_NAME",
                                        "counselor",
                                    ).strip()
                                    or "counselor"
                                ),
                            },
                        )

                        if response.ok:
                            st.session_state["inbox_notice"] = (
                                "Reply sent to Telegram."
                            )
                            st.rerun()

                        st.error("Reply failed: " + api_error(response))

                    except (
                        RuntimeError,
                        requests.RequestException,
                    ) as exc:
                        st.error(
                            f"Reply failed: {type(exc).__name__}: {exc}"
                        )

        else:
            st.info(
                "AI is handling this conversation. Select Take over "
                "conversation before sending a counselor reply."
            )

        with st.expander("Conversation activity / audit trail"):
            try:
                response = api_get(
                    f"/api/conversations/telegram/"
                    f"{selected_uid}/events",
                    params={"limit": 100},
                    timeout=(5, 15),
                )

                if response.ok:
                    events = response.json().get("events", [])

                    if events:
                        st.dataframe(
                            [
                                {
                                    "Event": item.get("event_type", ""),
                                    "Actor": item.get("actor", ""),
                                    "Details": item.get("details", ""),
                                    "Time": item.get("created_at", ""),
                                }
                                for item in events
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.caption("No counselor actions recorded yet.")

                else:
                    st.warning("Could not load activity history.")

            except (
                RuntimeError,
                requests.RequestException,
                ValueError,
            ):
                st.warning("Activity history is unavailable.")


# ============================================================
# 12. KNOWLEDGE BASE
# ============================================================

elif page == "Knowledge Base":
    page_header(
        "Knowledge Base",
        "Institute knowledge base",
        "Upload official documents and manage the retrieval index.",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Local documents", len(local_documents))

    with c2:
        st.metric(
            "Indexed chunks",
            document_chunks if rag_service else "—",
        )

    with c3:
        st.metric(
            "RAG status",
            "Ready" if rag_service else "Needs attention",
        )

    st.write("")

    st.markdown(
        """
        <div class="panel">
            <div class="panel-header">
                <div class="panel-header-left">
                    <span class="panel-header-icon">📤</span>
                    <span class="panel-title">Upload institute document</span>
                </div>
            </div>
            <div class="section-subtitle">
                PDF or DOCX · maximum 15 MB
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Backend URL: {COUNSELOR_API_URL}")

    kb_notice = st.session_state.pop("kb_notice", None)

    if kb_notice:
        st.success(kb_notice)

    uploaded_document = st.file_uploader(
        "Choose a PDF or Word document",
        type=["pdf", "docx"],
        key="kb_document_uploader",
    )

    upload_col, reindex_col = st.columns(2)

    with upload_col:
        upload_clicked = st.button(
            "Upload and index",
            type="primary",
            disabled=uploaded_document is None,
            use_container_width=True,
            key="kb_upload_button",
        )

    with reindex_col:
        reindex_clicked = st.button(
            "Re-index all documents",
            use_container_width=True,
            key="kb_reindex_button",
        )

    if upload_clicked and uploaded_document is not None:
        if uploaded_document.size > MAX_DOCUMENT_BYTES:
            st.error("The document exceeds the 15 MB limit.")

        else:
            try:
                response = api_post(
                    "/api/documents/upload",
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
                    st.error("Upload failed: " + api_error(response))

                else:
                    result = response.json()
                    filename = result.get(
                        "filename",
                        uploaded_document.name,
                    )
                    status = result.get("index_status", "unknown")

                    if status == "indexed":
                        st.success(
                            f"{filename} was uploaded and indexed."
                        )
                    else:
                        st.warning(
                            f"{filename} was stored, but the index status "
                            f"is {status}. Check backend logs and retry indexing."
                        )

                    try:
                        if (
                            rag_service
                            and rag_service.refresh_index_if_changed()
                        ):
                            st.info("The local RAG index was refreshed.")
                    except Exception as exc:
                        st.warning(
                            "Upload succeeded, but the local index could "
                            f"not refresh ({type(exc).__name__})."
                        )

            except RuntimeError as exc:
                st.error(str(exc))

            except requests.RequestException as exc:
                st.error(
                    f"Could not reach document API "
                    f"({type(exc).__name__})."
                )

            except ValueError:
                st.error("Document API returned an invalid response.")

    if reindex_clicked:
        try:
            response = api_post(
                "/api/documents/reindex",
                timeout=(10, 900),
            )

            if not response.ok:
                st.error("Re-index failed: " + api_error(response))

            else:
                result = response.json()
                parts = ["Backend re-index completed."]

                if result.get("documents") is not None:
                    parts.append(
                        f"Documents: {result['documents']}."
                    )

                if result.get("chunks") is not None:
                    parts.append(f"Chunks: {result['chunks']}.")

                st.session_state["kb_notice"] = " ".join(parts)
                get_rag_service.clear()
                st.rerun()

        except RuntimeError as exc:
            st.error(str(exc))

        except requests.RequestException as exc:
            st.error(
                f"Re-index request failed: {type(exc).__name__}."
            )

        except ValueError:
            st.error("Re-index endpoint returned an invalid response.")

    st.divider()

    st.markdown(
        """
        <div class="panel">
            <div class="panel-header">
                <div class="panel-header-left">
                    <span class="panel-header-icon">📁</span>
                    <span class="panel-title">Stored documents</span>
                </div>
            </div>
            <div class="section-subtitle">
                Document records returned by the backend
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        documents = load_documents()
        st.caption(f"{len(documents)} document(s) registered.")

        if documents:
            rows = []

            for document in documents:
                filename = document.get("filename", "Unknown")

                size = document.get(
                    "size_bytes",
                    document.get("size", 0),
                ) or 0

                try:
                    size_mb = round(float(size) / (1024 * 1024), 2)
                except (TypeError, ValueError):
                    size_mb = 0.0

                rows.append(
                    {
                        "Document": filename,
                        "Type": document.get(
                            "extension",
                            Path(filename).suffix.lower(),
                        ),
                        "Size (MB)": size_mb,
                        "Index status": document.get(
                            "index_status",
                            document.get("status", "unknown"),
                        ),
                        "Stored path": document.get(
                            "relative_path",
                            "",
                        ),
                    }
                )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info("No documents are currently listed by the backend.")

    except RuntimeError as exc:
        st.warning(str(exc))

    except requests.RequestException as exc:
        st.warning(
            f"Document list unavailable ({type(exc).__name__})."
        )

    except ValueError:
        st.warning("Document API returned an invalid response.")


# ============================================================
# 13. FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer-note">
        AI Lead Desk · Admissions workspace ·
        Keep API keys in .env and never commit secrets.
    </div>
    """,
    unsafe_allow_html=True,
)