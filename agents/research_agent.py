"""
Research Agent — finds academic resources, explanations, and references
using DuckDuckGo search and synthesizes results with Mistral.
"""

import os
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


SYSTEM_PROMPT = """You are the Research Agent — an expert academic researcher and tutor.
You help students find information, understand topics deeply, and discover learning resources.

When you have search results, synthesize them into a clear, structured response:
1. **Direct Answer** — Answer the question directly and concisely
2. **Key Points** — Bullet points with the most important information  
3. **Deeper Explanation** — More detail for students who want to understand fully
4. **Resources** — Suggest further reading or resources

When you don't have search results, use your knowledge to provide a thorough academic explanation.

Always cite sources when available. Be academically rigorous but student-friendly.
Use examples and analogies to make complex topics accessible."""


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Perform a DuckDuckGo search and return results."""
    if not DDGS_AVAILABLE:
        return []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception:
        return []


def format_search_results(results: list[dict]) -> str:
    """Format search results for inclusion in the LLM prompt."""
    if not results:
        return ""
    lines = ["Search Results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] {r.get('title', 'No title')}")
        lines.append(f"    URL: {r.get('href', '')}")
        lines.append(f"    {r.get('body', '')[:400]}")
    return "\n".join(lines)


def run_research_agent(user_message: str, search_query: str = "") -> str:
    """
    Run the Research Agent.

    Args:
        user_message: Student's research question or topic
        search_query: Optional custom search query (defaults to user_message)

    Returns:
        Research summary and resources as a string
    """
    llm = get_llm()

    # Perform web search
    query = search_query if search_query else user_message
    search_results = search_web(query, max_results=5)
    search_context = format_search_results(search_results)

    if search_context:
        prompt = f"""Student question: {user_message}

{search_context}

Using the search results above, provide a comprehensive, student-friendly answer.
Include source references where relevant."""
    else:
        prompt = f"""Student question: {user_message}

No web search results available. Answer based on your academic knowledge.
Be thorough and suggest where the student might find more information."""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    # Append source links if available
    result = response.content
    if search_results:
        result += "\n\n---\n**🔗 Sources:**\n"
        for i, r in enumerate(search_results[:3], 1):
            title = r.get("title", "Source")[:60]
            url = r.get("href", "")
            if url:
                result += f"{i}. [{title}]({url})\n"

    return result
