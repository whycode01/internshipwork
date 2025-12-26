import asyncio

from react_agent import run_agent

if __name__ == "__main__":
    q = input("Question: ").strip()
    ans = asyncio.run(run_agent(q))
    print("\nAnswer:", ans)
