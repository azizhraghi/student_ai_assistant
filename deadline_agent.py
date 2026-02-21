"""
Deadline Agent — manages student deadlines and study schedules.
Uses SQLite for persistent storage and Mistral for natural language interaction.
"""

import os
import json
import re
from datetime import datetime
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

from tools.db import (
    add_deadline, get_all_deadlines, update_deadline_status,
    delete_deadline, get_upcoming_deadlines
)


SYSTEM_PROMPT = """You are the Deadline Tracker Agent — a smart academic schedule manager.
You help students manage their deadlines, assignments, and study plans.

You have access to a database of deadlines. Based on the student's message, you must:
1. Detect the intent (add, list, complete, delete, upcoming, plan)
2. Extract relevant information
3. Return a JSON action object

Always respond with a JSON object in this exact format:
{
  "action": "<add|list|complete|delete|upcoming|plan|chat>",
  "data": {
    // For "add": { "title": str, "due_date": "YYYY-MM-DD", "subject": str, "priority": "low|medium|high", "notes": str }
    // For "complete" or "delete": { "id": int }
    // For "list": { "status": "pending|done|all" }
    // For "upcoming": { "days": int }
    // For "plan" or "chat": { "message": str }
  },
  "user_message": "<friendly confirmation message to show the student>"
}

Today's date is: """ + datetime.now().strftime("%Y-%m-%d") + """

Priority guidelines:
- high: exams, final projects, submissions due within 3 days
- medium: assignments, quizzes, due within a week
- low: readings, optional tasks, due in 2+ weeks

Always extract dates even if written naturally (e.g. "next Monday", "in 3 days", "end of the week").
Convert all dates to YYYY-MM-DD format."""


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.1,
    )


def parse_llm_action(raw: str) -> dict:
    """Extract JSON from LLM response."""
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"action": "chat", "data": {"message": raw}, "user_message": raw}


def format_deadline(d: dict) -> str:
    """Format a single deadline record for display."""
    priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    status_icons = {"pending": "⏳", "done": "✅", "overdue": "❌"}
    icon = priority_icons.get(d.get("priority", "medium"), "🟡")
    status = status_icons.get(d.get("status", "pending"), "⏳")
    subject = f" | {d['subject']}" if d.get("subject") else ""
    notes = f"\n   📝 {d['notes']}" if d.get("notes") else ""
    return (
        f"{status} **{d['title']}**{subject}\n"
        f"   {icon} Due: {d['due_date']} | ID: #{d['id']}{notes}"
    )


def format_deadlines_list(deadlines: list) -> str:
    if not deadlines:
        return "📭 No deadlines found."
    return "\n\n".join(format_deadline(d) for d in deadlines)


def execute_action(action_obj: dict) -> str:
    """Execute the DB action and return a formatted response."""
    action = action_obj.get("action", "chat")
    data = action_obj.get("data", {})
    user_msg = action_obj.get("user_message", "")

    if action == "add":
        try:
            record = add_deadline(
                title=data.get("title", "Untitled"),
                due_date=data.get("due_date", datetime.now().strftime("%Y-%m-%d")),
                subject=data.get("subject", ""),
                priority=data.get("priority", "medium"),
                notes=data.get("notes", ""),
            )
            return (
                f"✅ **Deadline added!**\n\n"
                f"{format_deadline(record)}\n\n"
                f"{user_msg}"
            )
        except Exception as e:
            return f"❌ Error adding deadline: {str(e)}"

    elif action == "list":
        status_filter = data.get("status", None)
        if status_filter == "all":
            status_filter = None
        deadlines = get_all_deadlines(status=status_filter)
        label = f"({status_filter})" if status_filter else "(all)"
        return f"📋 **Your Deadlines** {label}:\n\n{format_deadlines_list(deadlines)}"

    elif action == "upcoming":
        days = data.get("days", 7)
        deadlines = get_upcoming_deadlines(days=days)
        return (
            f"📅 **Upcoming Deadlines** (next {days} days):\n\n"
            f"{format_deadlines_list(deadlines)}"
        )

    elif action == "complete":
        did = data.get("id")
        if did and update_deadline_status(int(did), "done"):
            return f"✅ Deadline #{did} marked as **done**! Great work! 🎉"
        return f"❌ Could not find deadline #{did}."

    elif action == "delete":
        did = data.get("id")
        if did and delete_deadline(int(did)):
            return f"🗑️ Deadline #{did} deleted."
        return f"❌ Could not find deadline #{did}."

    else:
        # General chat or plan
        return user_msg if user_msg else data.get("message", "How can I help with your deadlines?")


def run_deadline_agent(user_message: str, conversation_history: list = None) -> str:
    """
    Run the Deadline Agent.

    Args:
        user_message: Student's natural language message
        conversation_history: Optional list of prior messages

    Returns:
        Formatted response string
    """
    llm = get_llm()

    # Provide current DB context to LLM
    current_deadlines = get_all_deadlines()
    db_context = ""
    if current_deadlines:
        db_context = "\n\nCurrent deadlines in the database:\n" + "\n".join(
            f"- ID#{d['id']}: {d['title']} | Due: {d['due_date']} | Status: {d['status']}"
            for d in current_deadlines
        )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT + db_context),
        HumanMessage(content=user_message)
    ])

    action_obj = parse_llm_action(response.content)
    return execute_action(action_obj)
