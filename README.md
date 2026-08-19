# Build AI Agents in 2026 — Course Code

Companion code for the video **"How to Build AI Agents in 2026 (The Right Way)"** — connect AI to your real apps and build agents that actually do things, without the auth headaches.

> **The one idea:** you connect your accounts **once** through [Arcade](https://arcade.dev), and the same connected tools work **everywhere** — in Claude Code, in the Claude Desktop app, on the web, in your own Python, inside LangChain or CrewAI, and in an agent that runs on a schedule on a server. You never store a password or an auth token.

**Heads up (2026):** most tutorials for this are already outdated. The old `langchain-arcade` and `crewai-arcade` packages are **deprecated** — both frameworks now just wrap the Arcade SDK (`arcadepy`). This repo uses the current, working way, verified against Arcade's live docs.

## What you build

| # | Folder | What |
|---|---|---|
| 1 | [`01-claude-code/`](01-claude-code/) | Connect your apps to Claude Code (a gateway + one `claude mcp add`). |
| 2 | [`02-custom-tool/`](02-custom-tool/) | Build and deploy your **own** custom MCP server with `arcade-mcp`. |
| 3 | [`03-langchain/`](03-langchain/) | The same tools in a **LangChain / LangGraph** agent (`email_agent.py`, then `email_slack_agent.py` — adding Slack is one line). |
| 4 | [`04-crewai/`](04-crewai/) | The same tools in a **CrewAI** crew. |
| 5 | [`05-scheduled-agent/`](05-scheduled-agent/) | The **Morning Planner**: reads your ClickUp tasks + calendar, plans your day, and writes the time-blocks back. |
| — | [`deploy/`](deploy/) | Run the planner 24/7 on a VPS (cron / systemd). |

New here? Start with **[`INSTALL.md`](INSTALL.md)** — a 10-minute, copy-paste setup.

## Setup (uv)

Deps live in `pyproject.toml`, locked in `uv.lock`, on **Python 3.12** (pinned in `.python-version`). uv installs that Python for you, into its own managed dir — it never touches your system Python.

1. **Get the code**:
   ```
   git clone https://github.com/tylerprogramming/arcade-course.git
   cd arcade-course
   ```
2. **Install uv** once: `brew install uv` (or `pip3 install uv`, or the installer at https://docs.astral.sh/uv).
3. **Install everything** (uv fetches Python 3.12 automatically):
   ```
   uv sync
   ```
4. **Install the custom-server CLI** for module 2:
   ```
   uv tool install arcade-mcp
   ```
5. **Add your keys**: copy `.env.example` to `.env` and fill it in. **Never commit `.env`** (it's gitignored).
   ```
   cp .env.example .env
   ```
6. **Run** anything through uv — no manual activate needed:
   ```
   uv run 03-langchain/email_agent.py
   uv run 04-crewai/main.py
   uv run 05-scheduled-agent/morning_planner.py --discover
   uv run 05-scheduled-agent/morning_planner.py          # dry run (writes nothing)
   uv run 05-scheduled-agent/morning_planner.py --apply  # creates the calendar blocks
   ```

> **pip fallback:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (needs Python 3.11+ installed yourself).

## Choose your model (OpenAI or Claude)

The agents are model-agnostic. In `.env`, set `LLM_PROVIDER=openai` (default) or `anthropic` — the tools don't change either way.

## Accounts you'll need (free to start)
- **Arcade** — API key (https://api.arcade.dev)
- **An LLM key** — OpenAI (https://platform.openai.com) *or* Anthropic (https://console.anthropic.com)
- **Google** (Gmail + Calendar), **ClickUp** (for the planner)
- Optional: **Slack** (only for `03-langchain/email_slack_agent.py`)
- Optional: a **VPS** to run the planner 24/7

## Safety baked in
- Anything that **writes** (calendar events, emails) runs in **draft / safe mode**, or into a **wipeable calendar**, until you trust it.
- **No tokens in code.** Arcade holds the per-user OAuth; your `.env` only holds API keys, and `.env` is gitignored.

---

Built with [Claude Code](https://claude.com/claude-code) + [Arcade](https://arcade.dev). Code by Tyler Reed ([@TylerReedAI](https://youtube.com/@TylerReedAI)).
