import asyncio
import json
import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from groq import Groq

from prompts import REACT_FEWSHOT, SYSTEM_PROMPT
from tools import render_tool_descriptions, run_tool, tool_catalog

load_dotenv()

MODEL = "llama-3.3-70b-versatile"  # choose Groq model
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ACTION_RE = re.compile(r"^Action:\s*(\w+)\s*$", re.IGNORECASE)
INPUT_RE = re.compile(r"^Action Input:\s*(\{.*\})\s*$", re.IGNORECASE)
FINAL_RE = re.compile(r"^Final Answer:\s*(.*)$", re.IGNORECASE)

def build_messages(question: str, scratchpad: str) -> List[Dict[str,str]]:
    tools_desc = render_tool_descriptions()
    tool_names = ",".join(t.name for t in tool_catalog())
    system = SYSTEM_PROMPT.format(tool_names=tool_names)
    user = f"{REACT_FEWSHOT}\n\nTools:\n{tools_desc}\n\nQuestion: {question}\n{scratchpad}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

async def step(question: str, scratchpad: str) -> str:
    msgs = build_messages(question, scratchpad)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=msgs,
        temperature=0.2,
        max_completion_tokens=512,
    )
    return resp.choices.message.content

async def run_agent(question: str, max_iters: int = 8):
    scratchpad = ""
    for _ in range(max_iters):
        out = await step(question, scratchpad)
        scratchpad += ("" if scratchpad.endswith("\n") else "\n") + out.strip() + "\n"
        for line in out.splitlines():
            m = FINAL_RE.match(line.strip())
            if m:
                return m.group(1).strip()
        action_name, action_args = None, None
        for line in out.splitlines():
            ma = ACTION_RE.match(line.strip())
            mi = INPUT_RE.match(line.strip())
            if ma: action_name = ma.group(1)
            if mi:
                try:
                    action_args = json.loads(mi.group(1))
                except Exception:
                    action_args = {}
        if not action_name:
            scratchpad += "Observation: Missing action. Please continue.\n"
            continue
        obs = await run_tool(action_name, action_args or {})
        scratchpad += f"Observation: {obs}\n"
    return "Max iterations reached. No final answer."
