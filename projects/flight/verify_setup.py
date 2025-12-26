"""Test script to verify LangGraph Studio setup."""

import os
import sys
from pathlib import Path


def check_langgraph_json():
    """Check if langgraph.json exists and is valid."""
    print("1. Checking langgraph.json...")
    
    if not os.path.exists("langgraph.json"):
        print("   [ERROR] langgraph.json not found!")
        return False
    
    import json
    try:
        with open("langgraph.json", "r") as f:
            config = json.load(f)
        
        if "graphs" not in config:
            print("   [ERROR] 'graphs' key missing in langgraph.json")
            return False
        
        if "agent" not in config["graphs"]:
            print("   [ERROR] 'agent' graph not defined")
            return False
        
        print("   [OK] langgraph.json is valid")
        print(f"   Graph entry point: {config['graphs']['agent']}")
        return True
    except Exception as e:
        print(f"   [ERROR] Failed to parse langgraph.json: {e}")
        return False


def check_env_file():
    """Check if .env file exists with required keys."""
    print("\n2. Checking .env file...")
    
    if not os.path.exists(".env"):
        print("   [ERROR] .env file not found!")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    
    if not groq_key:
        print("   [ERROR] GROQ_API_KEY not found in .env")
        return False
    
    print("   [OK] GROQ_API_KEY found")
    
    if not langsmith_key or langsmith_key == "your_langsmith_api_key_here":
        print("   [WARNING] LANGSMITH_API_KEY not set (optional for LangGraph Studio)")
        print("   Get it from: https://smith.langchain.com/ > Settings > API Keys")
    else:
        print("   [OK] LANGSMITH_API_KEY found")
    
    return True


def check_graph_function():
    """Check if create_graph function exists."""
    print("\n3. Checking create_graph function...")
    
    try:
        from flight_agent import create_graph
        print("   [OK] create_graph function found")
        
        # Try to create the graph
        graph = create_graph()
        print("   [OK] Graph compiled successfully")
        
        return True
    except ImportError as e:
        print(f"   [ERROR] Could not import create_graph: {e}")
        return False
    except Exception as e:
        print(f"   [ERROR] Failed to create graph: {e}")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    print("\n4. Checking dependencies...")
    
    required = [
        "langgraph",
        "langchain_groq",
        "browser_use",
        "dotenv",
        "pydantic"
    ]
    
    missing = []
    for package in required:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"   [OK] {package}")
        except ImportError:
            print(f"   [ERROR] {package} not installed")
            missing.append(package)
    
    if missing:
        print(f"\n   Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def check_langgraph_cli():
    """Check if langgraph CLI is installed."""
    print("\n5. Checking LangGraph CLI...")
    
    import subprocess
    try:
        result = subprocess.run(
            ["langgraph", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   [OK] LangGraph CLI installed: {result.stdout.strip()}")
            return True
        else:
            print("   [ERROR] LangGraph CLI not working properly")
            return False
    except FileNotFoundError:
        print("   [ERROR] LangGraph CLI not installed")
        print("   Install with: pip install langgraph-cli")
        return False


def print_summary(results):
    """Print summary of checks."""
    print("\n" + "="*60)
    print("SETUP VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check}")
    
    print("="*60)
    
    if all_passed:
        print("\nAll checks passed! You can now run:")
        print("\n  langgraph dev")
        print("\nThen open: http://localhost:8123")
    else:
        print("\nSome checks failed. Please fix the issues above.")
    
    print("\n")


def main():
    """Run all checks."""
    print("="*60)
    print("LANGGRAPH STUDIO SETUP VERIFICATION")
    print("="*60)
    print()
    
    results = {
        "langgraph.json": check_langgraph_json(),
        ".env file": check_env_file(),
        "create_graph function": check_graph_function(),
        "Dependencies": check_dependencies(),
        "LangGraph CLI": check_langgraph_cli()
    }
    
    print_summary(results)


if __name__ == "__main__":
    main()
