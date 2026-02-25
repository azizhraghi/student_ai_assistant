"""
Course Agent — processes course materials from multiple sources and provides
structured summaries, key concepts, and explanations.

Supported inputs: PDF, PowerPoint (.pptx), URL, plain text
"""

import os
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

from tools.pdf_parser import parse_pdf
from tools.pptx_parser import parse_pptx
from tools.url_scraper import scrape_url


SYSTEM_PROMPT = """You are the Course Structuring Agent — an expert academic assistant.
You receive course material (from PDFs, slides, web pages, or text) and help students understand it.

Your capabilities:
1. **Summarize** — Create concise, structured summaries of course content
2. **Key Concepts** — Extract and explain the most important concepts
3. **Structure** — Organize content into logical sections with clear headings
4. **Explain** — Break down complex topics into simple, understandable language
5. **Study Notes** — Convert raw material into clean, study-ready notes

Always format your response clearly with:
- A brief overview at the top
- Organized sections with headers
- Bullet points for key facts
- Highlighted important terms in **bold**
- A "Quick Review" summary at the end

Be thorough but concise. Focus on what a student needs to learn and remember."""


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.2,
    )


# ── Source Processors ──────────────────────────────────────────────────────────

def process_pdf(file_bytes: bytes) -> str:
    return parse_pdf(file_bytes)


def process_pptx(file_bytes: bytes) -> str:
    return parse_pptx(file_bytes)


def process_url(url: str) -> str:
    return scrape_url(url)


def process_text(text: str) -> str:
    return text


# ── Main Agent Function ────────────────────────────────────────────────────────

def run_course_agent(
    user_message: str,
    source_type: str = "text",
    source_content: str = "",
    file_bytes: bytes = None,
    url: str = "",
) -> str:
    """
    Run the Course Agent.

    Args:
        user_message: What the student wants (summarize, explain, etc.)
        source_type: One of 'pdf', 'pptx', 'url', 'text'
        source_content: Raw text content (for 'text' type)
        file_bytes: Raw file bytes (for 'pdf' or 'pptx')
        url: URL string (for 'url' type)

    Returns:
        Structured course notes / summary as a string.
    """
    llm = get_llm()

    # Extract content based on source type
    extracted_content = ""
    source_label = ""

    if source_type == "pdf" and file_bytes:
        extracted_content = process_pdf(file_bytes)
        source_label = "📄 PDF Document"
    elif source_type == "pptx" and file_bytes:
        extracted_content = process_pptx(file_bytes)
        source_label = "📊 PowerPoint Presentation"
    elif source_type == "url" and url:
        extracted_content = process_url(url)
        source_label = f"🌐 Web Page: {url}"
    elif source_type == "text" and source_content:
        extracted_content = source_content
        source_label = "📝 Plain Text"
    else:
        # No source provided — treat as a general course question
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ])
        return response.content

    # Truncate if too long (Mistral context limit safety)
    max_chars = 12000
    if len(extracted_content) > max_chars:
        extracted_content = extracted_content[:max_chars] + "\n\n[Content truncated for length...]"

    prompt = f"""Source: {source_label}

--- COURSE MATERIAL ---
{extracted_content}
--- END OF MATERIAL ---

Student request: {user_message}

Please process the above course material according to the student's request."""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    return response.content
