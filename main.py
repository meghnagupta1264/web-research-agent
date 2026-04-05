import os
import json
import urllib3
from groq import Groq
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box
from tool_definitions import TOOLS
from tool_implementations import web_search, read_page, summarize_findings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()
client  = Groq(api_key=os.environ.get("GROQ_API_KEY"))
console = Console()

def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    # Map tool names to their corresponding handler lambdas
    registry = {
        "web_search":        lambda: web_search(**tool_args),
        "read_page":         lambda: read_page(**tool_args),
        "summarize_findings": lambda: summarize_findings(**tool_args),
    }
    handler = registry.get(tool_name)
    if handler:
        return handler()
    # Return an error message if the tool name is not recognized
    return f"Unknown tool: {tool_name}"

# ═══════════════════════════════════════════════════════════════
#  RESEARCH AGENT LOOP
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an autonomous web research agent. You MUST always respond by calling one of the available tools. Never respond with plain text during research.

When given a topic:
1. Use web_search to find relevant sources (search 2-3 different queries)
2. Use read_page on the most promising URLs to get full content
3. Search again if you need more detail on specific aspects
4. When you have enough information (after reading at least 3-4 sources),
   call summarize_findings with everything you have learned

Be systematic. Cover multiple angles. Prefer recent sources.
Do not ask the user for clarification — make research decisions autonomously.
Always call a tool. Never respond with plain text until you call summarize_findings."""


def run_research_agent(topic: str) -> str:
    """
    Full autonomous research loop.
    Runs until the agent calls summarize_findings or hits max steps.
    """
    # Initialize conversation history with the user's research request
    history   = [{"role": "user", "content": f"Research this topic thoroughly: {topic}"}]
    step      = 0
    max_steps = 15   # Safety limit — prevents infinite loops

    console.print(f"\n[cyan]Starting research on:[/cyan] {topic}\n")

    visited_urls = set()

    while step < max_steps:
        step += 1
        console.print(f"[dim]── step {step} ──────────────────────[/dim]")

        # Send the full conversation history to the LLM with available tools
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history
            ],
            tools       = TOOLS,
            tool_choice = "required",              # Force the agent to choose a tool if it wants to do anything beyond plain text responses
            temperature = 0.3,
            max_tokens = 1024,
        )

        msg           = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # ── Agent chose to call one or more tools ──
        if finish_reason == "tool_calls" and msg.tool_calls:

            # Append the assistant's tool-call message to history
            history.append({
                "role":       "assistant",
                "content":    msg.content or "",
                "tool_calls": [
                    {
                        "id":       tc.id,
                        "type":     "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in msg.tool_calls
                ]
            })

            # Process each tool call sequentially
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                # show what the agent is doing in real time with rich formatting
                if tool_name == "web_search":
                    console.print(f"  [yellow]searching:[/yellow] {tool_args.get('query')}")
                elif tool_name == "read_page":
                    url = tool_args.get('url')
                    if url in visited_urls:
                        console.print(f"  [dim]skipping (already read): {url[:70]}[/dim]")         # Don't read the same URL twice — if the agent tries, skip and warn it in the next tool call
                        history.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": "Already read this URL. Use a different source.",           # Inform the agent that this URL has already been processed so it can adjust its next action accordingly
                        })
                        continue
                    visited_urls.add(url)
                    console.print(f"  [blue]reading:[/blue]   {url[:70]}...")
                elif tool_name == "summarize_findings":
                    console.print(f"  [green]synthesizing findings...[/green]")

                result = dispatch_tool(tool_name, tool_args)

                # summarize_findings produces the final report — return it immediately
                if tool_name == "summarize_findings":
                    return result

                # Append the tool result to history, capped to avoid context overflow
                history.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      result[:4000],
                })

        # ── Agent produced a plain text response (no tool call) ──
        else:
            final = msg.content or ""
            history.append({"role": "assistant", "content": final})
            return final

    # Fallback message if the agent exhausts all allowed steps
    return "Research agent hit maximum steps. Partial research may be incomplete."

def main():
    # Display a welcome banner with usage instructions
    console.print(Panel(
        "[bold]Web Research Agent[/bold]\n"
        "Give me any topic — I'll search, read, and synthesize a report autonomously.",
        border_style = "cyan",
        box          = box.ROUNDED,
    ))

    while True:
        console.print()
        topic = input("Research topic (or 'quit'): ").strip()

        # Skip empty input
        if not topic:
            continue
        # Exit the loop on quit command
        if topic.lower() == "quit":
            break

        # Run the full autonomous research pipeline
        report = run_research_agent(topic)

        # Display the final markdown report in a styled panel
        console.print("\n")
        console.print(Panel(
            Markdown(report),
            title        = f"[bold]Research Report: {topic}[/bold]",
            border_style = "green",
            box          = box.ROUNDED,
            padding      = (1, 2),
        ))

        # Derive a safe filename from the topic and save the report as markdown
        filename = topic.lower().replace(" ", "_")[:40] + "_report.md"
        with open(filename, "w") as f:
            f.write(f"# Research Report: {topic}\n\n{report}")
        console.print(f"\n[dim]Report saved to {filename}[/dim]")

if __name__ == "__main__":
    main()