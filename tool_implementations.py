#  TOOL IMPLEMENTATIONS
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup          # For parsing HTML content from web pages
from ddgs import DDGS     # For performing web searches without needing an API key
from groq import Groq
import urllib3

urllib3.disable_warnings()
load_dotenv()
client  = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def web_search(query: str, max_results: int = 5) -> str:
    """
    Search DuckDuckGo and return titles, URLs, and snippets.
    DuckDuckGo requires no API key — completely free.
    """
    try:
        results = []
        # Use DDGS context manager to perform a text search
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                # Format each result as a readable block
                results.append(
                    f"Title: {r['title']}\n"
                    f"URL:   {r['href']}\n"
                    f"Snippet: {r['body']}\n"
                )

        # Return early if no results were found
        if not results:
            return "No results found."

        # Join all results with a separator for readability
        return f"Search results for '{query}':\n\n" + "\n---\n".join(results)

    except Exception as e:
        return f"Search failed: {e}"

def read_page(url: str, max_chars: int = 3000) -> str:
    """
    Fetch a webpage and extract clean readable text.
    Strips all HTML tags, scripts, and navigation.
    """
    try:
        # Mimic a browser user-agent to avoid bot-blocking
        headers = {"User-Agent": "Mozilla/5.0 (research bot)"}
        resp    = requests.get(url, headers=headers, timeout=10, verify=False)
        resp.raise_for_status()  # Raise an error for non-2xx HTTP responses

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noisy/non-content tags from the DOM
        for tag in soup(["script", "style", "nav", "footer",
                         "header", "aside", "form"]):
            tag.decompose()

        # Extract all remaining visible text with newline separators
        text = soup.get_text(separator="\n", strip=True)

        # Remove blank lines to produce clean output
        lines = [l for l in text.splitlines() if l.strip()]
        clean = "\n".join(lines)

        # Truncate to max_chars and append ellipsis if content was cut
        return clean[:max_chars] + ("..." if len(clean) > max_chars else "")

    except Exception as e:
        return f"Failed to read {url}: {e}"

def summarize_findings(findings: str, topic: str) -> str:
    """
    Take all raw findings and produce a clean structured report.
    This is a second LLM call specifically for synthesis.
    """
    # Call the LLM with a dedicated system prompt for structured summarization
    response = client.chat.completions.create(
        model    = "llama-3.3-70b-versatile",
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a research analyst. Given raw research findings, "
                    "produce a clear structured report in markdown format with: "
                    "## Summary, ## Key Findings (bullet points), "
                    "## Notable Sources, ## Conclusion. "
                    "Be factual, cite sources where possible, be concise."
                )
            },
            {
                "role": "user",
                # Pass the topic and raw findings for the LLM to synthesize
                "content": f"Topic: {topic}\n\nFindings:\n{findings}"
            }
        ],
        temperature = 0.3,   # Low temperature for factual, deterministic output
        max_tokens = 1024,
    )
    # Return the generated markdown report content
    return response.choices[0].message.content