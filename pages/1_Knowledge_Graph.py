"""
Knowledge Graph Page — interactive concept map from course materials.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

load_dotenv()

# ── Styles ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    #MainMenu, footer, header { visibility: hidden; }

    .page-header { text-align: center; padding: 24px 0 8px 0; }
    .page-header h1 {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .page-header p { color: #64748b; font-size: 0.9rem; }

    .stat-card {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 12px; padding: 16px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stat-number { font-size: 2rem; font-weight: 800; color: #6366f1; }
    .stat-label { font-size: 0.8rem; color: #64748b; margin-top: 2px; }

    .legend-dot {
        display: inline-block; width: 12px; height: 12px;
        border-radius: 50%; margin-right: 6px;
    }
    .concept-pill {
        display: inline-block; background: #f1f5f9;
        border: 1px solid #6366f1; border-radius: 20px;
        padding: 4px 12px; margin: 3px;
        font-size: 0.8rem; color: #4f46e5;
    }
    .graph-container {
        border: 1px solid #e2e8f0; border-radius: 16px;
        overflow: hidden; background: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
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
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="page-header">
    <div style="color:#64748b; font-weight:600; font-size:1.1rem; margin-bottom: -8px; letter-spacing: 0.05em; text-transform: uppercase;">🎓 Student AI Assistant</div>
    <h1>🕸️ Knowledge Graph</h1>
    <p>Upload your course material and watch your knowledge come alive as an interactive concept map</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

from ui import render_sidebar
render_sidebar("🕸️ Knowledge Graph")

with st.sidebar:
    st.markdown("### 📁 Input Source")

    input_mode = st.radio(
        "Choose input",
        ["📄 Upload PDF/PPTX", "📝 Paste Text", "🌐 From URL"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### ⚙️ Options")
    user_hint = st.text_input(
        "Focus on (optional)",
        placeholder="e.g. 'neural networks', 'definitions only'",
    )

    st.markdown("---")
    st.markdown("### 🎨 Legend")
    legend_items = [
        ("#6366f1", "⭐ Core Topic"),
        ("#38bdf8", "● Concept"),
        ("#34d399", "◆ Method"),
        ("#f59e0b", "■ Definition"),
        ("#f472b6", "▲ Example"),
        ("#a78bfa", "○ Person"),
        ("#fb923c", "⬡ Formula"),
    ]
    for color, label in legend_items:
        st.markdown(
            f'<span class="legend-dot" style="background:{color}"></span>{label}',
            unsafe_allow_html=True
        )

    st.markdown("---")
    if st.button("🗑️ Clear Graph", use_container_width=True):
        st.session_state.pop("graph_result", None)
        st.rerun()

    st.markdown("""
    <div style='color:#475569; font-size:0.75rem; text-align:center; margin-top:8px'>
        ATLAS TBS Hackathon 2026<br>LangGraph + Mistral
    </div>
    """, unsafe_allow_html=True)

# ── Input Area ────────────────────────────────────────────────────────────────

content_to_process = ""
source_ready = False

if input_mode == "📄 Upload PDF/PPTX":
    uploaded = st.file_uploader(
        "Drop your PDF or PPTX here",
        type=["pdf", "pptx"],
        label_visibility="collapsed"
    )
    if uploaded:
        file_bytes = uploaded.read()
        ext = uploaded.name.split(".")[-1].lower()
        with st.spinner(f"Extracting text from {uploaded.name}..."):
            if ext == "pdf":
                from tools.pdf_parser import parse_pdf
                content_to_process = parse_pdf(file_bytes)
            elif ext == "pptx":
                from tools.pptx_parser import parse_pptx
                content_to_process = parse_pptx(file_bytes)
        st.success(f"✅ {uploaded.name} — {len(content_to_process):,} characters extracted")
        source_ready = True

elif input_mode == "📝 Paste Text":
    content_to_process = st.text_area(
        "Paste your course notes",
        height=180,
        placeholder="Paste lecture notes, textbook excerpts, or any academic content...",
        label_visibility="collapsed"
    )
    source_ready = bool(content_to_process.strip())

elif input_mode == "🌐 From URL":
    url = st.text_input("Enter URL", placeholder="https://en.wikipedia.org/wiki/...")
    if url:
        with st.spinner("Scraping content from URL..."):
            from tools.url_scraper import scrape_url
            content_to_process = scrape_url(url)
        if content_to_process.startswith("Error"):
            st.error(content_to_process)
        else:
            st.success(f"✅ {len(content_to_process):,} characters extracted")
            source_ready = True

# ── Generate Button ───────────────────────────────────────────────────────────

st.markdown("---")
col_btn, col_info = st.columns([2, 5])
with col_btn:
    generate = st.button(
        "🧠 Generate Knowledge Graph",
        use_container_width=True,
        disabled=not (source_ready and os.getenv("MISTRAL_API_KEY")),
        type="primary"
    )
with col_info:
    if not os.getenv("MISTRAL_API_KEY"):
        st.warning("⚠️ Set your Mistral API key in the sidebar")
    elif not source_ready:
        st.info("👆 Add course content above to get started")
    else:
        st.success("✅ Ready! Click 'Generate Knowledge Graph'")

# ── Graph Generation ──────────────────────────────────────────────────────────

if generate and source_ready and os.getenv("MISTRAL_API_KEY"):
    with st.spinner("🧠 Extracting concepts and building knowledge graph... (~15–20 sec)"):
        from agents.graph_agent import run_graph_agent
        result = run_graph_agent(content_to_process, user_hint=user_hint)
        st.session_state["graph_result"] = result

# ── Graph Display ─────────────────────────────────────────────────────────────

if "graph_result" in st.session_state:
    result = st.session_state["graph_result"]
    stats = result["stats"]
    graph_data = result["graph_data"]

    if not graph_data.get("nodes"):
        st.error("❌ Could not extract graph. Try adding more content or rephrasing.")
    else:
        st.markdown(f"### 🕸️ {result['title']}")

        # Stats row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["node_count"]}</div><div class="stat-label">Concepts</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{stats["edge_count"]}</div><div class="stat-label">Relationships</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{len(stats.get("categories", {}))}</div><div class="stat-label">Categories</div></div>', unsafe_allow_html=True)
        with c4:
            top = stats.get("top_concepts", [])
            top_label = top[0][0][:14] + "…" if top and len(top[0][0]) > 14 else (top[0][0] if top else "—")
            st.markdown(f'<div class="stat-card"><div class="stat-number" style="font-size:1rem;padding-top:8px">{top_label}</div><div class="stat-label">Central Concept</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Graph
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        components.html(result["html"], height=640, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style='color:#64748b; font-size:0.8rem; text-align:center; margin-top:8px'>
            🖱️ Drag to rearrange &nbsp;|&nbsp; 🔍 Scroll to zoom &nbsp;|&nbsp; 👆 Hover for details
        </div>""", unsafe_allow_html=True)

        # Insights
        st.markdown("---")
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### 🏆 Most Connected Concepts")
            for label, count in stats.get("top_concepts", []):
                st.markdown(f'<span class="concept-pill">🔗 {label} ({count} links)</span>', unsafe_allow_html=True)

        with col_right:
            st.markdown("#### 📊 Node Categories")
            cat_colors = {
                "core": "#6366f1", "concept": "#38bdf8", "method": "#34d399",
                "definition": "#f59e0b", "example": "#f472b6", "person": "#a78bfa", "formula": "#fb923c",
            }
            for cat, count in sorted(stats.get("categories", {}).items(), key=lambda x: -x[1]):
                color = cat_colors.get(cat, "#818cf8")
                st.markdown(f'<span class="concept-pill" style="border-color:{color};color:{color}">{cat.capitalize()} ({count})</span>', unsafe_allow_html=True)

        st.markdown("---")
        import json as _json
        st.download_button(
            "📥 Export Graph (JSON)",
            data=_json.dumps(graph_data, indent=2),
            file_name="knowledge_graph.json",
            mime="application/json",
        )

else:
    st.markdown("""
    <div style='text-align:center; padding: 60px 20px; color:#475569'>
        <div style='font-size:4rem'>🕸️</div>
        <div style='font-size:1.2rem; margin-top:12px; color:#94a3b8'>
            Upload course material to generate your knowledge graph
        </div>
        <div style='font-size:0.9rem; margin-top:8px'>
            The AI extracts concepts, definitions, methods, and their relationships — all rendered as an interactive map
        </div>
    </div>
    """, unsafe_allow_html=True)
