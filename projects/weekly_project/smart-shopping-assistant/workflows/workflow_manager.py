"""
Workflow Manager for Smart Shopping Assistant
Manages workflow execution and integration with existing components
"""

import asyncio
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add absolute path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from workflows import create_shopping_workflow, WorkflowConfig
from database.database import Database

class WorkflowManager:
    """Manager for coordinating workflows with existing system components"""
    
    def __init__(self, database: Database, price_tracker=None):
        self.database = database
        self.price_tracker = price_tracker
        
        # Configure workflow
        self.workflow_config = WorkflowConfig(
            max_retries=int(os.getenv("LANGGRAPH_MAX_RETRIES", "3")),
            timeout=int(os.getenv("LANGGRAPH_TIMEOUT", "300")),
            headless_browser=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            stealth_mode=os.getenv("BROWSER_STEALTH", "true").lower() == "true",
            parallel_execution=True,
            cache_results=True,
            enable_notifications=True,
            debug_mode=False
        )
        
        # Create workflow instance
        self.workflow = create_shopping_workflow(self.workflow_config)
        
        # Track active sessions
        self.active_sessions = {}
    
    async def search_product_workflow(self, product_name: str, websites: List[str]) -> Dict[str, Any]:
        """Execute product search workflow - main entry point for dashboard"""
        try:
            # Import the proper state creation function
            from workflows.states.workflow_states import create_initial_state
            
            # Create proper initial state with all required fields
            initial_state = create_initial_state(product_name)
            
            # Set the websites in the search planning
            initial_state["search_planning"]["selected_sites"] = websites
            
            print(f"🔧 Executing workflow for: {product_name}")
            
            # Execute the workflow with proper method call
            result = await self.workflow.ainvoke(initial_state)
            
            print(f"✅ Workflow completed with status: {result.get('workflow_status', 'unknown')}")
            
            # Extract products from validation state
            products = result.get("validation", {}).get("validated_products", [])
            
            # Convert to expected format
            return {
                "success": True,
                "products": products,
                "workflow_status": result.get("workflow_status", "completed"),
                "session_id": result.get("session_id", f"session_{hash(str(initial_state))}"), 
                "query": product_name
            }
            
        except Exception as e:
            print(f"❌ Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "products": [],
                "workflow_status": "failed",
                "query": product_name
            }
    
    async def search_products_async(self, query: str, user_id: str = "default", selected_sites: List[str] = None) -> Dict[str, Any]:
        """Execute product search using LangGraph workflow"""
        try:
            # Use provided sites or default to all sites
            websites = selected_sites if selected_sites else ["amazon.in", "flipkart.com", "myntra.com", "ajio.com"]
            
            # Execute workflow using the main method
            result = await self.search_product_workflow(
                product_name=query,
                websites=websites
            )
            
            # Store session info
            if result.get("session_id"):
                self.active_sessions[result["session_id"]] = {
                    "query": query,
                    "user_id": user_id,
                    "start_time": datetime.now(),
                    "status": result.get("workflow_status", "unknown")
                }
            
            # If successful, save products to database for tracking
            if result["success"] and result["products"]:
                await self.save_products_to_database(result["products"], query)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "products": [],
                "workflow_status": "failed"
            }
    
    def search_products_sync(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Synchronous wrapper for product search"""
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.search_products_async(query, user_id))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "products": [],
                "workflow_status": "failed"
            }
    
    async def save_products_to_database(self, products: List[Dict[str, Any]], query: str):
        """Save workflow products to database for tracking"""
        try:
            for product in products:
                # Extract price as float
                price_str = product.get("price", "")
                current_price = self.extract_price_float(price_str)
                
                if current_price is None:
                    continue
                
                # Create product record
                product_data = {
                    "name": product.get("name", ""),
                    "url": product.get("url", ""),
                    "current_price": current_price,
                    "site": product.get("site", ""),
                    "rating": self.extract_rating_float(product.get("rating", "")),
                    "category": product.get("category", "other"),
                    "brand": product.get("brand", "Unknown"),
                    "features": ", ".join(product.get("key_features", [])),
                    "search_query": query,
                    "relevance_score": product.get("relevance_score", 0.5)
                }
                
                # Check if product already exists
                existing_product = self.database.find_product_by_url(product_data["url"])
                
                if existing_product:
                    # Update existing product
                    self.database.update_product_price(existing_product.id, current_price)
                else:
                    # Add new product
                    self.database.add_product(
                        name=product_data["name"],
                        url=product_data["url"],
                        current_price=current_price,
                        site=product_data["site"]
                    )
                    
        except Exception as e:
            print(f"Error saving products to database: {e}")
    
    def extract_price_float(self, price_str: str) -> Optional[float]:
        """Extract float price from price string"""
        if not price_str or price_str == "Price not available":
            return None
        
        try:
            # Remove currency symbols and commas
            import re
            price_clean = re.sub(r'[^\d.]', '', price_str)
            return float(price_clean) if price_clean else None
        except:
            return None
    
    def extract_rating_float(self, rating_str: str) -> Optional[float]:
        """Extract float rating from rating string"""
        if not rating_str:
            return None
        
        try:
            return float(rating_str)
        except:
            return None
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a workflow session"""
        try:
            # Get workflow status
            workflow_status = await self.workflow.get_workflow_status(session_id)
            
            # Add session info if available
            if session_id in self.active_sessions:
                session_info = self.active_sessions[session_id]
                workflow_status.update({
                    "query": session_info["query"],
                    "user_id": session_info["user_id"],
                    "duration": str(datetime.now() - session_info["start_time"])
                })
            
            return workflow_status
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active workflow sessions"""
        return {
            session_id: {
                **session_info,
                "start_time": session_info["start_time"].isoformat(),
                "duration": str(datetime.now() - session_info["start_time"])
            }
            for session_id, session_info in self.active_sessions.items()
        }
    
    def convert_legacy_results(self, legacy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy search results to workflow format"""
        try:
            # Extract products from legacy format
            products = []
            
            if "sites" in legacy_results:
                for site_name, site_data in legacy_results["sites"].items():
                    if isinstance(site_data, dict) and "products" in site_data:
                        for product in site_data["products"]:
                            # Convert to workflow format
                            converted_product = {
                                "name": product.get("name", ""),
                                "price": product.get("price", ""),
                                "rating": product.get("rating", "4.0"),
                                "url": product.get("url", ""),
                                "availability": product.get("availability", "Available"),
                                "site": site_name,
                                "category": "other",
                                "brand": "Unknown",
                                "key_features": [],
                                "relevance_score": 0.7,  # Default relevance
                                "extracted_at": datetime.now().isoformat()
                            }
                            products.append(converted_product)
            
            # Convert to workflow result format
            return {
                "success": len(products) > 0,
                "query": legacy_results.get("product_name", ""),
                "workflow_id": f"legacy_{int(datetime.now().timestamp())}",
                "session_id": f"legacy_session_{int(datetime.now().timestamp())}",
                "products": products,
                "total_products": len(products),
                "best_deals": products[:3],  # Top 3 as best deals
                "deal_count": min(3, len(products)),
                "price_comparisons": [],
                "comparison_metrics": {
                    "total_products": len(products),
                    "site_distribution": self.get_site_distribution(products),
                    "category_distribution": {"other": len(products)}
                },
                "data_quality": {
                    "confidence_score": 0.8,
                    "quality_score": 0.7,
                    "recommendation_score": 0.75
                },
                "sites_searched": list(set(p["site"] for p in products)),
                "workflow_status": "completed_legacy",
                "retry_attempts": 0,
                "errors": None,
                "validation_errors": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Legacy conversion failed: {str(e)}",
                "query": "",
                "products": [],
                "workflow_status": "failed"
            }
    
    def get_site_distribution(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of products by site"""
        distribution = {}
        for product in products:
            site = product.get("site", "unknown")
            distribution[site] = distribution.get(site, 0) + 1
        return distribution
    
    def is_workflow_enabled(self) -> bool:
        """Check if workflow execution is enabled"""
        return os.getenv("ENABLE_LANGGRAPH_WORKFLOW", "true").lower() == "true"
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get current workflow configuration"""
        return {
            "max_retries": self.workflow_config.max_retries,
            "timeout": self.workflow_config.timeout,
            "headless_browser": self.workflow_config.headless_browser,
            "stealth_mode": self.workflow_config.stealth_mode,
            "parallel_execution": self.workflow_config.parallel_execution,
            "cache_results": self.workflow_config.cache_results,
            "enable_notifications": self.workflow_config.enable_notifications,
            "debug_mode": self.workflow_config.debug_mode
        }

# Global workflow manager instance (to be initialized by main app)
workflow_manager: Optional[WorkflowManager] = None

def initialize_workflow_manager(database: Database, price_tracker=None) -> WorkflowManager:
    """Initialize global workflow manager"""
    global workflow_manager
    workflow_manager = WorkflowManager(database, price_tracker)
    return workflow_manager

def get_workflow_manager() -> Optional[WorkflowManager]:
    """Get global workflow manager instance"""
    return workflow_manager