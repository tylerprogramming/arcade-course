# Install the Agents — Setup Pack

Follow this and you'll have working AI agents connected to your real accounts, no
auth headaches. Takes about 10 minutes. Every step is copy-paste.

> The whole idea: you connect your accounts **once** through Arcade, and the same
> connection works in Claude Code, in Python agents (LangChain / CrewAI), and in a
> scheduled agent on a server. You never store a password or a token.

## What you'll have at the end
- Your apps connected to **Claude Code**
- Your **own** custom tool, deployed as a live MCP server
- The same tools running in a **LangChain** agent and a **CrewAI** crew
- A **Morning Planner** that reads your tasks + calendar and blocks your day, on a schedule

## What you need (free to start)
- **Arcade** account + API key — https://api.arcade.dev (Dashboard → API Keys)
- **An LLM key** — OpenAI (https://platform.openai.com) or Anthropic (https://console.anthropic.com)
- A **Google** account (Gmail + Calendar)
- A **ClickUp** account (only for the Morning Planner)
- Optional: a **Hostinger VPS** (to run the planner 24/7)

---

## 1. Install uv (the Python tool)
```
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# or, if you have Homebrew:  brew install uv
# or, if you have pip:       pip3 install uv
```

## 2. Get the code
Clone this repo and open a terminal inside it:
```
git clone https://github.com/tylerprogramming/arcade-course.git
cd arcade-course
```
(Run every command below from this folder.)

## 3. Install everything
```
uv sync
```
This creates a private environment and installs the deps. **uv even fetches the
right Python (3.12) for you** — you don't need to install Python yourself.

## 4. Install the custom-server tool (for building your own tool)
```
uv tool install arcade-mcp
```

## 5. Add your keys
```
cp .env.example .env
```
Open `.env` and fill in `ARCADE_API_KEY`, your `OPENAI_API_KEY` (or set
`LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`), and `ARCADE_USER_ID` (your email).
**Never share `.env`** — it's ignored by git on purpose.

## 6. Connect your apps (once)
1. Arcade Dashboard → **MCP Gateways** → **Create MCP Gateway**
2. Give it a **slug**, add tools: **Gmail**, **Google Calendar** (and **ClickUp** for the planner)
3. Copy the URL — it looks like `https://api.arcade.dev/mcp/<your-slug>`
4. Add it to Claude Code:
   ```
   claude mcp add arcade --transport http "https://api.arcade.dev/mcp/<your-slug>"
   claude mcp list
   ```
The first time an agent uses a tool, Arcade pops the real Google/ClickUp consent
screen. Approve once. That's the only auth you ever do.

## 7. Run the agents
```
# LangChain agent (chat that can use your Gmail):
uv run 03-langchain/email_agent.py

# CrewAI crew (same tools, different framework):
uv run 04-crewai/main.py

# Morning Planner — first, see your real tool names:
uv run 05-scheduled-agent/morning_planner.py --discover
# then a safe dry run (prints the plan, writes nothing):
uv run 05-scheduled-agent/morning_planner.py
# when you're happy, let it write the blocks:
uv run 05-scheduled-agent/morning_planner.py --apply
```

## 8. Run it on a schedule (optional)
See `deploy/README.md` for cron (local) and a Hostinger VPS (always-on) so the
planner runs every morning before you sit down.

---

## Troubleshooting
- **"command not found: uv"** → restart your terminal, or use the full path uv printed on install.
- **A tool asks you to authorize every run** → make sure `ARCADE_USER_ID` is the same each time.
- **Planner can't find a task/calendar tool** → run with `--discover` and set the tool names it prints.
- **Wrong Python** → `uv` handles it; you don't need Python 3.12 installed system-wide.
- **Model errors** → check `LLM_PROVIDER` matches the key you filled in (`openai` vs `anthropic`).

Safety: anything that writes (calendar, email) starts in draft/safe mode or a
wipeable "AI Plan" calendar. Trust it first, then loosen the leash.
