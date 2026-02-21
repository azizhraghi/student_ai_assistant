"""
Revision Agent — generates quizzes, flashcards, and revision summaries
to help students actively study and retain information.
"""

import os
import json
import re
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage


QUIZ_SYSTEM_PROMPT = """You are the Revision Agent — an expert at creating engaging study materials.
You generate quizzes, flashcards, and revision content to help students learn effectively.

When generating a QUIZ, respond with JSON in this exact format:
{
  "type": "quiz",
  "title": "Quiz title",
  "questions": [
    {
      "id": 1,
      "question": "Question text?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": "A",
      "explanation": "Brief explanation of why this is correct"
    }
  ]
}

When generating FLASHCARDS, respond with JSON in this exact format:
{
  "type": "flashcards",
  "title": "Flashcard set title",
  "cards": [
    {
      "id": 1,
      "front": "Term or question",
      "back": "Definition or answer"
    }
  ]
}

When generating a SUMMARY for revision, respond with JSON:
{
  "type": "summary",
  "title": "Summary title",
  "content": "Structured markdown summary text"
}

Always generate at least 5 items (questions or cards) unless asked for fewer.
Make questions progressively harder. Cover key concepts thoroughly."""


CHAT_SYSTEM_PROMPT = """You are the Revision Agent — a friendly, expert tutor.
Help students revise by explaining concepts, answering questions, and creating study materials.
Be encouraging, clear, and pedagogically effective."""


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.4,
    )


def detect_revision_mode(message: str) -> str:
    """Detect if the student wants a quiz, flashcards, summary, or general chat."""
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["quiz", "test me", "question", "mcq", "multiple choice"]):
        return "quiz"
    if any(w in msg_lower for w in ["flashcard", "flash card", "card", "term", "definition"]):
        return "flashcards"
    if any(w in msg_lower for w in ["summary", "summarize", "revise", "recap", "overview", "notes"]):
        return "summary"
    return "chat"


def parse_json_response(raw: str) -> dict | None:
    """Extract JSON from LLM response."""
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def format_quiz(data: dict) -> str:
    """Format quiz JSON into readable markdown."""
    lines = [f"## 📝 {data.get('title', 'Quiz')}\n"]
    for q in data.get("questions", []):
        lines.append(f"**Q{q['id']}.** {q['question']}")
        for opt in q.get("options", []):
            lines.append(f"  - {opt}")
        lines.append(f"  ✅ **Answer:** {q['answer']}")
        if q.get("explanation"):
            lines.append(f"  💡 *{q['explanation']}*")
        lines.append("")
    return "\n".join(lines)


def format_flashcards(data: dict) -> str:
    """Format flashcards JSON into readable markdown."""
    lines = [f"## 🃏 {data.get('title', 'Flashcards')}\n"]
    for card in data.get("cards", []):
        lines.append(f"**Card {card['id']}**")
        lines.append(f"  **Front:** {card['front']}")
        lines.append(f"  **Back:** {card['back']}")
        lines.append("")
    return "\n".join(lines)


def format_summary(data: dict) -> str:
    """Format summary JSON."""
    return f"## 📖 {data.get('title', 'Revision Summary')}\n\n{data.get('content', '')}"


def run_revision_agent(user_message: str, topic_content: str = "") -> str:
    """
    Run the Revision Agent.

    Args:
        user_message: What the student wants (quiz, flashcards, etc.)
        topic_content: Optional course content to base the revision on

    Returns:
        Formatted revision material as a string
    """
    llm = get_llm()
    mode = detect_revision_mode(user_message)

    if mode == "chat":
        # General revision question — no structured output needed
        context = f"\n\nCourse material provided:\n{topic_content[:6000]}" if topic_content else ""
        response = llm.invoke([
            SystemMessage(content=CHAT_SYSTEM_PROMPT),
            HumanMessage(content=user_message + context)
        ])
        return response.content

    # Structured generation (quiz / flashcards / summary)
    content_block = ""
    if topic_content:
        content_block = f"\n\nBase your content on this course material:\n{topic_content[:8000]}"

    prompt = f"{user_message}{content_block}"

    response = llm.invoke([
        SystemMessage(content=QUIZ_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    parsed = parse_json_response(response.content)

    if parsed:
        t = parsed.get("type", mode)
        if t == "quiz":
            return format_quiz(parsed)
        elif t == "flashcards":
            return format_flashcards(parsed)
        elif t == "summary":
            return format_summary(parsed)

    # Fallback: return raw response
    return response.content
