"""
Analytics Agent — generates a personalized AI weekly study report
based on real tracked data: sessions, quiz scores, deadlines, topics.
"""

import os
import json
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage


REPORT_PROMPT = """You are an expert academic coach and learning analyst.
You have access to a student's real study data for the past 30 days.
Generate a personalized, insightful weekly study report.

Your report must include:

## 📊 Performance Summary
Brief overview of this week vs last week.

## 💪 Strengths
What the student is doing well — be specific, reference actual topics and scores.

## 🎯 Areas to Improve
2-3 specific, actionable areas where performance is lacking. Be direct but encouraging.

## 📈 Quiz Progress
Analyze the score trend. Is the student improving? What topics need more focus?

## ⚡ This Week's Priority
The single most important thing the student should focus on right now, with a specific action plan.

## 🗓️ Recommended Study Plan
A concrete day-by-day suggestion for the next 5 days based on pending deadlines and weak topics.

## 🏆 Motivational Close
One powerful, personalized sentence to keep the student going.

Be specific, data-driven, and genuinely helpful. Reference actual numbers from the data.
Avoid generic advice. Every recommendation must be tied to the actual student data provided."""


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.4,
    )


def generate_weekly_report(analytics_data: dict) -> str:
    """
    Generate a personalized AI weekly report from analytics data.

    Args:
        analytics_data: Full summary dict from study_tracker.get_full_summary()

    Returns:
        Markdown-formatted report string
    """
    llm = get_llm()

    # Build human-readable data summary for the LLM
    streak = analytics_data.get("streak", {})
    quiz_stats = analytics_data.get("quiz_stats", {})
    agent_usage = analytics_data.get("agent_usage", {})
    topics = analytics_data.get("topic_frequency", [])
    deadlines = analytics_data.get("deadlines", {})
    quiz_history = analytics_data.get("quiz_history", [])
    daily = analytics_data.get("daily_activity", [])

    # Compute week totals
    total_sessions = sum(d["count"] for d in daily)
    last_7 = sum(d["count"] for d in daily[-7:])
    prev_7 = sum(d["count"] for d in daily[-14:-7])

    top_topics = [t["topic"] for t in topics[:5]]
    recent_quiz_scores = [f"{q['topic']}: {q['pct']}%" for q in quiz_history[-5:]]

    data_summary = f"""
STUDENT STUDY DATA (Last 30 days):

Study Activity:
- Total study sessions: {total_sessions}
- Last 7 days: {last_7} sessions
- Previous 7 days: {prev_7} sessions
- Current study streak: {streak.get('current', 0)} days
- Longest streak ever: {streak.get('longest', 0)} days
- Total active study days: {streak.get('total_days', 0)}

Agent Usage (what the student used most):
{json.dumps(agent_usage, indent=2)}

Quiz Performance:
- Total quizzes taken: {quiz_stats.get('total_attempts', 0)}
- Average score: {quiz_stats.get('avg_score', 0)}%
- Best score: {quiz_stats.get('best_score', 0)}%
- Total questions answered: {quiz_stats.get('total_questions', 0)}
- Recent quiz scores: {', '.join(recent_quiz_scores) if recent_quiz_scores else 'None yet'}

Top Studied Topics: {', '.join(top_topics) if top_topics else 'None tracked yet'}

Deadlines:
- Completed: {deadlines.get('done', 0)}
- Pending: {deadlines.get('pending', 0)}
- Total: {deadlines.get('total', 0)}
"""

    response = llm.invoke([
        SystemMessage(content=REPORT_PROMPT),
        HumanMessage(content=data_summary)
    ])

    return response.content


def get_quick_insight(analytics_data: dict) -> str:
    """Generate a short 2-sentence AI insight for the dashboard header."""
    llm = get_llm()

    streak = analytics_data.get("streak", {})
    quiz_stats = analytics_data.get("quiz_stats", {})
    last_7 = sum(d["count"] for d in analytics_data.get("daily_activity", [])[-7:])

    response = llm.invoke([
        SystemMessage(content="You are a supportive academic coach. Write exactly 2 sentences: one observation about the student's recent activity and one specific recommendation. Be direct and data-driven. No fluff."),
        HumanMessage(content=f"Student stats: {last_7} study sessions this week, {streak.get('current',0)}-day streak, average quiz score {quiz_stats.get('avg_score',0)}%.")
    ])
    return response.content
