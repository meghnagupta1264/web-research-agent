TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information on a topic. "
                "Returns a list of results with titles, URLs, and snippets. "
                "Use this first to find relevant sources before reading them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — be specific for better results"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5, max 10)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": (
                "Fetch and read the full text content of a webpage. "
                "Use this after web_search to get the full content of a promising result. "
                "Pass the URL from search results."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL of the page to read"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default 3000)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_findings",
            "description": (
                "Call this when you have gathered enough information and are ready "
                "to produce the final research report. Pass all your findings as a string."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "findings": {
                        "type": "string",
                        "description": "All research findings gathered so far"
                    },
                    "topic": {
                        "type": "string",
                        "description": "The original research topic"
                    }
                },
                "required": ["findings", "topic"]
            }
        }
    }
]