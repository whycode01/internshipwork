# tools.py
import ast
import json
import operator as op
from typing import List

import httpx
from duckduckgo_search import DDGS
from pydantic import BaseModel


class ToolSpec(BaseModel):
    name: str
    description: str
    arg_schema: dict  # renamed from `schema` to avoid BaseModel.schema() shadowing

def tool_catalog() -> List[ToolSpec]:
    return [
        ToolSpec(
            name="web_search",
            description="Search the web and return the top result snippet.",
            arg_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
        ToolSpec(
            name="get_url",
            description="Fetch raw text content from a URL.",
            arg_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        ),
        ToolSpec(
            name="calculator",
            description="Evaluate a safe arithmetic expression.",
            arg_schema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        ),
    ]  # Define the available tools and their JSON arg schemas in one place for the ReAct prompt and validation. [web:3][web:5]

def render_tool_descriptions() -> str:
    parts = []
    for t in tool_catalog():
        parts.append(f"- {t.name}: {t.description}. args={json.dumps(t.arg_schema)}")
    return "\n".join(parts)  # This string is injected into the ReAct system prompt so the model knows valid tools and arguments. [web:5]

async def run_tool(name: str, args: dict) -> str:
    """
    Execute a tool by name with validated args.
    Returns a short text observation string (truncated where needed).
    """
    name = (name or "").strip()
    args = args or {}
    if name == "web_search":
        q = args.get("query", "").strip()
        if not q:
            return "Error: query required."
        try:
            # duckduckgo_search is synchronous; keep it simple inside the async function
            with DDGS() as ddg:
                results = ddg.text(q, max_results=5)
            if not results:
                return "No results."
            top = results[0]
            title = top.get("title")
            href = top.get("href")
            snippet = top.get("body")
            # Keep observation compact to fit ReAct scratchpad nicely
            return f"title: {title}\nhref: {href}\nsnippet: {snippet}"
        except Exception as e:
            return f"Search error: {e}"  # Ensure the agent sees an Observation even on failure. [web:3]

    if name == "get_url":
        url = args.get("url", "").strip()
        if not url:
            return "Error: url required."
        try:
            # Reasonable connect/read timeouts for local and remote URLs
            timeout = httpx.Timeout(connect=10.0, read=10.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                r = await client.get(url)
                # Basic content-type guard; still return text for HTML-like responses
                text = r.text
            return text[:4000]  # Truncate to avoid inflating the scratchpad. [web:5]
        except Exception as e:
            return f"Fetch error: {e}"

    if name == "calculator":
        expr = args.get("expression", "").strip()
        if not expr:
            return "Error: expression required."
        # Very small, safe evaluator for + - * / ** and parentheses; disallows names/calls.
        allowed = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.USub: op.neg,
        }
        def eval_(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.Num):
                return node.n
            if isinstance(node, ast.UnaryOp) and type(node.op) in allowed:
                return allowed[type(node.op)](eval_(node.operand))
            if isinstance(node, ast.BinOp) and type(node.op) in allowed:
                return allowed[type(node.op)](eval_(node.left), eval_(node.right))
            if isinstance(node, ast.Expression):
                return eval_(node.body)
            raise ValueError("Unsupported expression")
        try:
            parsed = ast.parse(expr, mode="eval")
            result = eval_(parsed)
            return str(result)
        except Exception as e:
            return f"Calc error: {e}"

    return f"Unknown tool: {name}"  # Let the agent recover if it hallucinated a tool name. [web:3]
