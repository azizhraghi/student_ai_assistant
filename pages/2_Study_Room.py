"""
Collaborative Study Room — multi-student AI-powered study sessions.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import time
from dotenv import load_dotenv

load_dotenv()

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    #MainMenu, footer, header { visibility: hidden; }

    .page-header { text-align: center; padding: 20px 0 8px; }
    .page-header h1 {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .page-header p { color: #64748b; font-size: 0.9rem; }

    .room-code-display {
        background: linear-gradient(135deg, #f1f5f9, #ede9fe);
        border: 2px solid #6366f1;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    .room-code {
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: 0.3em;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .room-label { color: #64748b; font-size: 0.8rem; margin-top: 4px; }

    .member-chip {
        display: inline-block;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 0.82rem;
        color: #334155;
    }
    .member-chip.you {
        border-color: #6366f1;
        color: #4f46e5;
        background: #ede9fe;
    }

    .upload-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 6px 0;
        font-size: 0.85rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .upload-card .uploader { color: #6366f1; font-weight: 600; }
    .upload-card .filename { color: #64748b; }

    .chat-msg-user {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        padding: 10px 14px;
        border-radius: 16px 16px 4px 16px;
        margin: 6px 0;
        margin-left: 20%;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(99,102,241,0.15);
    }
    .chat-msg-ai {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #1e293b;
        padding: 10px 14px;
        border-radius: 16px 16px 16px 4px;
        margin: 6px 0;
        margin-right: 20%;
        font-size: 0.9rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .chat-msg-system {
        text-align: center;
        color: #64748b;
        font-size: 0.78rem;
        padding: 4px 0;
    }
    .msg-meta { font-size: 0.72rem; color: #94a3b8; margin-bottom: 3px; }

    .stat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stat-number { font-size: 1.8rem; font-weight: 800; color: #6366f1; }
    .stat-label { font-size: 0.75rem; color: #64748b; }

    .quiz-question {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .quiz-answer-correct { color: #059669; font-weight: 600; }
    .quiz-answer-wrong { color: #dc2626; }

    .tab-content { padding: 16px 0; }

    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #1e293b !important; }

    .stButton > button {
        border-radius: 8px !important; border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important; color: #1e293b !important;
    }
    .stButton > button:hover {
        border-color: #6366f1 !important; color: #6366f1 !important;
        background-color: #f5f3ff !important;
    }

    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #64748b; }
    .stTabs [aria-selected="true"] { color: #6366f1 !important; border-bottom-color: #6366f1 !important; }

    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important; color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "collab_room_code": None,
        "collab_username": None,
        "collab_in_room": False,
        "quiz_answers": {},
        "quiz_submitted": False,
        "quiz_data": None,
        "last_refresh": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ── Sidebar ───────────────────────────────────────────────────────────────────

from ui import render_sidebar
render_sidebar("👥 Collaborative Study Room")

with st.sidebar:
    if st.session_state.collab_in_room:
        # Room info in sidebar
        st.markdown("### 🏠 Your Room")
        st.markdown(f"""
        <div style='background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;padding:12px;text-align:center'>
            <div style='font-size:1.6rem;font-weight:900;letter-spacing:0.2em;color:#6366f1'>
                {st.session_state.collab_room_code}
            </div>
            <div style='color:#64748b;font-size:0.75rem'>Room Code — share with friends!</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"👤 **You:** {st.session_state.collab_username}")

        st.markdown("---")
        st.markdown("### 👥 Members")
        from tools.collab_db import get_members
        members = get_members(st.session_state.collab_room_code)
        for m in members:
            is_you = m["username"] == st.session_state.collab_username
            cls = "member-chip you" if is_you else "member-chip"
            label = f"⭐ {m['username']} (you)" if is_you else f"👤 {m['username']}"
            st.markdown(f'<span class="{cls}">{label}</span>', unsafe_allow_html=True)

        st.markdown("---")

        # Upload in sidebar
        st.markdown("### 📁 Upload Material")
        with st.expander("Add your content", expanded=False):
            upload_tab, text_tab = st.tabs(["📄 File", "📝 Text"])
            with upload_tab:
                up_file = st.file_uploader("PDF or PPTX", type=["pdf","pptx"], key="collab_file")
                if up_file and st.button("📤 Share with Room", key="share_file"):
                    fb = up_file.read()
                    ext = up_file.name.split(".")[-1].lower()
                    with st.spinner("Extracting..."):
                        if ext == "pdf":
                            from tools.pdf_parser import parse_pdf
                            content = parse_pdf(fb)
                        else:
                            from tools.pptx_parser import parse_pptx
                            content = parse_pptx(fb)
                    from tools.collab_db import add_upload
                    add_upload(st.session_state.collab_room_code, st.session_state.collab_username, up_file.name, content)
                    st.success(f"✅ {up_file.name} shared!")
                    st.rerun()
            with text_tab:
                paste_text = st.text_area("Paste notes", height=100, key="collab_text_input")
                paste_name = st.text_input("Title", placeholder="e.g. Chapter 3 Notes", key="collab_text_name")
                if st.button("📤 Share Text", key="share_text") and paste_text:
                    from tools.collab_db import add_upload
                    add_upload(st.session_state.collab_room_code, st.session_state.collab_username,
                               paste_name or "Pasted Notes", paste_text)
                    st.success("✅ Text shared!")
                    st.rerun()

        st.markdown("---")

        if st.button("🚪 Leave Room", use_container_width=True):
            st.session_state.collab_in_room = False
            st.session_state.collab_room_code = None
            st.session_state.collab_username = None
            st.session_state.quiz_data = None
            st.session_state.quiz_submitted = False
            st.rerun()

    st.markdown("""
    <div style='color:#475569;font-size:0.72rem;text-align:center;margin-top:12px'>
        ATLAS TBS Hackathon 2026<br>LangGraph + Mistral
    </div>
    """, unsafe_allow_html=True)


# ── Main Content ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="page-header">
    <div style="color:#64748b; font-weight:600; font-size:1.1rem; margin-bottom: -8px; letter-spacing: 0.05em; text-transform: uppercase;">🎓 Student AI Assistant</div>
    <h1>👥 Collaborative Study Room</h1>
    <p>Study together, share materials, and let AI build a unified knowledge base for your group</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# LOBBY — not in a room yet
# ═══════════════════════════════════════════════════════

if not st.session_state.collab_in_room:
    st.markdown("---")
    col_create, col_join = st.columns(2)

    with col_create:
        st.markdown("### 🆕 Create a Room")
        st.markdown("Start a new study session and invite your teammates.")
        room_name = st.text_input("Session name", placeholder="e.g. Data Structures Exam Prep", key="create_name")
        username_create = st.text_input("Your name", placeholder="e.g. Yassine", key="create_username")
        if st.button("🚀 Create Room", use_container_width=True, type="primary"):
            if room_name and username_create:
                from tools.collab_db import create_room, join_room
                room = create_room(room_name)
                join_room(room["code"], username_create)
                st.session_state.collab_room_code = room["code"]
                st.session_state.collab_username = username_create
                st.session_state.collab_in_room = True
                st.rerun()
            else:
                st.warning("Please fill in all fields.")

    with col_join:
        st.markdown("### 🔗 Join a Room")
        st.markdown("Enter the room code shared by your teammate.")
        room_code_input = st.text_input("Room code", placeholder="e.g. AB12CD", key="join_code").upper()
        username_join = st.text_input("Your name", placeholder="e.g. Sana", key="join_username")
        if st.button("🚪 Join Room", use_container_width=True):
            if room_code_input and username_join:
                from tools.collab_db import get_room, join_room
                room = get_room(room_code_input)
                if room:
                    join_room(room_code_input, username_join)
                    st.session_state.collab_room_code = room_code_input
                    st.session_state.collab_username = username_join
                    st.session_state.collab_in_room = True
                    st.rerun()
                else:
                    st.error("❌ Room not found. Check the code and try again.")
            else:
                st.warning("Please fill in all fields.")

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center;padding:40px 20px;color:#475569'>
        <div style='font-size:3rem'>👥</div>
        <div style='font-size:1.1rem;color:#94a3b8;margin-top:10px'>Create or join a room to start collaborating</div>
        <div style='font-size:0.85rem;margin-top:6px'>
            Share your room code with teammates — everyone's materials get merged into one AI-powered knowledge base
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════
# INSIDE THE ROOM
# ═══════════════════════════════════════════════════════

from tools.collab_db import (
    get_room, get_members, get_uploads, get_merged_content,
    get_messages, add_message, get_room_graph, save_room_graph
)

room = get_room(st.session_state.collab_room_code)
members = get_members(st.session_state.collab_room_code)
uploads = get_uploads(st.session_state.collab_room_code)

# ── Room Header ───────────────────────────────────────────────────────────────

col_title, col_code = st.columns([3,1])
with col_title:
    st.markdown(f"## 🏠 {room['name']}")
    member_html = " ".join(
        f'<span class="member-chip {"you" if m["username"]==st.session_state.collab_username else ""}">'
        f'{"⭐ " if m["username"]==st.session_state.collab_username else "👤 "}{m["username"]}</span>'
        for m in members
    )
    st.markdown(member_html, unsafe_allow_html=True)
with col_code:
    st.markdown(f"""
    <div class="room-code-display">
        <div class="room-code">{st.session_state.collab_room_code}</div>
        <div class="room-label">Share this code</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Stats ─────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(members)}</div><div class="stat-label">Members</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(uploads)}</div><div class="stat-label">Materials Shared</div></div>', unsafe_allow_html=True)
with c3:
    total_chars = sum(len(u["content"]) for u in uploads)
    st.markdown(f'<div class="stat-card"><div class="stat-number">{total_chars//1000}K</div><div class="stat-label">Chars of Content</div></div>', unsafe_allow_html=True)
with c4:
    messages = get_messages(st.session_state.collab_room_code)
    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(messages)}</div><div class="stat-label">Messages</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_chat, tab_materials, tab_quiz, tab_graph = st.tabs(
    ["💬 Group Chat", "📚 Materials", "✏️ Group Quiz", "🕸️ Shared Graph"]
)


# ══════════════════════════════════════
# TAB 1 — GROUP CHAT
# ══════════════════════════════════════
with tab_chat:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    messages = get_messages(st.session_state.collab_room_code, limit=60)

    chat_container = st.container()
    with chat_container:
        if not messages:
            st.markdown("""
            <div style='text-align:center;padding:40px;color:#475569'>
                <div style='font-size:2rem'>💬</div>
                <div style='margin-top:8px'>No messages yet. Start the conversation!</div>
            </div>""", unsafe_allow_html=True)
        for msg in messages:
            is_me = msg["username"] == st.session_state.collab_username
            is_ai = msg["role"] == "assistant"
            is_system = msg["username"] == "system"

            if is_system:
                st.markdown(f'<div class="chat-msg-system">— {msg["content"]} —</div>', unsafe_allow_html=True)
            elif is_ai:
                st.markdown(f'<div class="chat-msg-ai"><div class="msg-meta">🤖 AI Assistant · {msg["created_at"][11:16]}</div>', unsafe_allow_html=True)
                st.markdown(msg["content"])
                st.markdown('</div>', unsafe_allow_html=True)
            elif is_me:
                st.markdown(f'<div class="chat-msg-user"><div class="msg-meta" style="color:#93c5fd">You · {msg["created_at"][11:16]}</div>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-msg-ai"><div class="msg-meta">👤 {msg["username"]} · {msg["created_at"][11:16]}</div>{msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Chat input
    with st.form("collab_chat_form", clear_on_submit=True):
        cols = st.columns([7, 1, 1])
        with cols[0]:
            chat_input = st.text_input("Message", placeholder="Ask the group AI or chat with your teammates...", label_visibility="collapsed")
        with cols[1]:
            send_btn = st.form_submit_button("Send 💬", use_container_width=True)
        with cols[2]:
            ask_ai_btn = st.form_submit_button("Ask AI 🤖", use_container_width=True)

    if (send_btn or ask_ai_btn) and chat_input.strip():
        add_message(st.session_state.collab_room_code, st.session_state.collab_username, "user", chat_input.strip())

        if ask_ai_btn and os.getenv("MISTRAL_API_KEY"):
            merged = get_merged_content(st.session_state.collab_room_code)
            with st.spinner("🤖 AI thinking..."):
                from agents.collab_agent import answer_room_question
                ai_response = answer_room_question(
                    chat_input.strip(), merged, st.session_state.collab_username
                )
            add_message(st.session_state.collab_room_code, "AI Assistant", "assistant", ai_response, "collab")

        st.rerun()

    # Auto-refresh
    if st.button("🔄 Refresh", use_container_width=False):
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════
# TAB 2 — MATERIALS
# ══════════════════════════════════════
with tab_materials:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    if not uploads:
        st.markdown("""
        <div style='text-align:center;padding:40px;color:#475569'>
            <div style='font-size:2rem'>📚</div>
            <div style='margin-top:8px'>No materials shared yet.<br>Use the sidebar to upload your content!</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"### 📚 {len(uploads)} Material(s) Shared")

        # Group by member
        by_member = {}
        for u in uploads:
            by_member.setdefault(u["username"], []).append(u)

        for member, files in by_member.items():
            is_you = member == st.session_state.collab_username
            label = f"⭐ {member} (you)" if is_you else f"👤 {member}"
            with st.expander(f"{label} — {len(files)} file(s)"):
                for f in files:
                    st.markdown(f"""
                    <div class="upload-card">
                        <span class="uploader">📄 {f['filename']}</span>
                        <span class="filename"> · {len(f['content']):,} chars · {f['uploaded_at'][5:16]}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"Preview: {f['filename']}", expanded=False):
                        st.text(f['content'][:800] + ("..." if len(f['content']) > 800 else ""))

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════
# TAB 3 — GROUP QUIZ
# ══════════════════════════════════════
with tab_quiz:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    merged = get_merged_content(st.session_state.collab_room_code)

    if not merged:
        st.info("📚 No materials uploaded yet. Share content first to generate a group quiz!")
    else:
        if st.button("🎯 Generate Group Quiz", type="primary", use_container_width=False):
            with st.spinner("🤖 Building quiz from all materials..."):
                from agents.collab_agent import generate_group_quiz
                member_names = [m["username"] for m in members]
                quiz = generate_group_quiz(merged, member_names)
                st.session_state.quiz_data = quiz
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False

        if st.session_state.quiz_data:
            quiz = st.session_state.quiz_data
            st.markdown(f"### 📝 {quiz.get('title', 'Group Quiz')}")
            st.markdown(f"*{len(quiz.get('questions', []))} questions covering all uploaded materials*")
            st.markdown("---")

            for q in quiz.get("questions", []):
                qid = q["id"]
                st.markdown(f'<div class="quiz-question">', unsafe_allow_html=True)
                st.markdown(f"**Q{qid}.** {q['question']}")

                if q.get("source"):
                    st.markdown(f"*📖 From: {q['source']}*")

                if not st.session_state.quiz_submitted:
                    selected = st.radio(
                        f"q{qid}",
                        options=q.get("options", []),
                        key=f"quiz_q_{qid}",
                        label_visibility="collapsed"
                    )
                    st.session_state.quiz_answers[qid] = selected[0] if selected else None
                else:
                    user_ans = st.session_state.quiz_answers.get(qid, "")
                    correct = q.get("answer", "")
                    for opt in q.get("options", []):
                        is_correct = opt.startswith(correct)
                        is_chosen = user_ans and opt.startswith(user_ans)
                        if is_correct:
                            st.markdown(f'<span class="quiz-answer-correct">✅ {opt}</span>', unsafe_allow_html=True)
                        elif is_chosen:
                            st.markdown(f'<span class="quiz-answer-wrong">❌ {opt}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f"- {opt}")
                    if q.get("explanation"):
                        st.markdown(f"💡 *{q['explanation']}*")

                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            if not st.session_state.quiz_submitted:
                if st.button("✅ Submit Quiz", type="primary"):
                    st.session_state.quiz_submitted = True
                    # Calculate score
                    correct_count = sum(
                        1 for q in quiz.get("questions", [])
                        if st.session_state.quiz_answers.get(q["id"]) == q.get("answer")
                    )
                    total = len(quiz.get("questions", []))
                    add_message(
                        st.session_state.collab_room_code,
                        st.session_state.collab_username,
                        "user",
                        f"📝 Completed the group quiz: {correct_count}/{total} correct!"
                    )
                    st.rerun()
            else:
                correct_count = sum(
                    1 for q in quiz.get("questions", [])
                    if st.session_state.quiz_answers.get(q["id"]) == q.get("answer")
                )
                total = len(quiz.get("questions", []))
                pct = int(correct_count / total * 100) if total else 0
                emoji = "🏆" if pct >= 80 else "📈" if pct >= 60 else "💪"
                st.success(f"{emoji} Score: **{correct_count}/{total}** ({pct}%)")
                if st.button("🔄 Retake Quiz"):
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════
# TAB 4 — SHARED KNOWLEDGE GRAPH
# ══════════════════════════════════════
with tab_graph:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    merged = get_merged_content(st.session_state.collab_room_code)

    if not merged:
        st.info("📚 Share course materials first to generate the group knowledge graph!")
    else:
        col_btn, col_info = st.columns([2, 4])
        with col_btn:
            build_graph_btn = st.button("🕸️ Build Shared Graph", type="primary", use_container_width=True)
        with col_info:
            cached = get_room_graph(st.session_state.collab_room_code)
            if cached:
                built_at = get_room(st.session_state.collab_room_code).get("graph_built_at", "")
                st.info(f"✅ Graph cached — built at {built_at[11:16] if built_at else 'unknown'}. Rebuild if new materials were added.")

        if build_graph_btn:
            with st.spinner("🧠 Building shared knowledge graph from all materials..."):
                from agents.graph_agent import run_graph_agent
                import json
                result = run_graph_agent(merged, user_hint="This content comes from multiple students — show how their topics interconnect")
                save_room_graph(st.session_state.collab_room_code, json.dumps(result))
                st.session_state["collab_graph_result"] = result
                st.rerun()

        # Load from cache or session
        graph_result = st.session_state.get("collab_graph_result") or get_room_graph(st.session_state.collab_room_code)
        if isinstance(graph_result, str):
            import json
            graph_result = json.loads(graph_result)

        if graph_result and graph_result.get("graph_data", {}).get("nodes"):
            stats = graph_result["stats"]
            st.markdown(f"### 🕸️ {graph_result['title']}")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["node_count"]}</div><div class="stat-label">Concepts</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["edge_count"]}</div><div class="stat-label">Relationships</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{len(members)}</div><div class="stat-label">Contributors</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06)">', unsafe_allow_html=True)
            components.html(graph_result["html"], height=600, scrolling=False)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style='color:#64748b;font-size:0.78rem;text-align:center;margin-top:6px'>
                🖱️ Drag · 🔍 Zoom · 👆 Hover for details
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
