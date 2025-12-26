import asyncio
import os

from react_agent_traced import run_agent_traced

if __name__ == "__main__":
    question = input("Question: ").strip()
    # Optionally propagate user/session for analytics
    user_id = os.getenv("USER_ID") or "user-001"
    session_id = os.getenv("SESSION_ID") or "sess-001"
    ans = asyncio.run(run_agent_traced(question, user_id=user_id, session_id=session_id))
    print("\nAnswer:", ans)
