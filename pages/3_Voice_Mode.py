"""
Voice Mode — talk to your AI study assistant using your microphone.
Speech-to-Text via Web Speech API (browser), Text-to-Speech via gTTS.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

load_dotenv()

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    #MainMenu, footer, header { visibility: hidden; }

    .page-header { text-align: center; padding: 24px 0 8px; }
    .page-header h1 {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .page-header p { color: #64748b; font-size: 0.9rem; }

    .transcript-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 20px;
        min-height: 60px;
        font-size: 1rem;
        color: #1e293b;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .transcript-placeholder { color: #94a3b8; font-style: italic; }

    .chat-bubble-user {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 4px 20px;
        margin: 8px 0;
        margin-left: 20%;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(99,102,241,0.15);
    }
    .chat-bubble-ai {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #1e293b;
        padding: 12px 18px;
        border-radius: 20px 20px 20px 4px;
        margin: 8px 0;
        margin-right: 20%;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .agent-badge {
        display: inline-block;
        background: #f1f5f9;
        color: #6366f1;
        font-size: 0.68rem;
        padding: 2px 8px;
        border-radius: 20px;
        margin-bottom: 5px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid #e2e8f0;
    }

    .lang-chip {
        display: inline-block;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 4px 14px;
        margin: 3px;
        font-size: 0.82rem;
        color: #64748b;
        cursor: pointer;
    }
    .lang-chip.active {
        border-color: #6366f1;
        color: #4f46e5;
        background: #ede9fe;
    }

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

    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important; color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "voice_messages": [],
        "voice_transcript": "",
        "voice_language": "en-US",
        "tts_language": "en",
        "tts_enabled": True,
        "voice_pending_input": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Language Config ────────────────────────────────────────────────────────────
LANGUAGES = {
    "🇬🇧 English":  ("en-US", "en"),
    "🇫🇷 French":   ("fr-FR", "fr"),
    "🇸🇦 Arabic":   ("ar-SA", "ar"),
    "🇩🇪 German":   ("de-DE", "de"),
    "🇪🇸 Spanish":  ("es-ES", "es"),
}

AGENT_ICONS = {
    "course_agent":   "📚",
    "deadline_agent": "📅",
    "revision_agent": "✏️",
    "research_agent": "🔍",
    "general":        "🧠",
}


# ── Sidebar ───────────────────────────────────────────────────────────────────
from ui import render_sidebar
render_sidebar("🎤 Voice Mode")

with st.sidebar:
    st.markdown("### 🌐 Language")

    for label, (stt_code, tts_code) in LANGUAGES.items():
        is_active = st.session_state.voice_language == stt_code
        if st.button(
            label,
            key=f"lang_{stt_code}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.voice_language = stt_code
            st.session_state.tts_language = tts_code
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    st.session_state.tts_enabled = st.toggle(
        "🔊 Read responses aloud",
        value=st.session_state.tts_enabled
    )

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.voice_messages = []
        st.session_state.voice_transcript = ""
        st.rerun()

    st.markdown("""
    <div style='color:#475569;font-size:0.72rem;text-align:center;margin-top:12px'>
        ATLAS TBS Hackathon 2026<br>LangGraph + Mistral
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div style="color:#64748b; font-weight:600; font-size:1.1rem; margin-bottom: -8px; letter-spacing: 0.05em; text-transform: uppercase;">🎓 Student AI Assistant</div>
    <h1>🎤 Voice Mode</h1>
    <p>Speak to your AI tutor — ask questions, get quizzes, manage deadlines, all hands-free</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")


# ── Speech-to-Text Component ───────────────────────────────────────────────────
# Uses the browser's Web Speech API via a custom HTML component

lang_code = st.session_state.voice_language

stt_component = f"""
<div id="voice-ui" style="font-family: 'Inter', sans-serif;">

    <!-- Waveform animation -->
    <style>
        @keyframes pulse {{
            0%, 100% {{ transform: scaleY(0.4); opacity: 0.5; }}
            50% {{ transform: scaleY(1); opacity: 1; }}
        }}
        .wave-bar {{
            display: inline-block;
            width: 5px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            border-radius: 3px;
            margin: 0 2px;
            height: 40px;
            animation: pulse 1s ease-in-out infinite;
        }}
        .wave-bar:nth-child(2) {{ animation-delay: 0.1s; }}
        .wave-bar:nth-child(3) {{ animation-delay: 0.2s; }}
        .wave-bar:nth-child(4) {{ animation-delay: 0.3s; }}
        .wave-bar:nth-child(5) {{ animation-delay: 0.4s; }}
        .wave-bar:nth-child(6) {{ animation-delay: 0.3s; }}
        .wave-bar:nth-child(7) {{ animation-delay: 0.2s; }}
        .wave-bar:nth-child(8) {{ animation-delay: 0.1s; }}
        #waveform {{ display: none; margin: 16px auto; text-align: center; }}
        #waveform.active {{ display: block; }}

        #mic-btn {{
            width: 90px; height: 90px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            color: white;
            font-size: 2rem;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 20px rgba(99,102,241,0.3);
            display: block;
            margin: 0 auto;
        }}
        #mic-btn:hover {{ transform: scale(1.06); box-shadow: 0 6px 28px rgba(99,102,241,0.4); }}
        #mic-btn.listening {{
            background: linear-gradient(135deg, #ef4444, #f97316);
            box-shadow: 0 4px 24px rgba(239,68,68,0.5);
            animation: micPulse 1s ease-in-out infinite;
        }}
        @keyframes micPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.08); }}
        }}
        #status-text {{
            text-align: center;
            color: #64748b;
            font-size: 0.88rem;
            margin-top: 12px;
            min-height: 20px;
        }}
        #status-text.listening {{ color: #6366f1; font-weight: 600; }}
        #transcript-display {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 14px 18px;
            min-height: 54px;
            margin-top: 16px;
            color: #1e293b;
            font-size: 1rem;
            line-height: 1.6;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        #transcript-display.empty {{ color: #94a3b8; font-style: italic; }}
        #send-btn {{
            display: none;
            margin: 12px auto 0;
            padding: 10px 28px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            color: white;
            border: none;
            border-radius: 24px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        #send-btn:hover {{ transform: scale(1.04); }}
        #error-msg {{
            color: #dc2626;
            font-size: 0.82rem;
            text-align: center;
            margin-top: 8px;
            display: none;
        }}
    </style>

    <!-- Mic Button -->
    <div style="text-align:center; padding: 24px 0 0;">
        <button id="mic-btn" onclick="toggleListening()">🎤</button>
        <div id="status-text">Click the mic to start speaking</div>

        <!-- Waveform -->
        <div id="waveform">
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
        </div>

        <!-- Transcript -->
        <div id="transcript-display" class="empty">
            Your words will appear here as you speak...
        </div>
        <div id="error-msg"></div>

        <!-- Send button -->
        <button id="send-btn" onclick="sendTranscript()">Send to AI ✨</button>
    </div>

    <script>
        let recognition = null;
        let isListening = false;
        let finalTranscript = '';

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        function toggleListening() {{
            if (!SpeechRecognition) {{
                showError('⚠️ Your browser does not support voice input. Try Chrome or Edge.');
                return;
            }}
            if (isListening) {{
                stopListening();
            }} else {{
                startListening();
            }}
        }}

        function startListening() {{
            finalTranscript = '';
            recognition = new SpeechRecognition();
            recognition.lang = '{lang_code}';
            recognition.continuous = true;
            recognition.interimResults = true;

            recognition.onstart = () => {{
                isListening = true;
                document.getElementById('mic-btn').classList.add('listening');
                document.getElementById('mic-btn').textContent = '⏹️';
                document.getElementById('status-text').textContent = '🔴 Listening... Click to stop';
                document.getElementById('status-text').classList.add('listening');
                document.getElementById('waveform').classList.add('active');
                document.getElementById('send-btn').style.display = 'none';
                document.getElementById('error-msg').style.display = 'none';
                const box = document.getElementById('transcript-display');
                box.classList.remove('empty');
                box.textContent = '';
            }};

            recognition.onresult = (event) => {{
                let interimTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {{
                    if (event.results[i].isFinal) {{
                        finalTranscript += event.results[i][0].transcript + ' ';
                    }} else {{
                        interimTranscript += event.results[i][0].transcript;
                    }}
                }}
                const box = document.getElementById('transcript-display');
                box.innerHTML = finalTranscript + '<span style="color:#64748b">' + interimTranscript + '</span>';
            }};

            recognition.onerror = (event) => {{
                stopListening();
                if (event.error !== 'no-speech') {{
                    showError('⚠️ Error: ' + event.error + '. Make sure microphone access is allowed.');
                }}
            }};

            recognition.onend = () => {{
                if (isListening) stopListening();
            }};

            recognition.start();
        }}

        function stopListening() {{
            isListening = false;
            if (recognition) recognition.stop();
            document.getElementById('mic-btn').classList.remove('listening');
            document.getElementById('mic-btn').textContent = '🎤';
            document.getElementById('waveform').classList.remove('active');
            const statusEl = document.getElementById('status-text');
            statusEl.classList.remove('listening');

            if (finalTranscript.trim()) {{
                statusEl.textContent = '✅ Got it! Send to AI or click mic to redo';
                document.getElementById('send-btn').style.display = 'block';
            }} else {{
                statusEl.textContent = 'Click the mic to start speaking';
                const box = document.getElementById('transcript-display');
                box.classList.add('empty');
                box.textContent = 'Your words will appear here as you speak...';
            }}
        }}

        function sendTranscript() {{
            const text = finalTranscript.trim();
            if (!text) return;
            // Send to Streamlit via query param trick
            const input = document.createElement('input');
            input.style.display = 'none';
            document.body.appendChild(input);
            // Use Streamlit's component messaging
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: text
            }}, '*');
        }}

        function showError(msg) {{
            const el = document.getElementById('error-msg');
            el.textContent = msg;
            el.style.display = 'block';
        }}
    </script>
</div>
"""


# ── Layout: Mic on left, Chat on right ────────────────────────────────────────
col_mic, col_chat = st.columns([2, 3])

with col_mic:
    st.markdown("### 🎤 Speak")

    # Render STT component — returns transcript when "Send" is clicked
    transcript_result = components.html(stt_component, height=340, scrolling=False)

    st.markdown("---")
    st.markdown("**Or type your question:**")
    with st.form("voice_text_form", clear_on_submit=True):
        typed_input = st.text_input(
            "Type",
            placeholder="Type if mic doesn't work...",
            label_visibility="collapsed"
        )
        typed_submit = st.form_submit_button("Send ✨", use_container_width=True)

    # Manual transcript input (fallback / after browser sends value)
    st.markdown("**Paste voice transcript:**")
    with st.form("voice_paste_form", clear_on_submit=True):
        pasted = st.text_input(
            "Paste transcript",
            placeholder="Paste spoken text here and hit Send",
            label_visibility="collapsed"
        )
        paste_submit = st.form_submit_button("Send 🎤", use_container_width=True)


with col_chat:
    st.markdown("### 💬 Conversation")

    chat_area = st.container()

    with chat_area:
        if not st.session_state.voice_messages:
            st.markdown("""
            <div style='text-align:center;padding:50px 20px;color:#475569'>
                <div style='font-size:3rem'>🎤</div>
                <div style='font-size:1.05rem;color:#94a3b8;margin-top:10px'>
                    Start speaking or typing to chat with your AI tutor
                </div>
                <div style='font-size:0.85rem;margin-top:8px'>
                    Try: "Explain neural networks", "Add an exam deadline", "Quiz me on Python"
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            for msg in st.session_state.voice_messages:
                if msg["role"] == "user":
                    icon = "🎤" if msg.get("via_voice") else "⌨️"
                    st.markdown(
                        f'<div class="chat-bubble-user">{icon} {msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    intent = msg.get("intent", "general")
                    icon = AGENT_ICONS.get(intent, "🤖")
                    badge = f'<div class="agent-badge">{icon} {intent.replace("_"," ")}</div>'
                    st.markdown(f'<div class="chat-bubble-ai">{badge}', unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Auto-play TTS for last AI message
                    if (
                        st.session_state.tts_enabled
                        and msg == st.session_state.voice_messages[-1]
                        and msg.get("tts_b64")
                    ):
                        from tools.tts import get_audio_html
                        st.markdown(get_audio_html(msg["tts_b64"], autoplay=True), unsafe_allow_html=True)


# ── Process Input ─────────────────────────────────────────────────────────────

def process_voice_input(user_text: str, via_voice: bool = False):
    if not user_text.strip():
        return
    if not os.getenv("MISTRAL_API_KEY"):
        st.error("⚠️ Please set your Mistral API Key in the sidebar.")
        return

    st.session_state.voice_messages.append({
        "role": "user",
        "content": user_text.strip(),
        "via_voice": via_voice,
    })

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.voice_messages
    ]

    with st.spinner("🤖 Thinking..."):
        try:
            from agents.orchestrator import run_orchestrator
            result = run_orchestrator(history)
            response_text = result["response"]
            intent = result["intent"]

            # Generate TTS
            tts_b64 = ""
            if st.session_state.tts_enabled:
                from tools.tts import text_to_speech
                tts_b64 = text_to_speech(response_text, lang=st.session_state.tts_language)

            st.session_state.voice_messages.append({
                "role": "assistant",
                "content": response_text,
                "intent": intent,
                "tts_b64": tts_b64,
            })
        except Exception as e:
            st.session_state.voice_messages.append({
                "role": "assistant",
                "content": f"❌ Error: {str(e)}",
                "intent": "error",
                "tts_b64": "",
            })

    st.rerun()


# Typed input
if typed_submit and typed_input.strip():
    process_voice_input(typed_input.strip(), via_voice=False)

# Pasted transcript
if paste_submit and pasted.strip():
    process_voice_input(pasted.strip(), via_voice=True)

# Pending input from session (set by other mechanisms)
if st.session_state.get("voice_pending_input"):
    pending = st.session_state.voice_pending_input
    st.session_state.voice_pending_input = ""
    process_voice_input(pending, via_voice=True)
