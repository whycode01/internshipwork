import asyncio
import json
import os
import re
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv
from groq import Groq
from langfuse import Langfuse, get_client

from prompts import REACT_FEWSHOT, SYSTEM_PROMPT
from tools import render_tool_descriptions, run_tool, tool_catalog

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
langfuse: Langfuse = get_client()
assert langfuse.auth_check(), "Langfuse auth failed. Check LANGFUSE_* env vars."

ACTION_RE = re.compile(r"^Action:\s*(\w+)\s*$", re.IGNORECASE)
INPUT_RE = re.compile(r"^Action Input:\s*(\{.*\})\s*$", re.IGNORECASE)
FINAL_RE = re.compile(r"^Final Answer:\s*(.*)$", re.IGNORECASE)

def build_messages(question: str, scratchpad: str) -> List[Dict[str,str]]:
    tools_desc = render_tool_descriptions()
    system = SYSTEM_PROMPT.format(tool_names=",".join(t.name for t in tool_catalog()))
    user = f"{REACT_FEWSHOT}\n\nTools:\n{tools_desc}\n\nQuestion: {question}\n{scratchpad}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

async def llm_call(messages: List[Dict[str,str]]):
    t0 = time.time()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        max_completion_tokens=512,
    )
    latency_ms = int((time.time() - t0) * 1000)
    content = resp.choices[0].message.content
    usage = getattr(resp, "usage", None)
    return content, latency_ms, usage

async def run_agent_traced(question: str, user_id: Optional[str] = None, session_id: Optional[str] = None, max_iters: int = 8):
    with langfuse.start_as_current_span(name="react-agent") as trace_span:
        trace_span.update(
            user_id=user_id,
            session_id=session_id,
            tags=["react", "groq", "custom"],
            input={"question": question},
        )

        scratchpad = ""
        for step_idx in range(max_iters):
            messages = build_messages(question, scratchpad)

            with langfuse.start_as_current_span(name="llm.chat") as llm_span:
                llm_span.create_event(name="llm.request", input={"messages": messages, "model": MODEL})
                content, latency_ms, usage = await llm_call(messages)
                llm_span.create_event(name="llm.response", output={"content": content, "usage": usage})
                llm_span.update(attributes={"llm.model": MODEL, "latency.ms": latency_ms})

            langfuse.create_event(name="agent.step.output", input={"step": step_idx, "raw": content})

            scratchpad += ("" if scratchpad.endswith("\n") else "\n") + content.strip() + "\n"

            # Check Final Answer
            for line in content.splitlines():
                m = FINAL_RE.match(line.strip())
                if m:
                    final = m.group(1).strip()
                    trace_span.update(output={"final_answer": final})
                    return final

            # Parse action + args
            action_name, action_args = None, None
            for line in content.splitlines():
                ma = ACTION_RE.match(line.strip()); mi = INPUT_RE.match(line.strip())
                if ma: action_name = ma.group(1)
                if mi:
                    try:
                        action_args = json.loads(mi.group(1))
                    except Exception:
                        action_args = {}

            with langfuse.start_as_current_span(name="tool.call") as tool_span:
                tool_span.update(attributes={"tool.name": action_name or "missing"})
                tool_span.create_event(name="tool.input", input={"args": action_args})
                if not action_name:
                    observation = "Missing action. Please continue."
                else:
                    observation = await run_tool(action_name, action_args or {})
                tool_span.create_event(name="tool.output", output={"observation": observation})

            scratchpad += f"Observation: {observation}\n"

        trace_span.update(output={"final_answer": "Max iterations reached."}, tags=["max-iters"])
        return "Max iterations reached. No final answer."
