"""
Planner Node for Smart Shopping Assistant
Handles query analysis and search strategy planning using Groq
"""

import os
import sys
import asyncio
from typing import Dict, List, Any
from groq import Groq
import json
import re

# Add absolute path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from workflows.states.workflow_states import WorkflowState, update_state_step, log_error

class PlannerNode:
    """Node responsible for planning search strategy using AI"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        # Site capabilities mapping
        self.site_capabilities = {
            "amazon.in": {
                "categories": ["electronics", "books", "clothing", "home", "sports", "beauty"],
                "strengths": ["wide_selection", "competitive_pricing", "fast_delivery"],
                "price_range": "all"
            },
            "flipkart.com": {
                "categories": ["electronics", "clothing", "home", "sports", "beauty"],
                "strengths": ["local_brands", "festive_offers", "easy_returns"],
                "price_range": "budget_to_premium"
            },
            "myntra.com": {
                "categories": ["clothing", "beauty", "accessories", "home"],
                "strengths": ["fashion_focus", "brand_variety", "style_recommendations"],
                "price_range": "budget_to_luxury"
            },
            "ajio.com": {
                "categories": ["clothing", "accessories", "beauty", "home"],
                "strengths": ["trendy_fashion", "exclusive_brands", "youth_focus"],
                "price_range": "affordable_to_premium"
            }
        }
    
    async def plan_search(self, state: WorkflowState) -> WorkflowState:
        """Plan search strategy and select sites"""
        try:
            query = state["search_planning"]["query"]
            
            # Analyze query using Groq with retry logic
            analysis = await self.analyze_query_with_retry(query)
            
            # Update search planning state
            state["search_planning"]["user_intent"] = analysis["intent"]
            state["search_planning"]["product_category"] = analysis["category"]
            state["search_planning"]["price_range"] = analysis.get("price_range")
            state["search_planning"]["search_strategy"] = analysis["strategy"]
            
            # Use selected sites from state if available, otherwise select optimal sites
            if state["search_planning"]["selected_sites"]:
                # User has pre-selected sites, use them
                selected_sites = state["search_planning"]["selected_sites"]
                print(f"🌐 Using user-selected sites: {selected_sites}")
            else:
                # No pre-selection, use category-based selection
                selected_sites = self.select_sites(analysis["category"], analysis.get("price_range"))
                print(f"🤖 AI-selected sites based on category '{analysis['category']}': {selected_sites}")
            
            state["search_planning"]["selected_sites"] = selected_sites
            
            # Set user preferences
            state["search_planning"]["user_preferences"] = {
                "priority": analysis.get("priority", "price"),
                "filters": analysis.get("filters", {}),
                "sort_by": analysis.get("sort_by", "relevance")
            }
            
            state["workflow_status"] = "planning_completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Planning failed: {str(e)}", "planning")
            state["workflow_status"] = "planning_failed"
            return state
    
    async def analyze_query_with_retry(self, query: str, max_attempts: int = 3) -> Dict[str, Any]:
        """Analyze query with retry logic and fallback"""
        for attempt in range(max_attempts):
            try:
                return await self.analyze_query(query)
            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Groq API attempt {attempt + 1} failed: {str(e)}")
                        print(f"Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print("All Groq API attempts failed, using fallback analysis")
                        return self.get_fallback_analysis(query)
                else:
                    print(f"Groq API error (non-rate-limit): {str(e)}, using fallback")
                    return self.get_fallback_analysis(query)
        
        return self.get_fallback_analysis(query)
    
    def get_fallback_analysis(self, query: str) -> Dict[str, Any]:
        """Provide fallback analysis when Groq API is unavailable"""
        category = self.extract_category_fallback(query)
        
        return {
            "intent": "search",
            "category": category,
            "strategy": "broad_search",
            "priority": "relevance",
            "filters": {},
            "sort_by": "relevance"
        }
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze search query using Groq AI with improved error handling"""
        
        prompt = f"""
        Analyze this shopping search query and provide structured information:
        
        Query: "{query}"
        
        Please analyze and return a JSON response with:
        1. intent: What is the user trying to do? (search, compare, track, buy)
        2. category: Product category (electronics, clothing, books, home, sports, beauty, other)
        3. price_range: If mentioned, extract min and max price in INR
        4. strategy: Best search strategy (broad_search, specific_search, brand_focused, price_focused)
        5. priority: What seems most important (price, quality, brand, features, reviews)
        6. filters: Any specific filters mentioned (brand, color, size, features)
        7. sort_by: How results should be sorted (price, ratings, relevance, popularity)
        
        Example response:
        {{
            "intent": "search",
            "category": "electronics",
            "price_range": {{"min": 10000, "max": 50000}},
            "strategy": "specific_search",
            "priority": "price",
            "filters": {{"brand": "samsung", "type": "smartphone"}},
            "sort_by": "price"
        }}
        
        Only return valid JSON, no other text.
        """
        
        try:
            # Add exponential backoff to reduce API pressure
            import time
            import asyncio
            
            for attempt in range(3):  # Max 3 attempts
                try:
                    response = self.groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are an expert shopping assistant that analyzes search queries. Always respond with valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        model=self.model,
                        temperature=0.1,
                        max_tokens=500
                    )
                    
                    # Parse JSON response
                    content = response.choices[0].message.content.strip()
                    
                    # Clean up response to ensure valid JSON
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    
                    # Remove any extra content after the JSON
                    content = content.strip()
                    if content.count('}') > content.count('{'):
                        # Find the last complete JSON object
                        brace_count = 0
                        end_index = -1
                        for i, char in enumerate(content):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_index = i + 1
                                    break
                        if end_index > 0:
                            content = content[:end_index]
                    
                    analysis = json.loads(content)
                    
                    # Validate and set defaults
                    analysis.setdefault("intent", "search")
                    analysis.setdefault("category", "other")
                    analysis.setdefault("strategy", "broad_search")
                    analysis.setdefault("priority", "relevance")
                    analysis.setdefault("filters", {})
                    analysis.setdefault("sort_by", "relevance")
                    
                    return analysis
                    
                except Exception as api_error:
                    print(f"Groq API attempt {attempt + 1} failed: {api_error}")
                    if attempt < 2:  # Don't wait after last attempt
                        wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s
                        print(f"Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                    continue
            
            # If all attempts failed, use fallback
            print("All Groq API attempts failed, using fallback analysis")
            return self.get_fallback_analysis(query)
            
        except Exception as e:
            print(f"Query analysis failed: {e}")
            return self.get_fallback_analysis(query)
    
    def get_fallback_analysis(self, query: str) -> Dict[str, Any]:
        """Generate fallback analysis when Groq API fails"""
        return {
            "intent": "search",
            "category": self.extract_category_fallback(query),
            "strategy": "broad_search",
            "priority": "relevance",
            "filters": {},
            "sort_by": "relevance"
        }
    
    def extract_category_fallback(self, query: str) -> str:
        """Fallback category extraction using keywords"""
        query_lower = query.lower()
        
        # Electronics keywords
        if any(word in query_lower for word in ["phone", "mobile", "laptop", "computer", "tablet", "headphone", "camera", "tv", "smartwatch"]):
            return "electronics"
        
        # Clothing keywords
        elif any(word in query_lower for word in ["shirt", "tshirt", "jeans", "dress", "jacket", "shoes", "clothes", "fashion"]):
            return "clothing"
        
        # Home keywords
        elif any(word in query_lower for word in ["furniture", "kitchen", "home", "decor", "appliance", "lunch", "box", "storage", "container"]):
            return "home"
        
        # Beauty keywords
        elif any(word in query_lower for word in ["makeup", "skincare", "beauty", "cosmetics", "perfume"]):
            return "beauty"
        
        # Sports keywords
        elif any(word in query_lower for word in ["sports", "fitness", "gym", "exercise", "outdoor"]):
            return "sports"
        
        # Books keywords
        elif any(word in query_lower for word in ["book", "novel", "textbook", "magazine"]):
            return "books"
        
        else:
            return "other"
    
    def select_sites(self, category: str, price_range: Dict = None) -> List[str]:
        """Select optimal sites based on category and price range"""
        suitable_sites = []
        
        for site, capabilities in self.site_capabilities.items():
            # Check if site handles this category
            if category in capabilities["categories"] or category == "other":
                suitable_sites.append(site)
        
        # If no specific sites found, include all major sites
        if not suitable_sites:
            suitable_sites = ["amazon.in", "flipkart.com"]
        
        # Always include Amazon and Flipkart for broad coverage
        priority_sites = ["amazon.in", "flipkart.com"]
        for site in priority_sites:
            if site not in suitable_sites:
                suitable_sites.append(site)
        
        # Add category-specific sites
        if category in ["clothing", "beauty", "accessories"]:
            if "myntra.com" not in suitable_sites:
                suitable_sites.append("myntra.com")
            if "ajio.com" not in suitable_sites:
                suitable_sites.append("ajio.com")
        elif category in ["home", "other"]:
            # Include fashion sites for home accessories and general products
            if "myntra.com" not in suitable_sites:
                suitable_sites.append("myntra.com")
            if "ajio.com" not in suitable_sites:
                suitable_sites.append("ajio.com")
        
        # Ensure we always have all 4 sites for comprehensive search
        all_sites = ["amazon.in", "flipkart.com", "myntra.com", "ajio.com"]
        for site in all_sites:
            if site not in suitable_sites:
                suitable_sites.append(site)
        
        return suitable_sites[:4]  # Return all 4 sites
    
    def should_retry(self, state: WorkflowState) -> bool:
        """Determine if planning should be retried"""
        return (state["retry_attempts"] < state["max_retries"] and 
                state["workflow_status"] == "planning_failed")