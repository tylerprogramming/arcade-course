# Module 1 — Connect your apps to Claude Code (Arcade gateway)

The baseline: use Arcade's prebuilt tools inside Claude Code. This is the 045/046
setup, recapped fast. No code — a gateway plus one command.

## 1. Build a gateway (dashboard)

1. Go to **https://api.arcade.dev/dashboard/mcp-gateways**
2. **Create MCP Gateway** → set a **Name** and a **Slug** (the slug becomes the URL)
3. Pick the tools/MCP servers to include (for the course: **Gmail**, **Google Calendar**, and later **ClickUp**)
4. Auth mode: **Arcade Auth** ("members of this project") is fine for your own use; **User Source (OIDC)** for production
5. Save → copy the generated URL. It looks like:

```
https://api.arcade.dev/mcp/<your-gateway-slug>
```

## 2. Add it to Claude Code (one command)

```bash
claude mcp add arcade --transport http "https://api.arcade.dev/mcp/<your-gateway-slug>"
claude mcp list          # verify "arcade" is connected
claude mcp get arcade    # details
```

## 3. Use it

Ask Claude Code something that needs a tool, e.g. *"list my Google calendars"* or
*"what unread emails came in today."* The **first** time it touches a tool, Arcade
pops the real Google consent screen — approve once. Arcade stores + refreshes the
token; you never paste one, and it's not in any file.

> That first-use OAuth is the whole point of Arcade: you connected a real account
> to Claude Code without building or storing any auth. Same gateway URL also works
> in Cursor, VS Code, and any MCP client.

Next → `../02-custom-tool/` to build your OWN tool and add it to a gateway like this one.
