from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.squad import build_orchestrator

load_dotenv()

# Configure logging to show MCP tool calls
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    orchestrator = await build_orchestrator()
    user_id = "user_calc"
    session_id = str(uuid.uuid4())

    print("🤖 FastMCP + AWS Agent Squad (Calc)")
    print("Type a math question (e.g., 'gcd(84,30)', 'sqrt(16) + 3').")
    print("Type 'quit' to exit.\n")

    while True:
        q = input("You: ").strip()
        if q.lower() in {"q", "quit", "exit"}:
            print("Bye!")
            break

        response = await orchestrator.route_request(q, user_id, session_id)
        meta = response.metadata
        print(f"\n[Agent: {meta.agent_name}]")
        try:
            text_blocks = [c.get("text") for c in response.output.content if "text" in c]
            text = "\n".join(tb for tb in text_blocks if tb)
            print(text or "(no text)")
        except Exception:
            print(response.output)
        print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
