"""
Orchestrator Agent — the brain of the multi-agent system.
Uses LangGraph to route student queries to the appropriate specialized agent.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os
import json
import re


# ─────────────────────────────────────────────
# State Definition
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    messages: list
    intent: str
    agent_response: str
    next_agent: str


# ─────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────

def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.1,
    )


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────

ROUTER_PROMPT = """You are the Orchestrator of a Student AI Assistant.
Detect the student's intent and route to the correct agent.

Agents:
- course_agent: uploading, summarizing, structuring course content, explaining topics from materials
- deadline_agent: adding/listing/completing/deleting deadlines, study schedules, reminders
- revision_agent: quizzes, flashcards, self-testing, revision summaries, "test me"
- research_agent: finding resources, web search, understanding topics, academic questions
- graph_agent: building knowledge graphs, visualizing concepts, concept maps, mind maps, "show me a graph", "visualize"
- general: greetings, unclear requests, meta questions about the assistant

Respond with ONLY a JSON object:
{"intent": "<agent_name>", "reasoning": "<one sentence>"}"""


def router_node(state: AgentState) -> AgentState:
    llm = get_llm()
    last_message = state["messages"][-1]["content"]

    response = llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=f"Student message: {last_message}")
    ])

    match = re.search(r'\{.*?\}', response.content, re.DOTALL)
    intent = "general"
    if match:
        try:
            parsed = json.loads(match.group())
            intent = parsed.get("intent", "general")
        except json.JSONDecodeError:
            pass

    return {**state, "intent": intent, "next_agent": intent}


# ─────────────────────────────────────────────
# Agent Nodes
# ─────────────────────────────────────────────

def general_agent_node(state: AgentState) -> AgentState:
    llm = get_llm()
    history = [SystemMessage(content="""You are a helpful Student AI Assistant.
Help students manage their studies, courses, deadlines, and revision.
Be concise, friendly, and encouraging.""")]
    for msg in state["messages"]:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))
    response = llm.invoke(history)
    return {**state, "agent_response": response.content}


def course_agent_node(state: AgentState) -> AgentState:
    from agents.course_agent import run_course_agent
    last_message = state["messages"][-1]["content"]
    result = run_course_agent(user_message=last_message)
    return {**state, "agent_response": result}


def deadline_agent_node(state: AgentState) -> AgentState:
    from agents.deadline_agent import run_deadline_agent
    last_message = state["messages"][-1]["content"]
    result = run_deadline_agent(user_message=last_message, conversation_history=state["messages"])
    return {**state, "agent_response": result}


def revision_agent_node(state: AgentState) -> AgentState:
    from agents.revision_agent import run_revision_agent
    last_message = state["messages"][-1]["content"]
    result = run_revision_agent(user_message=last_message)
    return {**state, "agent_response": result}


def research_agent_node(state: AgentState) -> AgentState:
    from agents.research_agent import run_research_agent
    last_message = state["messages"][-1]["content"]
    result = run_research_agent(user_message=last_message)
    return {**state, "agent_response": result}


def graph_agent_node(state: AgentState) -> AgentState:
    result = "🕸️ **Knowledge Graph ready!** Head to the **Knowledge Graph** page in the sidebar to generate an interactive concept map from your uploaded material.\n\nYou can also paste text directly on that page!"
    return {**state, "agent_response": result}


# ─────────────────────────────────────────────
# Routing Function
# ─────────────────────────────────────────────

def route_to_agent(state: AgentState) -> Literal[
    "general_agent", "course_agent", "deadline_agent", "revision_agent", "research_agent", "graph_agent"
]:
    intent = state.get("intent", "general")
    return {
        "course_agent": "course_agent",
        "deadline_agent": "deadline_agent",
        "revision_agent": "revision_agent",
        "research_agent": "research_agent",
        "graph_agent": "graph_agent",
    }.get(intent, "general_agent")


# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("general_agent", general_agent_node)
    graph.add_node("course_agent", course_agent_node)
    graph.add_node("deadline_agent", deadline_agent_node)
    graph.add_node("revision_agent", revision_agent_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("graph_agent", graph_agent_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges("router", route_to_agent, {
        "general_agent": "general_agent",
        "course_agent": "course_agent",
        "deadline_agent": "deadline_agent",
        "revision_agent": "revision_agent",
        "research_agent": "research_agent",
        "graph_agent": "graph_agent",
    })

    for node in ["general_agent", "course_agent", "deadline_agent", "revision_agent", "research_agent", "graph_agent"]:
        graph.add_edge(node, END)

    return graph.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_orchestrator(messages: list, extra: dict = None) -> dict:
    """
    Run the full multi-agent pipeline.

    Args:
        messages: Full conversation history [{"role": ..., "content": ...}]
        extra: Optional extra data (file_bytes, source_type, url, topic_content)

    Returns:
        {"response": str, "intent": str}
    """
    graph = get_graph()

    # If extra data provided (file upload, url), inject into course/revision agent directly
    if extra:
        intent = extra.get("force_intent", "")
        if intent == "course_agent":
            from agents.course_agent import run_course_agent
            result = run_course_agent(
                user_message=messages[-1]["content"],
                source_type=extra.get("source_type", "text"),
                source_content=extra.get("source_content", ""),
                file_bytes=extra.get("file_bytes"),
                url=extra.get("url", ""),
            )
            return {"response": result, "intent": "course_agent"}
        elif intent == "revision_agent":
            from agents.revision_agent import run_revision_agent
            result = run_revision_agent(
                user_message=messages[-1]["content"],
                topic_content=extra.get("topic_content", ""),
            )
            return {"response": result, "intent": "revision_agent"}

    initial_state: AgentState = {
        "messages": messages,
        "intent": "",
        "agent_response": "",
        "next_agent": "",
    }

    result = graph.invoke(initial_state)
    return {"response": result["agent_response"], "intent": result["intent"]}
