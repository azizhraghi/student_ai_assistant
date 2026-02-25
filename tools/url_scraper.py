"""
URL Scraper Tool — fetches and extracts readable text from a web page.
"""

import requests
from bs4 import BeautifulSoup


def scrape_url(url: str, timeout: int = 10) -> str:
    """
    Fetch a URL and extract clean readable text.
    Returns extracted text or an error message.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Extract main content
        main = soup.find("main") or soup.find("article") or soup.find("body")
        text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

        # Clean up excessive blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {str(e)}"
