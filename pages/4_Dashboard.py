"""
Smart Progress Dashboard — full student analytics with AI weekly report.
Pulls real data from all agents: quiz scores, deadlines, sessions, topics.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    #MainMenu, footer, header { visibility: hidden; }

    .page-header { text-align: center; padding: 24px 0 4px; }
    .page-header h1 {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .page-header p { color: #64748b; font-size: 0.9rem; }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 14px 14px 0 0;
    }
    .kpi-card.blue::before   { background: linear-gradient(90deg, #38bdf8, #6366f1); }
    .kpi-card.purple::before { background: linear-gradient(90deg, #6366f1, #a855f7); }
    .kpi-card.green::before  { background: linear-gradient(90deg, #10b981, #38bdf8); }
    .kpi-card.orange::before { background: linear-gradient(90deg, #f97316, #f59e0b); }
    .kpi-card.pink::before   { background: linear-gradient(90deg, #ec4899, #f97316); }
    .kpi-card.indigo::before { background: linear-gradient(90deg, #6366f1, #818cf8); }

    .kpi-value {
        font-size: 2.4rem;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-label { font-size: 0.78rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-sub   { font-size: 0.8rem; color: #94a3b8; margin-top: 4px; }

    .kpi-card.blue   .kpi-value { color: #38bdf8; }
    .kpi-card.purple .kpi-value { color: #6366f1; }
    .kpi-card.green  .kpi-value { color: #10b981; }
    .kpi-card.orange .kpi-value { color: #f97316; }
    .kpi-card.pink   .kpi-value { color: #ec4899; }
    .kpi-card.indigo .kpi-value { color: #6366f1; }

    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        margin: 24px 0 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .insight-box {
        background: linear-gradient(135deg, #f1f5f9, #ede9fe);
        border: 1px solid #e2e8f0;
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        padding: 16px 20px;
        font-size: 0.92rem;
        color: #334155;
        line-height: 1.6;
        margin-bottom: 16px;
    }

    .report-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px 28px;
        line-height: 1.8;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .topic-bar-label { font-size: 0.82rem; color: #334155; }
    .topic-bar-track {
        background: #e2e8f0;
        border-radius: 6px;
        height: 10px;
        margin: 4px 0 10px;
        overflow: hidden;
    }
    .topic-bar-fill {
        height: 10px;
        border-radius: 6px;
        background: linear-gradient(90deg, #6366f1, #38bdf8);
    }

    .deadline-chip {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 3px;
    }
    .deadline-chip.done    { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
    .deadline-chip.pending { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
    .deadline-chip.overdue { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

    .chart-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .chart-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
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


# ── Sidebar ───────────────────────────────────────────────────────────────────
from ui import render_sidebar
render_sidebar("📊 Smart Dashboard")

with st.sidebar:

    st.markdown("---")
    st.markdown("### ⚙️ Options")

    time_range = st.selectbox("Time range", ["Last 7 days", "Last 30 days", "Last 90 days"])
    days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
    selected_days = days_map[time_range]

    st.markdown("---")
    if st.button("🌱 Load Demo Data", use_container_width=True, help="Seed realistic sample data"):
        from tools.study_tracker import seed_demo_data
        seed_demo_data()
        st.success("✅ Demo data loaded!")
        st.rerun()

    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.session_state.pop("ai_report", None)
        st.session_state.pop("ai_insight", None)
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style='color:#475569;font-size:0.72rem;text-align:center'>
        ATLAS TBS Hackathon 2026<br>LangGraph + Mistral
    </div>
    """, unsafe_allow_html=True)


# ── Load Data ─────────────────────────────────────────────────────────────────
from tools.study_tracker import get_full_summary, get_daily_activity, get_agent_usage, get_quiz_history, get_quiz_stats, get_topic_frequency, get_study_streak
from tools.db import get_all_deadlines

summary = get_full_summary(selected_days)
streak = summary["streak"]
quiz_stats = summary["quiz_stats"]
agent_usage = summary["agent_usage"]
daily_activity = summary["daily_activity"]
topics = summary["topic_frequency"]
deadlines_data = summary["deadlines"]
quiz_history = summary["quiz_history"]


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div style="color:#64748b; font-weight:600; font-size:1.1rem; margin-bottom: -8px; letter-spacing: 0.05em; text-transform: uppercase;">🎓 Student AI Assistant</div>
    <h1>📊 Smart Dashboard</h1>
    <p>Your personalized learning analytics — powered by AI</p>
</div>
""", unsafe_allow_html=True)

# Last updated
st.markdown(
    f"<div style='text-align:right;color:#475569;font-size:0.75rem;margin-bottom:8px'>Last updated: {datetime.now().strftime('%B %d, %Y · %H:%M')}</div>",
    unsafe_allow_html=True
)


# ── AI Quick Insight ──────────────────────────────────────────────────────────
if os.getenv("MISTRAL_API_KEY"):
    if "ai_insight" not in st.session_state:
        with st.spinner("🤖 Generating AI insight..."):
            from agents.analytics_agent import get_quick_insight
            st.session_state["ai_insight"] = get_quick_insight(summary)

    st.markdown(f"""
    <div class="insight-box">
        🤖 <strong>AI Coach Says:</strong><br>{st.session_state["ai_insight"]}
    </div>
    """, unsafe_allow_html=True)


# ── KPI Row ───────────────────────────────────────────────────────────────────
total_sessions = sum(d["count"] for d in daily_activity)
avg_score = quiz_stats.get("avg_score", 0) or 0
best_score = quiz_stats.get("best_score", 0) or 0
total_quizzes = quiz_stats.get("total_attempts", 0) or 0

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""<div class="kpi-card blue">
        <div class="kpi-value">{streak['current']}</div>
        <div class="kpi-label">Day Streak 🔥</div>
        <div class="kpi-sub">Best: {streak['longest']} days</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="kpi-card purple">
        <div class="kpi-value">{total_sessions}</div>
        <div class="kpi-label">Study Sessions</div>
        <div class="kpi-sub">Last {selected_days} days</div>
    </div>""", unsafe_allow_html=True)

with c3:
    score_color = "green" if avg_score >= 70 else "orange"
    st.markdown(f"""<div class="kpi-card {score_color}">
        <div class="kpi-value">{avg_score:.0f}%</div>
        <div class="kpi-label">Avg Quiz Score</div>
        <div class="kpi-sub">Best: {best_score:.0f}%</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""<div class="kpi-card indigo">
        <div class="kpi-value">{total_quizzes}</div>
        <div class="kpi-label">Quizzes Taken</div>
        <div class="kpi-sub">{quiz_stats.get('total_questions',0)} questions answered</div>
    </div>""", unsafe_allow_html=True)

with c5:
    done = deadlines_data.get("done", 0)
    total_dl = deadlines_data.get("total", 0)
    completion = round(done / total_dl * 100) if total_dl else 0
    st.markdown(f"""<div class="kpi-card pink">
        <div class="kpi-value">{completion}%</div>
        <div class="kpi-label">Deadline Rate</div>
        <div class="kpi-sub">{done}/{total_dl} completed</div>
    </div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""<div class="kpi-card orange">
        <div class="kpi-value">{streak['total_days']}</div>
        <div class="kpi-label">Active Days</div>
        <div class="kpi-sub">Total study days</div>
    </div>""", unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)


# ── Charts Row 1: Activity + Quiz Trend ──────────────────────────────────────
col_activity, col_quiz = st.columns([3, 2])

with col_activity:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📅 Daily Study Activity</div>', unsafe_allow_html=True)

    if daily_activity:
        import altair as alt
        import pandas as pd

        df_activity = pd.DataFrame(daily_activity)
        df_activity["date"] = pd.to_datetime(df_activity["date"])

        chart = alt.Chart(df_activity).mark_area(
            line={"color": "#6366f1", "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="#6366f1", offset=0),
                    alt.GradientStop(color="#f8fafc00", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            ),
            point=alt.OverlayMarkDef(color="#6366f1", size=50),
        ).encode(
            x=alt.X("date:T", axis=alt.Axis(format="%b %d", labelColor="#64748b", gridColor="#f1f5f9", tickColor="#e2e8f0")),
            y=alt.Y("count:Q", axis=alt.Axis(labelColor="#64748b", gridColor="#f1f5f9", tickColor="#e2e8f0"), title="Sessions"),
            tooltip=[alt.Tooltip("date:T", format="%b %d"), alt.Tooltip("count:Q", title="Sessions")],
        ).properties(height=200, background="#ffffff").configure_view(strokeWidth=0)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No activity data yet. Start studying!")
    st.markdown('</div>', unsafe_allow_html=True)

with col_quiz:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📈 Quiz Score Trend</div>', unsafe_allow_html=True)

    if quiz_history:
        import altair as alt
        import pandas as pd

        df_quiz = pd.DataFrame(quiz_history)
        df_quiz["attempt"] = range(1, len(df_quiz) + 1)
        df_quiz["label"] = df_quiz["topic"].str[:12] + " #" + df_quiz["attempt"].astype(str)

        # Color by performance
        df_quiz["color"] = df_quiz["pct"].apply(
            lambda x: "#34d399" if x >= 80 else "#f59e0b" if x >= 60 else "#f87171"
        )

        base = alt.Chart(df_quiz)

        line = base.mark_line(
            color="#38bdf8", strokeWidth=2, strokeDash=[4, 2]
        ).encode(
            x=alt.X("attempt:O", axis=alt.Axis(labelColor="#64748b", gridColor="#f1f5f9")),
            y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(labelColor="#64748b", gridColor="#f1f5f9"), title="Score %"),
        )

        points = base.mark_circle(size=80).encode(
            x="attempt:O",
            y="pct:Q",
            color=alt.Color("color:N", scale=None),
            tooltip=[alt.Tooltip("topic:N"), alt.Tooltip("pct:Q", title="Score %"), alt.Tooltip("date:N")],
        )

        chart = (line + points).properties(height=200, background="#ffffff").configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

        # Legend
        st.markdown("""
        <div style='font-size:0.72rem;color:#64748b;margin-top:4px'>
            🟢 ≥80% &nbsp; 🟡 60-79% &nbsp; 🔴 <60%
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No quizzes taken yet.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Charts Row 2: Agent Usage + Topics ───────────────────────────────────────
col_agents, col_topics = st.columns([2, 3])

with col_agents:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">🤖 Agent Usage</div>', unsafe_allow_html=True)

    if agent_usage:
        import altair as alt
        import pandas as pd

        AGENT_COLORS = {
            "course_agent":   "#38bdf8",
            "revision_agent": "#818cf8",
            "deadline_agent": "#34d399",
            "research_agent": "#f59e0b",
            "general":        "#f472b6",
            "collab":         "#a78bfa",
        }
        AGENT_LABELS = {
            "course_agent":   "📚 Course",
            "revision_agent": "✏️ Revision",
            "deadline_agent": "📅 Deadlines",
            "research_agent": "🔍 Research",
            "general":        "🧠 General",
            "collab":         "👥 Collab",
        }

        df_agents = pd.DataFrame([
            {"agent": AGENT_LABELS.get(k, k), "count": v, "color": AGENT_COLORS.get(k, "#818cf8")}
            for k, v in sorted(agent_usage.items(), key=lambda x: -x[1])
        ])

        chart = alt.Chart(df_agents).mark_bar(
            cornerRadiusTopLeft=4, cornerRadiusTopRight=4
        ).encode(
            x=alt.X("count:Q", axis=alt.Axis(labelColor="#64748b", gridColor="#f1f5f9"), title="Sessions"),
            y=alt.Y("agent:N", sort="-x", axis=alt.Axis(labelColor="#64748b"), title=""),
            color=alt.Color("color:N", scale=None),
            tooltip=["agent:N", "count:Q"],
        ).properties(height=220, background="#ffffff").configure_view(strokeWidth=0)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No agent usage data yet.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_topics:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📚 Most Studied Topics</div>', unsafe_allow_html=True)

    if topics:
        max_count = max(t["count"] for t in topics)
        gradient_colors = [
            "linear-gradient(90deg, #6366f1, #818cf8)",
            "linear-gradient(90deg, #818cf8, #38bdf8)",
            "linear-gradient(90deg, #38bdf8, #34d399)",
            "linear-gradient(90deg, #34d399, #f59e0b)",
            "linear-gradient(90deg, #f59e0b, #f472b6)",
            "linear-gradient(90deg, #f472b6, #fb923c)",
            "linear-gradient(90deg, #fb923c, #f87171)",
            "linear-gradient(90deg, #f87171, #fca5a5)",
        ]
        for i, t in enumerate(topics):
            pct = int(t["count"] / max_count * 100)
            color = gradient_colors[i % len(gradient_colors)]
            st.markdown(f"""
            <div class="topic-bar-label">{t['topic']} <span style='float:right;color:#64748b'>{t['count']} sessions</span></div>
            <div class="topic-bar-track">
                <div class="topic-bar-fill" style="width:{pct}%;background:{color}"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No topic data yet.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Deadlines Overview ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🗓️ Deadlines Overview</div>', unsafe_allow_html=True)

all_deadlines = get_all_deadlines()
if all_deadlines:
    col_dl1, col_dl2 = st.columns([2, 1])
    with col_dl1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        for d in sorted(all_deadlines, key=lambda x: x["due_date"])[:8]:
            status_map = {
                "done": ("done", "✅"),
                "pending": ("pending", "⏳"),
                "overdue": ("overdue", "❌"),
            }
            cls, icon = status_map.get(d["status"], ("pending", "⏳"))
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            p_icon = priority_icons.get(d.get("priority", "medium"), "🟡")
            subj = f" · {d['subject']}" if d.get("subject") else ""
            st.markdown(
                f'<span class="deadline-chip {cls}">{icon} {d["title"]}{subj} · {d["due_date"]} {p_icon}</span>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_dl2:
        st.markdown('<div class="chart-card" style="text-align:center">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Completion</div>', unsafe_allow_html=True)
        done_c = sum(1 for d in all_deadlines if d["status"] == "done")
        pend_c = sum(1 for d in all_deadlines if d["status"] == "pending")
        over_c = sum(1 for d in all_deadlines if d["status"] == "overdue")

        if all_deadlines:
            import altair as alt
            import pandas as pd

            df_dl = pd.DataFrame([
                {"status": "Done ✅", "count": done_c, "color": "#34d399"},
                {"status": "Pending ⏳", "count": pend_c, "color": "#38bdf8"},
                {"status": "Overdue ❌", "count": over_c, "color": "#f87171"},
            ])
            pie = alt.Chart(df_dl).mark_arc(innerRadius=50, outerRadius=80).encode(
                theta=alt.Theta("count:Q"),
                color=alt.Color("color:N", scale=None, legend=alt.Legend(labelColor="#94a3b8")),
                tooltip=["status:N", "count:Q"],
            ).properties(height=180, background="#ffffff").configure_view(strokeWidth=0)
            st.altair_chart(pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No deadlines tracked yet. Add some from the main chat!")


# ── AI Weekly Report ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🤖 AI Weekly Study Report</div>', unsafe_allow_html=True)

col_gen, col_dl = st.columns([2, 1])
with col_gen:
    generate_btn = st.button(
        "🧠 Generate My AI Report",
        type="primary",
        use_container_width=False,
        disabled=not os.getenv("MISTRAL_API_KEY"),
    )
with col_dl:
    if "ai_report" in st.session_state:
        st.download_button(
            "📥 Download Report",
            data=st.session_state["ai_report"],
            file_name=f"study_report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )

if generate_btn:
    with st.spinner("🤖 Analyzing your data and writing your personalized report..."):
        from agents.analytics_agent import generate_weekly_report
        report = generate_weekly_report(summary)
        st.session_state["ai_report"] = report
    st.rerun()

if "ai_report" in st.session_state:
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(st.session_state["ai_report"])
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div style='background:#f1f5f9;border:1px dashed #cbd5e1;border-radius:14px;
                padding:32px;text-align:center;color:#64748b'>
        <div style='font-size:2rem'>🤖</div>
        <div style='margin-top:8px;font-size:0.95rem;color:#475569'>
            Click "Generate My AI Report" to get a personalized analysis<br>
            of your study patterns, quiz performance, and recommended actions.
        </div>
    </div>
    """, unsafe_allow_html=True)
