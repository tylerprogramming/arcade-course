"""
Module 3 — Drive Arcade tools from a LangChain / LangGraph agent, with Claude.

IMPORTANT (verified 2026-08): the old `langchain-arcade` package is DEPRECATED.
The current pattern loads tools via the Arcade SDK (`arcadepy.AsyncArcade`),
wraps each as a LangChain `StructuredTool`, and runs them inside a LangChain 1.0
agent (`create_agent`). Per-user authorization is handled with
`tools.authorize` -> LangGraph `interrupt` -> `auth.wait_for_completion`.

Install:  pip install arcadepy langchain langchain-anthropic langgraph python-dotenv
Env:      ARCADE_API_KEY, ARCADE_USER_ID, ANTHROPIC_API_KEY

Wiring is from docs.arcade.dev (use-arcade-tools, last updated 2026-07-27),
adapted only to use Anthropic Claude (claude-opus-4-8) instead of OpenAI.
"""
import asyncio
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from arcadepy import AsyncArcade
from arcadepy.types import ToolDefinition
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field, create_model

load_dotenv()

ARCADE_USER_ID = os.getenv("ARCADE_USER_ID")
MCP_SERVERS: List[str] = ["Slack"]                                   # e.g. ["Slack"] for a whole toolkit
TOOLS = ["Gmail_ListEmails", "Gmail_SendEmail", "Gmail_WhoAmI"]
SYSTEM_PROMPT = "You are a helpful assistant that can use Gmail and Slack tools."

TYPE_MAPPING = {"string": str, "number": float, "integer": int, "boolean": bool, "array": list, "json": dict}


def build_model():
    """Pick the chat model from env. LLM_PROVIDER=openai (default) or anthropic.
    The agent is model-agnostic, so swapping providers changes nothing else."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),
                             api_key=os.getenv("ANTHROPIC_API_KEY"))
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
                      api_key=os.getenv("OPENAI_API_KEY"))


def get_python_type(val_type: str) -> Any:
    t = TYPE_MAPPING.get(val_type)
    if t is None:
        raise ValueError(f"Invalid value type: {val_type}")
    return t


def arcade_schema_to_pydantic(tool_def: ToolDefinition) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for param in tool_def.input.parameters or []:
        param_type = get_python_type(param.value_schema.val_type)
        if param_type is list and param.value_schema.inner_val_type:
            inner_type = get_python_type(param.value_schema.inner_val_type)
            param_type = list[inner_type]
        default = ... if param.required else None
        fields[param.name] = (param_type, Field(default=default, description=param.description or "No description provided."))
    return create_model(f"{tool_def.name}Args", **fields)


async def arcade_to_langchain(client: AsyncArcade, tool: ToolDefinition) -> StructuredTool:
    args_schema = arcade_schema_to_pydantic(tool)

    async def tool_function(config: RunnableConfig, **kwargs: Any) -> Any:
        user_id = config.get("configurable", {}).get("user_id") if config else None
        if not user_id:
            raise ValueError("User ID is required to execute Arcade tools")

        # per-user authorization
        auth = await client.tools.authorize(tool_name=tool.qualified_name, user_id=user_id)
        if auth.status != "completed":
            result = interrupt({
                "type": "authorization_required",
                "tool_name": tool.qualified_name,
                "auth_response": {"id": auth.id, "url": auth.url},
            })
            if not result.get("authorized"):
                raise RuntimeError(f"Authorization was not completed for {tool.name}")

        # execute
        filtered = {k: v for k, v in kwargs.items() if v is not None and v != ""}
        resp = await client.tools.execute(tool_name=tool.qualified_name, input=filtered, user_id=user_id)
        if resp.output and resp.output.value:
            return resp.output.value
        return {"error": getattr(getattr(resp.output, "error", None), "message", "Unknown error"),
                "tool": tool.qualified_name}

    return StructuredTool.from_function(
        coroutine=tool_function,
        name=tool.qualified_name.replace(".", "_"),
        description=tool.description,
        args_schema=args_schema,
    )


async def get_arcade_tools(client: AsyncArcade, tools=None, mcp_servers=None) -> List[StructuredTool]:
    defs: dict[str, ToolDefinition] = {}
    if tools:
        for r in await asyncio.gather(*[client.tools.get(name=t) for t in tools]):
            defs[r.fully_qualified_name] = r
    if mcp_servers:
        for r in await asyncio.gather(*[client.tools.list(toolkit=s, limit=30) for s in mcp_servers]):
            for t in r.items:
                defs[t.fully_qualified_name] = t
    return await asyncio.gather(*[arcade_to_langchain(client, d) for d in defs.values()])


async def handle_auth(interrupt_value: Dict[str, Any], client: AsyncArcade) -> Dict[str, bool]:
    auth = interrupt_value.get("auth_response", {})
    print(f"\nAuthorize {interrupt_value.get('tool_name')} here:\n  {auth.get('url')}\nWaiting...")
    status = await client.auth.wait_for_completion(auth.get("id"))
    ok = status.status == "completed"
    print("Authorization completed." if ok else f"Authorization failed: {status.status}")
    return {"authorized": ok}


async def stream(agent, input_data, config) -> List[Any]:
    interrupts = []
    async for chunk in agent.astream(input_data, config, stream_mode="updates"):
        if "__interrupt__" in chunk:
            interrupts.extend(chunk["__interrupt__"])
        for node, out in chunk.items():
            if node == "__interrupt__":
                continue
            for msg in out.get("messages", []):
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"Calling tool: {tc['name']}")
                elif isinstance(msg, ToolMessage):
                    print(f"   {msg.name} completed")
                elif isinstance(msg, AIMessage) and msg.content:
                    print(f"\nAssistant:\n{msg.content}")
    return interrupts


async def main():
    client = AsyncArcade()  # reads ARCADE_API_KEY
    tools = await get_arcade_tools(client, tools=TOOLS, mcp_servers=MCP_SERVERS or None)
    model = build_model()
    agent = create_agent(system_prompt=SYSTEM_PROMPT, model=model, tools=tools, checkpointer=MemorySaver())

    print(f"\nAgent ready with {len(tools)} tools. Type 'quit' to exit.")
    config = {"configurable": {"thread_id": "t1", "user_id": ARCADE_USER_ID}}

    while True:
        try:
            msg = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in ("quit", "exit", "q"):
            break
        current = {"messages": [{"role": "user", "content": msg}]}
        while True:
            interrupts = await stream(agent, current, config)
            if not interrupts:
                break
            for it in interrupts:
                if it.value.get("type") == "authorization_required":
                    current = Command(resume=await handle_auth(it.value, client))
                    break
            else:
                break


if __name__ == "__main__":
    asyncio.run(main())
