"""
Module 4 — Drive the SAME Arcade tools from a CrewAI crew, with Claude.

IMPORTANT (verified 2026-08): the `crewai-arcade` package is DEPRECATED. The
current pattern (from docs.arcade.dev/en/home/crewai/use-arcade-tools, last
updated 2026-07-27) is to install plain CrewAI + the Arcade SDK and paste the
ArcadeTool wrapper below into your project. Note how similar this is to the
LangChain module: both frameworks just wrap arcadepy's authorize/execute.

Install:  pip install 'crewai[tools]' arcadepy python-dotenv
Env:      ARCADE_API_KEY, ARCADE_USER_ID, ANTHROPIC_API_KEY

The Arcade wiring (ArcadeTool, get_arcade_tools, _auth_tool, _run) is verbatim
from the Arcade docs. The LLM block + Crew/Task runner use Claude via CrewAI's
native LLM class (model string "anthropic/<id>", max_tokens required).
"""
import os
from typing import Any

from arcadepy import Arcade
from arcadepy.types import ToolDefinition
from crewai import Agent, Crew, LLM, Task
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field, create_model

load_dotenv()

ARCADE_USER_ID = os.getenv("ARCADE_USER_ID")
MCP_SERVERS: list[str] = []                       # e.g. ["Slack"] for a whole toolkit
TOOLS = ["Gmail_ListEmails", "Gmail_WhoAmI"]

TYPE_MAP: dict[str, type] = {"string": str, "number": float, "integer": int, "boolean": bool, "array": list, "json": dict}


def _python_type(val_type: str) -> type:
    t = TYPE_MAP.get(val_type)
    if t is None:
        raise ValueError(f"Unsupported Arcade value type: {val_type}")
    return t


def _build_args_model(tool_def: ToolDefinition) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for param in tool_def.input.parameters or []:
        param_type = _python_type(param.value_schema.val_type)
        if param_type is list and param.value_schema.inner_val_type:
            inner = _python_type(param.value_schema.inner_val_type)
            param_type = list[inner]
        default = ... if param.required else None
        fields[param.name] = (param_type, Field(default=default, description=param.description or ""))
    return create_model(f"{tool_def.name}Input", **fields)


class ArcadeTool(BaseTool):
    """A CrewAI tool backed by an Arcade tool definition."""
    name: str
    description: str
    args_schema: type[BaseModel]
    arcade_tool_name: str = ""
    user_id: str = ""
    _client: Arcade | None = None

    def _auth_tool(self):
        auth = self._client.tools.authorize(tool_name=self.arcade_tool_name, user_id=self.user_id)
        if auth.status != "completed":
            print(f"Authorization required. Visit: {auth.url}")
            self._client.auth.wait_for_completion(auth)

    def _run(self, **kwargs: Any) -> str:
        if self._client is None:
            self._client = Arcade()
        self._auth_tool()
        print(f"Calling {self.arcade_tool_name}...")
        clean = {k: v for k, v in kwargs.items() if v is not None and v != ""}
        result = self._client.tools.execute(tool_name=self.arcade_tool_name, input=clean, user_id=self.user_id)
        out = result.output
        if getattr(out, "error", None):
            return f"Tool error: {getattr(out.error, 'message', out.error)}"
        return str(out.value)


def get_arcade_tools(client: Arcade, *, tools=None, mcp_servers=None, user_id: str = "") -> list[ArcadeTool]:
    if not tools and not mcp_servers:
        raise ValueError("Provide at least one tool name or toolkit name")
    definitions: list[ToolDefinition] = []
    if tools:
        definitions.extend(client.tools.get(name=n) for n in tools)
    if mcp_servers:
        for tk in mcp_servers:
            definitions.extend(client.tools.list(toolkit=tk).items)
    return [
        ArcadeTool(
            client=client,
            name=d.qualified_name.replace(".", "_"),
            description=d.description,
            args_schema=_build_args_model(d),
            arcade_tool_name=d.qualified_name,
            user_id=user_id,
        )
        for d in definitions
    ]


def build_llm() -> LLM:
    """Pick the LLM from env. LLM_PROVIDER=openai (default) or anthropic.
    CrewAI's native LLM takes a '<provider>/<model>' string; Anthropic needs max_tokens."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        return LLM(model=f"anthropic/{os.getenv('ANTHROPIC_MODEL', 'claude-opus-4-8')}", max_tokens=4096)
    return LLM(model=f"openai/{os.getenv('OPENAI_MODEL', 'gpt-5.4-mini')}")


def main():
    client = Arcade()  # reads ARCADE_API_KEY
    arcade_tools = get_arcade_tools(client, tools=TOOLS, mcp_servers=MCP_SERVERS or None, user_id=ARCADE_USER_ID)

    llm = build_llm()  # openai by default; set LLM_PROVIDER=anthropic to use Claude

    agent = Agent(
        role="Communication Manager",
        goal="Help the user with their Gmail requests",
        backstory="You are a helpful assistant that can use Gmail.",
        tools=arcade_tools,
        llm=llm,
    )
    task = Task(
        description="Look up who I am in Gmail and list the subjects of my 3 most recent emails.",
        expected_output="My email address and a bullet list of 3 recent subject lines.",
        agent=agent,
    )
    result = Crew(agents=[agent], tasks=[task]).kickoff()
    print(result.raw)


if __name__ == "__main__":
    main()
