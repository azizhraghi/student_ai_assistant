"""
Collab Agent — AI agent for multi-student study rooms.
Generates group quizzes, shared summaries, and answers from merged content.
"""

import os
import json
import re
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


GROUP_QUIZ_PROMPT = """You are generating a group quiz for a collaborative study session.
Multiple students have uploaded different course materials. Create a unified quiz that covers ALL the materials.

Return ONLY a JSON object:
{
  "title": "Group Quiz Title",
  "questions": [
    {
      "id": 1,
      "question": "Question?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "A",
      "explanation": "Why this is correct",
      "source": "Which material this came from"
    }
  ]
}

Generate 8-12 questions. Mix difficulty levels. Cover all uploaded materials fairly."""


GROUP_SUMMARY_PROMPT = """You are creating a unified study summary for a collaborative study room.
Multiple students uploaded different materials. Create a cohesive summary that integrates all content.

Format your response as structured markdown with:
- An overview connecting all topics
- Key concepts from each material, clearly labelled
- How the topics relate to each other
- A "Master Study Guide" section at the end

Be thorough but organized. This is for group study."""


def generate_group_quiz(merged_content: str, member_names: list) -> dict:
    """Generate a quiz covering all uploaded materials."""
    llm = get_llm()

    content = merged_content[:12000] if len(merged_content) > 12000 else merged_content
    members_str = ", ".join(member_names)

    response = llm.invoke([
        SystemMessage(content=GROUP_QUIZ_PROMPT),
        HumanMessage(content=f"Study room members: {members_str}\n\n{content}\n\nGenerate the group quiz.")
    ])

    raw = response.content.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"title": "Group Quiz", "questions": []}


def generate_group_summary(merged_content: str, member_names: list) -> str:
    """Generate a unified summary of all uploaded materials."""
    llm = get_llm()

    content = merged_content[:12000] if len(merged_content) > 12000 else merged_content
    members_str = ", ".join(member_names)

    response = llm.invoke([
        SystemMessage(content=GROUP_SUMMARY_PROMPT),
        HumanMessage(content=f"Contributors: {members_str}\n\n{content}")
    ])
    return response.content


def answer_room_question(question: str, merged_content: str, username: str) -> str:
    """Answer a student's question using the room's merged content."""
    llm = get_llm()

    content = merged_content[:10000] if len(merged_content) > 10000 else merged_content
    context = f"\n\nRoom study materials:\n{content}" if content else ""

    response = llm.invoke([
        SystemMessage(content="""You are a collaborative AI tutor for a group study session.
Multiple students are studying together and have uploaded their materials.
Answer questions clearly and relate answers to the uploaded content when possible.
Be encouraging and mention when different students' materials complement each other."""),
        HumanMessage(content=f"{username} asks: {question}{context}")
    ])
    return response.content
