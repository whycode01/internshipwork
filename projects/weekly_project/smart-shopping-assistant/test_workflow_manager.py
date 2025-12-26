#!/usr/bin/env python3
"""
Test script to debug the workflow manager specifically
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
from utils.price_tracker import PriceTracker
from workflows.workflow_manager import WorkflowManager

async def test_workflow_manager():
    """Test the workflow manager like the Streamlit app does"""
    print("🔧 Testing workflow manager...")
    
    # Initialize database and price tracker like main.py
    db = Database()
    price_tracker = PriceTracker(db)
    
    # Initialize workflow manager like dashboard.py
    try:
        workflow_manager = WorkflowManager(db, price_tracker)
        print("✅ Workflow manager created successfully")
        
        # Test search like dashboard does
        print("\n🔍 Testing search_product_workflow...")
        result = await workflow_manager.search_product_workflow(
            product_name="lunch box",
            websites=["amazon.in", "flipkart.com"]
        )
        
        print(f"📊 Result success: {result.get('success', False)}")
        print(f"📊 Result status: {result.get('workflow_status', 'unknown')}")
        print(f"📊 Products found: {len(result.get('products', []))}")
        print(f"📊 Error: {result.get('error', 'none')}")
        
        if result.get('products'):
            print("\n📦 Products found:")
            for i, product in enumerate(result.get('products', [])[:3]):  # Show first 3
                print(f"  {i+1}. {product.get('name', 'Unknown')} - {product.get('price', 'N/A')} - {product.get('site', 'Unknown site')}")
        
    except Exception as e:
        print(f"❌ Workflow manager error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_manager())