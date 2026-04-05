# Web Research Agent

An autonomous AI agent that researches any topic by searching the web, reading full pages, and synthesizing a structured report — without you directing each step. Give it a topic, it decides what to search, what to read, and when it has enough information to write the report.

---

## What makes this different from previous projects

Every previous project was reactive — user asks, agent responds in one shot. This project is autonomous — you give a goal and the agent works toward it across multiple steps with no further input:

```
Project 5 (reactive, tool calling):
  User: "What's the weather in Mumbai?"
  Agent: calls one tool → answers → stops

Project 6 (autonomous, agentic loop):
  User: "Research how large language models work"
  Agent: searches "large language models architecture"
       → searches "how LLMs are trained"
       → reads maxiomtech.com
       → reads wikipedia
       → decides it needs more depth
       → searches "transformer architecture"
       → reads 3 more pages
       → decides it has enough
       → synthesizes structured report
       → stops
```

The agent decides how many steps to take, what to search next, which pages to read, and when it has gathered enough to write the report. You don't direct any of it.

---

## How it works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. You provide a research topic                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Agent loop begins (max 15 steps)                            │
│                                                                 │
│     LLM decides: which tool to call next?                       │
│       → web_search: find relevant URLs and snippets             │
│       → read_page: fetch and parse full page content            │
│       → summarize_findings: signal research is complete         │
│                                                                 │
│     Each tool result goes back into conversation history        │
│     LLM sees all previous searches and reads before deciding    │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Agent calls summarize_findings when ready                   │
│     → second LLM call dedicated to synthesis                    │
│     → produces structured markdown report                      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. Report displayed in terminal + saved as .md file            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Real run — "how large language models actually work"

```
── step 1 ──────────────────────
  searching: large language models architecture
  searching: how large language models are trained
  searching: large language models applications and limitations

── step 2 ──────────────────────
  searching: transformer architecture in large language models
  reading:   maxiomtech.com/large-language-model-architecture
  reading:   aicloudit.com/blog/ai/large-language-model-architecture
  reading:   en.wikipedia.org/wiki/Large_language_model
  reading:   slideshare.net/10-limitations-of-large-language-models

── step 3 ──────────────────────
  searching: large language models applications
  reading:   3 more sources

── step 4 ──────────────────────
  searching: large language models limitations
  reading:   3 more sources
  synthesizing findings...
```

8 searches, 10 page reads, 4 autonomous steps — zero input from the user after the initial topic.

---

## Tech stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| LLM Provider | [Groq](https://groq.com) (free tier) |
| Model | LLaMA 3.3 70B Versatile |
| Web Search | DuckDuckGo via `ddgs` (free, no API key) |
| Page Parsing | BeautifulSoup4 |
| Terminal UI | Rich |

---

## Setup

1. Clone the repo
2. Create and activate a virtual environment
3. Install dependencies: install groq python-dotenv rich requests beautifulsoup4 ddgs
4. Get a Groq API key
5. Create your `.env` file
6. Run the agent, enter the topic. The agent immediately starts working. You'll see each step printed in real time — what it's searching, which pages it's reading, when it starts synthesizing. The final report is displayed in the terminal and saved as a `.md` file in the project folder.
   git init
---

## Tools

**`web_search(query, max_results)`**
Searches DuckDuckGo and returns titles, URLs, and snippets. No API key required. The agent typically runs 2-3 different search queries to cover multiple angles of a topic before reading any pages.

**`read_page(url, max_chars)`**
Fetches a full webpage and strips all HTML, scripts, navigation, and noise using BeautifulSoup. Returns up to 3,000 characters of clean readable text. The agent uses search snippets to decide which URLs are worth reading in full.

**`summarize_findings(findings, topic)`**
The termination tool. When the agent decides it has gathered enough information, it calls this tool with all its raw findings. This triggers a dedicated second LLM call with a research analyst system prompt that produces the final structured markdown report. The agent calling this tool is the signal that research is complete.

---

## Key concepts demonstrated

Agentic loop with termination condition — unlike Project 5 where the loop ran until no more tool calls, this agent runs until it decides to call `summarize_findings`. The agent controls its own stopping condition. This pattern — work autonomously until a goal is reached — is the foundation of every autonomous agent system.

Multi-step autonomous decision making — each step the LLM sees the full history of everything it has searched and read, then decides what to do next. It's not following a fixed plan — it's making fresh decisions based on what it has learned so far.

Two-LLM-call architecture — the research loop uses one LLM call per step for decision making (low temperature, tool focused). The synthesis step uses a completely separate LLM call with a different system prompt optimized for structured writing. Separating these concerns produces much better reports than trying to do both in one call.

Web scraping with noise removal — `read_page` uses BeautifulSoup to remove `<script>`, `<style>`, `<nav>`, `<footer>`, and `<aside>` tags before extracting text. Without this, the raw HTML of most pages is 80% noise. The cleaned text is what actually goes into the LLM context.

Context window management — each page read is capped at 4,000 characters before being added to history. Without this cap, reading 10 pages would overflow the context window. The `max_steps = 15` safety limit prevents infinite loops if the agent gets stuck.

Safety limit pattern — every agentic loop needs a hard stop. The `max_steps` counter ensures the agent never runs indefinitely regardless of what the model decides. This is a standard pattern in all production agent systems.

---

## Limitations

Duplicate URL reads — the agent sometimes re-reads the same URLs across multiple steps. Fixed by tracking `visited_urls` and skipping already-read pages, forcing the agent to explore new sources.

SSL certificate issues on macOS — Python 3.14 installed via Homebrew doesn't automatically link to the system SSL certificate store. Fixed by adding `verify=False` to all `requests.get()` calls and suppressing warnings with `urllib3.disable_warnings()`. This is a dev-only workaround — production deployments handle SSL properly through the deployment environment.

DuckDuckGo rate limiting — aggressive repeated searches can trigger rate limiting. The agent's natural pacing (one step at a time) mostly avoids this, but long sessions may occasionally hit limits.

Report quality depends on source quality — the agent reads whatever DuckDuckGo returns. Low-quality or SEO-spam pages produce weaker reports. Adding domain filtering or a source quality check would improve consistency.
