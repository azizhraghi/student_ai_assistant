"""
Student AI Assistant — Main Streamlit App
Multi-agent system powered by LangGraph + Mistral
"""

import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Student AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    /* Main App Background */
    .stApp { background-color: #f8fafc; }

    /* Sidebar Content */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* User Messages */
    .user-message {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        padding: 14px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        margin-left: 15%;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    }

    /* Assistant Messages */
    .assistant-message {
        background-color: #ffffff;
        color: #1e293b;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        margin-right: 15%;
        font-size: 0.95rem;
        line-height: 1.6;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* Intent Badge */
    .intent-badge {
        display: inline-block;
        background-color: #f1f5f9;
        color: #6366f1;
        font-size: 0.7rem;
        padding: 2px 10px;
        border-radius: 20px;
        margin-bottom: 8px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid #e2e8f0;
    }

    /* Header Styling */
    .main-header { text-align: center; padding: 25px 0 15px 0; }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header p { color: #64748b; font-size: 1rem; }

    /* Agent Overview Cards */
    .agent-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #6366f1;
        font-size: 0.85rem;
        color: #334155;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Hide Streamlit components */
    #MainMenu, footer, header { visibility: hidden; }

    /* Forms and Inputs */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #6366f1 !important;
        border-bottom-color: #6366f1 !important;
    }

    /* Quick Action Buttons - Ensure they stand out in light mode */
    .stButton > button {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        color: #1e293b !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        border-color: #6366f1 !important;
        color: #6366f1 !important;
        background-color: #f5f3ff !important;
    }

    /* Sidebar Text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = bool(os.getenv("MISTRAL_API_KEY"))
if "course_content" not in st.session_state:
    st.session_state.course_content = ""

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 Student AI Assistant")
    st.markdown("---")

    # API Key
    if not st.session_state.api_key_set:
        st.markdown("### 🔑 Mistral API Key")
        api_key = st.text_input("API Key", type="password", placeholder="Enter your Mistral API key...")
        if api_key:
            os.environ["MISTRAL_API_KEY"] = api_key
            st.session_state.api_key_set = True
            st.success("✅ API Key set!")
            st.rerun()
    else:
        st.success("✅ Mistral API Key loaded")

    st.markdown("---")

    # File Upload Section
    st.markdown("### 📁 Upload Course Material")

    upload_tab, url_tab, text_tab = st.tabs(["📄 File", "🌐 URL", "📝 Text"])

    with upload_tab:
        uploaded_file = st.file_uploader(
            "Upload PDF or PPTX",
            type=["pdf", "pptx"],
            label_visibility="collapsed"
        )
        if uploaded_file:
            file_bytes = uploaded_file.read()
            ext = uploaded_file.name.split(".")[-1].lower()
            st.session_state.pending_file = {
                "bytes": file_bytes,
                "type": ext,
                "name": uploaded_file.name
            }
            st.success(f"✅ {uploaded_file.name} ready!")

    with url_tab:
        url_input = st.text_input("Enter URL", placeholder="https://...")
        if st.button("Load URL", use_container_width=True) and url_input:
            st.session_state.pending_url = url_input
            st.success("✅ URL ready!")

    with text_tab:
        text_input = st.text_area("Paste course content", height=120, placeholder="Paste your notes or text here...")
        if st.button("Use Text", use_container_width=True) and text_input:
            st.session_state.pending_text = text_input
            st.success("✅ Text ready!")

    # Show what's loaded
    pending_source = (
        st.session_state.get("pending_file") or
        st.session_state.get("pending_url") or
        st.session_state.get("pending_text")
    )
    if pending_source:
        st.info("📌 Source loaded — ask the Course Agent to process it!")
        if st.button("🗑️ Clear Source", use_container_width=True):
            for key in ["pending_file", "pending_url", "pending_text"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown("---")

    # Agents Overview
    st.markdown("### 🤖 Agents")

    agents = [
        ("🧠", "Orchestrator", "Routes queries", True),
        ("📚", "Course Agent", "PDF, PPTX, URL, Text", True),
        ("📅", "Deadline Agent", "SQLite task tracker", True),
        ("✏️", "Revision Agent", "Quizzes & Flashcards", True),
        ("🔍", "Research Agent", "Web search & resources", True),
    ]

    for icon, name, desc, active in agents:
        st.markdown(f"""
        <div class="agent-card">
            🟢 <strong>{icon} {name}</strong><br>
            <span style="color:#64748b; font-size:0.8rem">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style='color:#475569; font-size:0.75rem; text-align:center; margin-top:8px'>
        ATLAS TBS Hackathon 2026<br>LangGraph + Mistral
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🎓 Student AI Assistant</h1>
    <p>Your personal multi-agent AI companion for smarter studying</p>
</div>
""", unsafe_allow_html=True)

# Quick Actions
st.markdown("#### ⚡ Quick Actions")
col1, col2, col3, col4 = st.columns(4)

quick_actions = {
    col1: ("📚 Summarize material", "Please summarize the uploaded course material"),
    col2: ("📅 Show my deadlines", "Show me all my upcoming deadlines"),
    col3: ("✏️ Quiz me!", "Create a quiz to help me revise"),
    col4: ("🔍 Find resources", "Find me resources to learn about machine learning"),
}

for col, (label, prompt) in quick_actions.items():
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────
# Chat Display
# ─────────────────────────────────────────────

if not st.session_state.messages:
    st.markdown("""
    <div style='text-align:center; padding: 50px 20px; color:#475569'>
        <div style='font-size:3rem'>🎓</div>
        <div style='font-size:1.1rem; margin-top:10px'>Hi! I'm your Student AI Assistant.</div>
        <div style='font-size:0.9rem; margin-top:5px'>
            Upload a document, add a deadline, ask for a quiz, or search for resources.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    AGENT_ICONS = {
        "course_agent": "📚",
        "deadline_agent": "📅",
        "revision_agent": "✏️",
        "research_agent": "🔍",
        "general": "🧠",
    }
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            intent = msg.get("intent", "general")
            icon = AGENT_ICONS.get(intent, "🤖")
            badge = f'<div class="intent-badge">{icon} {intent.replace("_", " ")}</div>' if intent else ""
            # Use st.markdown for assistant messages (supports rich markdown like tables, code)
            st.markdown(f'<div class="assistant-message">{badge}', unsafe_allow_html=True)
            st.markdown(msg["content"])
            st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Chat Input
# ─────────────────────────────────────────────

st.markdown("---")

with st.form("chat_form", clear_on_submit=True):
    cols = st.columns([8, 1])
    with cols[0]:
        user_input = st.text_input(
            "Message",
            placeholder="Ask about your courses, deadlines, revision, or research...",
            label_visibility="collapsed"
        )
    with cols[1]:
        submit = st.form_submit_button("Send 🚀", use_container_width=True)

# ─────────────────────────────────────────────
# Handle Submission
# ─────────────────────────────────────────────

if submit and user_input and user_input.strip():
    if not st.session_state.api_key_set:
        st.error("⚠️ Please set your Mistral API Key in the sidebar first!")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        # Build extra context from pending uploads
        extra = None
        if st.session_state.get("pending_file"):
            f = st.session_state.pending_file
            extra = {
                "force_intent": "course_agent",
                "source_type": f["type"],
                "file_bytes": f["bytes"],
            }
        elif st.session_state.get("pending_url"):
            extra = {
                "force_intent": "course_agent",
                "source_type": "url",
                "url": st.session_state.pending_url,
            }
        elif st.session_state.get("pending_text"):
            extra = {
                "force_intent": "course_agent",
                "source_type": "text",
                "source_content": st.session_state.pending_text,
            }

        with st.spinner("🤖 Thinking..."):
            try:
                from orchestrator import run_orchestrator
                result = run_orchestrator(history, extra=extra)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "intent": result["intent"],
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ **Error:** {str(e)}\n\nMake sure your Mistral API key is valid.",
                    "intent": "error",
                })

        st.rerun()
