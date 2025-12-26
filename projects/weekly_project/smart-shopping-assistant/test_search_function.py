#!/usr/bin/env python3
"""
Test script to debug the search function
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.nodes.site_navigator_node import AmazonNavigator, FlipkartNavigator
from workflows.states.workflow_states import WorkflowState

async def test_search_function():
    """Test the search function to see what's going wrong"""
    print("🔍 Testing search function...")
    
    # Create test state
    state = WorkflowState()
    state["search_planning"] = {
        "query": "lunch box",
        "selected_sites": ["amazon.in", "flipkart.com"]
    }
    
    # Test Amazon navigator
    print("\n📦 Testing Amazon navigator...")
    amazon_nav = AmazonNavigator()
    try:
        result = await amazon_nav.navigate_and_search("lunch box", state)
        print(f"Amazon result: {result}")
    except Exception as e:
        print(f"❌ Amazon error: {e}")
    
    # Test Flipkart navigator
    print("\n🛒 Testing Flipkart navigator...")
    flipkart_nav = FlipkartNavigator()
    try:
        result = await flipkart_nav.navigate_and_search("lunch box", state)
        print(f"Flipkart result: {result}")
    except Exception as e:
        print(f"❌ Flipkart error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_function())