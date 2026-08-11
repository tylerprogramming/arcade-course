"""
Module 2 — Build your OWN MCP server / custom tool with Arcade.

Framework: arcade-mcp (the current SDK; GA 2025-10-17, superseded the old TDK).
Install the CLI + SDK once:  uv tool install arcade-mcp

Scaffold a fresh project instead of copying this file:
    arcade new my_server
    cd my_server/src/my_server
    # edit server.py, then:
    uv run server.py            # stdio (default)
    uv run server.py http       # HTTP + SSE, docs at http://127.0.0.1:8000/docs

Deploy it as a hosted MCP server (free tier includes 1):
    arcade login
    arcade deploy -e src/my_server/server.py
Then add it to an MCP Gateway in the dashboard and connect from Claude Code.

This file demonstrates three tool shapes: no-auth, secret-backed, and OAuth.
Verified against docs.arcade.dev (2026-08). Params are typed with
Annotated[type, "description"]; the docstring becomes the tool description;
`context` is injected automatically and hidden from the model.
"""
from typing import Annotated

import httpx
from arcade_mcp_server import Context, MCPApp

app = MCPApp(name="course_tools", version="1.0.0")


# --- 1) No-auth tool: hits a public API. The simplest useful custom tool. ---
@app.tool
async def github_repo_stars(
    repo: Annotated[str, "owner/name, e.g. 'ArcadeAI/arcade-mcp'"],
) -> Annotated[int, "The repository's current star count"]:
    """Return the number of stars a public GitHub repository has."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.github.com/repos/{repo}")
        r.raise_for_status()
        return int(r.json()["stargazers_count"])


# --- 2) Secret-backed tool: reads a key you stored, never hardcoded. ---
# Locally, put NEWS_API_KEY in the .env next to this file. On `arcade deploy`,
# Arcade discovers + uploads declared secrets and manages them server-side.
@app.tool(requires_secrets=["NEWS_API_KEY"])
async def search_news(
    context: Context,
    query: Annotated[str, "What to search the news for"],
) -> Annotated[list[str], "Up to 5 recent headline titles"]:
    """Search recent news headlines for a query, using a stored API key."""
    api_key = context.get_secret("NEWS_API_KEY")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "pageSize": 5, "sortBy": "publishedAt", "apiKey": api_key},
        )
        r.raise_for_status()
        return [a["title"] for a in r.json().get("articles", [])]


# --- 3) OAuth tool: Arcade runs the consent flow and injects the token. ---
# The model/MCP client never sees the token. Built-in providers live in
# arcade_mcp_server.auth (Google, GitHub, Slack, ...). For a provider you
# configured yourself, use OAuth2(id="your-provider-id", scopes=[...]).
from arcade_mcp_server.auth import Google  # noqa: E402


@app.tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/calendar.readonly"]))
async def my_calendar_names(context: Context) -> Annotated[list[str], "Your calendar names"]:
    """List the names of the signed-in user's Google calendars."""
    token = context.get_auth_token_or_empty()
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.googleapis.com/calendar/v3/users/me/calendarList",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return [item["summary"] for item in r.json().get("items", [])]


if __name__ == "__main__":
    # `arcade deploy` requires the entrypoint to call app.run().
    app.run(transport="stdio")
