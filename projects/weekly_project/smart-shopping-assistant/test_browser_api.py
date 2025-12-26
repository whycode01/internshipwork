#!/usr/bin/env python3
"""
Test script to understand browser-use API
"""

import asyncio
from browser_use import Browser

async def test_browser_api():
    browser = None
    try:
        browser = Browser()
        print("✅ Browser created successfully")
        
        # Get browser context
        context = await browser.new_context()
        print("✅ Context created successfully")
        print(f"Context methods: {[method for method in dir(context) if not method.startswith('_')]}")
        
        # Check if context has page methods
        if hasattr(context, 'new_page'):
            page = await context.new_page()
            print("✅ Page created successfully")
            print(f"Page methods: {[method for method in dir(page) if not method.startswith('_')]}")
            
            # Test navigation
            await page.goto("https://www.google.com")
            print("✅ Navigation successful")
            
            await page.close()
        
        await context.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_browser_api())