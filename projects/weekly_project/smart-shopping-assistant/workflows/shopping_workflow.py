"""
Main Shopping Workflow using LangGraph
Orchestrates the entire smart shopping process
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Literal
from langgraph.graph import StateGraph, END

# Add absolute path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to import checkpoint, but continue without if not available
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    CHECKPOINT_AVAILABLE = True
except ImportError:
    try:
        from langgraph_checkpoint.sqlite import SqliteSaver
        CHECKPOINT_AVAILABLE = True
    except ImportError:
        CHECKPOINT_AVAILABLE = False
        print("⚠️ Checkpoint not available - running without persistence")

import os
import sys

# Add parent directory to path for absolute imports when run directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from workflows.states.workflow_states import WorkflowState, WorkflowConfig, create_initial_state, increment_retry
from workflows.nodes.planner_node import PlannerNode
from workflows.nodes.site_navigator_node import SiteNavigatorNode
from workflows.nodes.data_extractor_node import DataExtractorNode, ValidatorNode
from workflows.nodes.comparator_node import ComparatorNode, NotificationNode

class SmartShoppingWorkflow:
    """Main workflow orchestrator for smart shopping assistant"""
    
    def __init__(self, config: WorkflowConfig = None):
        self.config = config or WorkflowConfig()
        self.setup_checkpointing()  # Setup checkpointing first
        self.setup_nodes()
        self.setup_workflow()
    
    def setup_nodes(self):
        """Initialize all workflow nodes"""
        self.planner_node = PlannerNode()
        self.navigator_node = SiteNavigatorNode()
        self.extractor_node = DataExtractorNode()
        self.validator_node = ValidatorNode()
        self.comparator_node = ComparatorNode()
        self.notification_node = NotificationNode()
    
    def setup_workflow(self):
        """Setup LangGraph workflow with nodes and edges"""
        
        # Create the workflow graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("planner", self.planner_step)
        workflow.add_node("navigator", self.navigator_step)
        workflow.add_node("extractor", self.extractor_step)
        workflow.add_node("validator", self.validator_step)
        workflow.add_node("comparator", self.comparator_step)
        workflow.add_node("notifier", self.notifier_step)
        workflow.add_node("retry", self.retry_step)
        workflow.add_node("error_handler", self.error_handler_step)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add edges with conditional routing
        workflow.add_conditional_edges(
            "planner",
            self.should_continue_after_planning,
            {
                "continue": "navigator",
                "retry": "retry",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "navigator",
            self.should_continue_after_navigation,
            {
                "continue": "extractor",
                "retry": "retry",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "extractor",
            self.should_continue_after_extraction,
            {
                "continue": "validator",
                "retry": "retry",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "validator",
            self.should_continue_after_validation,
            {
                "continue": "comparator",
                "retry": "retry",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "comparator",
            self.should_continue_after_comparison,
            {
                "continue": "notifier",
                "retry": "retry",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("notifier", END)
        workflow.add_edge("error_handler", END)
        
        # Add retry logic
        workflow.add_conditional_edges(
            "retry",
            self.should_retry,
            {
                "planner": "planner",
                "navigator": "navigator",
                "extractor": "extractor",
                "validator": "validator",
                "comparator": "comparator",
                "stop": "error_handler"
            }
        )
        
        # Compile workflow with optional checkpointing
        if self.checkpointer:
            self.workflow = workflow.compile(checkpointer=self.checkpointer)
        else:
            self.workflow = workflow.compile()
    
    def setup_checkpointing(self):
        """Setup SQLite checkpointing for workflow state persistence"""
        if CHECKPOINT_AVAILABLE:
            try:
                checkpoint_db = os.getenv("LANGGRAPH_CHECKPOINT_DB", "sqlite:///data/langgraph_checkpoints.db")
                self.checkpointer = SqliteSaver.from_conn_string(checkpoint_db)
                print("✅ Checkpointing enabled with SQLite")
            except Exception as e:
                print(f"⚠️ Checkpointing failed to initialize: {e}")
                self.checkpointer = None
        else:
            self.checkpointer = None
            print("⚠️ Running without checkpointing - state will not persist")
    
    # Node execution methods
    async def planner_step(self, state: WorkflowState) -> WorkflowState:
        """Execute planning step"""
        print("🧠 Executing planner step...")
        state["current_step"] = "planner"
        
        # Ensure error_log exists
        if "error_log" not in state:
            state["error_log"] = []
        
        # Ensure search_planning exists with basic structure
        if "search_planning" not in state:
            state["search_planning"] = {
                "query": "",
                "selected_sites": [],
                "user_intent": "",
                "product_category": "",
                "price_range": None,
                "search_strategy": "",
                "user_preferences": {}
            }
            
        try:
            result = await self.planner_node.plan_search(state)
            result["workflow_status"] = "planning_completed"
            result["current_step"] = "planner"
            print(f"✅ Planning completed: {result['search_planning']['selected_sites']}")
            return result
        except Exception as e:
            print(f"❌ Planning failed: {e}")
            state["workflow_status"] = "planning_failed"
            state["error_log"].append({
                "step": "planner",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            })
            return state
    
    async def navigator_step(self, state: WorkflowState) -> WorkflowState:
        """Execute navigation step"""
        print("🌐 Executing navigator step...")
        state["current_step"] = "site_navigator"
        
        # Ensure error_log exists
        if "error_log" not in state:
            state["error_log"] = []
            
        try:
            result = await self.navigator_node.execute(state)
            result["workflow_status"] = "navigation_completed"
            result["current_step"] = "site_navigator"
            print(f"✅ Navigation completed")
            return result
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            state["workflow_status"] = "navigation_failed"
            state["error_log"].append({
                "step": "navigator",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            })
            return state
    
    async def extractor_step(self, state: WorkflowState) -> WorkflowState:
        """Execute extraction step"""
        print("🔍 Executing extractor step...")
        state["current_step"] = "data_extractor"
        
        # Ensure error_log exists
        if "error_log" not in state:
            state["error_log"] = []
            
        try:
            result = await self.extractor_node.execute(state)
            result["workflow_status"] = "extraction_completed"
            result["current_step"] = "data_extractor"
            print(f"✅ Extraction completed")
            return result
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            state["workflow_status"] = "extraction_failed"
            state["error_log"].append({
                "step": "extractor",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            })
            return state
    
    async def validator_step(self, state: WorkflowState) -> WorkflowState:
        """Execute validation step"""
        print("✅ Executing validator step...")
        state["current_step"] = "validator"
        
        # Ensure error_log exists
        if "error_log" not in state:
            state["error_log"] = []
            
        try:
            result = await self.validator_node.execute(state)
            result["workflow_status"] = "validation_completed"
            result["current_step"] = "validator"
            print(f"✅ Validation completed")
            return result
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            state["workflow_status"] = "validation_failed"
            state["error_log"].append({
                "step": "validator",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            })
            return state
    
    async def comparator_step(self, state: WorkflowState) -> WorkflowState:
        """Execute comparison step"""
        print("📊 Executing comparator step...")
        state["current_step"] = "comparator"
        
        # Ensure error_log exists
        if "error_log" not in state:
            state["error_log"] = []
            
        try:
            result = await self.comparator_node.execute(state)
            result["workflow_status"] = "comparison_completed"
            result["current_step"] = "comparator"
            print(f"✅ Comparison completed")
            return result
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
            state["workflow_status"] = "comparison_failed"
            state["error_log"].append({
                "step": "comparator",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            })
            return state
    
    async def notifier_step(self, state: WorkflowState) -> WorkflowState:
        """Execute notification step"""
        print("📢 Executing notifier step...")
        state["current_step"] = "notifier"
        
        # Ensure error_log exists
        if "error_log" not in state:
            state["error_log"] = []
            
        try:
            result = await self.notification_node.execute(state)
            result["workflow_status"] = "notification_completed"
            result["current_step"] = "notifier"
            print(f"✅ Notification completed")
            return result
        except Exception as e:
            print(f"❌ Notification failed: {e}")
            state["workflow_status"] = "notification_failed"
            state["error_log"].append({
                "step": "notifier",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            })
            return state
    
    async def retry_step(self, state: WorkflowState) -> WorkflowState:
        """Handle retry logic"""
        # Ensure retry_attempts exists and increment it
        retry_attempts = state.get("retry_attempts", 0)
        state["retry_attempts"] = retry_attempts + 1
        
        print(f"🔄 Executing retry step (attempt {state['retry_attempts']})...")
        state["current_step"] = "retry_handler"
        
        # Add delay for retries with exponential backoff
        delay = min(2 ** retry_attempts, 8)  # Cap at 8 seconds
        await asyncio.sleep(delay)
        print(f"🔄 Retry attempt {state['retry_attempts']} ready")
        
        return state
    
    async def error_handler_step(self, state: WorkflowState) -> WorkflowState:
        """Handle workflow errors"""
        print("❌ Executing error handler step...")
        state["workflow_status"] = "failed"
        state["current_step"] = "error_handler"
        
        # Ensure required fields exist with safe defaults
        retry_attempts = state.get("retry_attempts", 0)
        error_log = state.get("error_log", [])
        
        # Log final error state
        print(f"Workflow failed after {retry_attempts} retries")
        print(f"Error log: {error_log}")
        
        return state
    
    # Edge condition methods
    def should_continue_after_planning(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        """Determine next step after planning"""
        status = state["workflow_status"]
        
        if status == "planning_completed":
            return "continue"
        elif status == "planning_failed" and state["retry_attempts"] < self.config.max_retries:
            return "retry"
        else:
            return "error"
    
    def should_continue_after_navigation(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        """Determine next step after navigation"""
        status = state["workflow_status"]
        
        if status == "navigation_completed":
            # Check if we have any products
            products = state["data_extraction"]["extracted_products"]
            if products:
                return "continue"
            elif state["retry_attempts"] < self.config.max_retries:
                return "retry"
            else:
                return "error"
        elif status == "navigation_failed" and state["retry_attempts"] < self.config.max_retries:
            return "retry"
        else:
            return "error"
    
    def should_continue_after_extraction(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        """Determine next step after extraction"""
        status = state["workflow_status"]
        
        if status == "extraction_completed":
            return "continue"
        elif status == "extraction_failed" and state["retry_attempts"] < self.config.max_retries:
            return "retry"
        else:
            return "error"
    
    def should_continue_after_validation(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        """Determine next step after validation"""
        status = state["workflow_status"]
        
        if status == "validation_completed":
            # Check if we have valid products
            valid_products = state["validation"]["validated_products"]
            if valid_products:
                return "continue"
            elif state["retry_attempts"] < self.config.max_retries:
                return "retry"
            else:
                return "error"
        elif status == "validation_failed" and state["retry_attempts"] < self.config.max_retries:
            return "retry"
        else:
            return "error"
    
    def should_continue_after_comparison(self, state: WorkflowState) -> Literal["continue", "retry", "error"]:
        """Determine next step after comparison"""
        status = state["workflow_status"]
        
        if status == "comparison_completed":
            return "continue"
        elif status == "comparison_failed" and state["retry_attempts"] < self.config.max_retries:
            return "retry"
        else:
            return "error"
    
    def should_retry(self, state: WorkflowState) -> str:
        """Determine retry target based on failure point"""
        if state["retry_attempts"] >= self.config.max_retries:
            return "stop"
        
        # Determine where to retry based on last failure
        status = state["workflow_status"]
        
        if "planning" in status:
            return "planner"
        elif "navigation" in status:
            return "navigator"
        elif "extraction" in status:
            return "extractor"
        elif "validation" in status:
            return "validator"
        elif "comparison" in status:
            return "comparator"
        else:
            return "stop"
    
    # Main execution methods
    async def execute_search(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Execute complete search workflow"""
        try:
            # Create initial state
            initial_state = create_initial_state(query, user_id)
            
            # Execute workflow
            config = {"configurable": {"thread_id": initial_state["session_id"]}}
            
            result = await self.workflow.ainvoke(initial_state, config)
            
            # Format result for return
            return self.format_workflow_result(result)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "products": [],
                "workflow_status": "failed"
            }
    
    def format_workflow_result(self, state: WorkflowState) -> Dict[str, Any]:
        """Format workflow result for external consumption"""
        validated_products = state["validation"]["validated_products"]
        best_deals = state["comparison"]["best_deals"]
        comparison_metrics = state["comparison"]["comparison_metrics"]
        
        return {
            "success": state["workflow_status"] not in ["failed", "planning_failed", "navigation_failed", "extraction_failed", "validation_failed", "comparison_failed"],
            "query": state["search_planning"]["query"],
            "workflow_id": state["workflow_id"],
            "session_id": state["session_id"],
            
            # Product data
            "products": validated_products,
            "total_products": len(validated_products),
            
            # Deal information
            "best_deals": [deal["product"] for deal in best_deals[:3]],  # Top 3 deals
            "deal_count": len(best_deals),
            
            # Comparison data
            "price_comparisons": state["comparison"]["price_comparisons"],
            "comparison_metrics": comparison_metrics,
            
            # Quality metrics
            "data_quality": {
                "confidence_score": state["data_extraction"]["confidence_score"],
                "quality_score": state["validation"]["quality_score"],
                "recommendation_score": state["comparison"]["recommendation_score"]
            },
            
            # Execution info
            "sites_searched": state["search_planning"]["selected_sites"],
            "execution_time": state.get("execution_time"),
            "workflow_status": state["workflow_status"],
            "retry_attempts": state["retry_attempts"],
            
            # Errors (if any)
            "errors": state["error_log"] if state["error_log"] else None,
            "validation_errors": state["validation"]["validation_errors"] if state["validation"]["validation_errors"] else None
        }
    
    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await self.workflow.aget_state(config)
            
            if state:
                return {
                    "session_id": session_id,
                    "current_step": state.values.get("current_step", "unknown"),
                    "workflow_status": state.values.get("workflow_status", "unknown"),
                    "retry_attempts": state.values.get("retry_attempts", 0),
                    "products_found": len(state.values.get("validation", {}).get("validated_products", [])),
                    "last_update": state.values.get("validation", {}).get("validation_timestamp", "")
                }
            else:
                return {"error": "Session not found"}
                
        except Exception as e:
            return {"error": str(e)}

# Factory function for easy instantiation
def create_shopping_workflow(config: WorkflowConfig = None):
    """Create and return a configured shopping workflow graph"""
    from langgraph.graph import StateGraph, END
    from workflows.states.workflow_states import WorkflowState
    
    # Create workflow instance
    workflow_instance = SmartShoppingWorkflow(config)
    
    # Create the state graph
    graph = StateGraph(WorkflowState)
    
    # Add all workflow nodes dynamically
    graph.add_node("planner", workflow_instance.planner_step)
    graph.add_node("site_navigator", workflow_instance.navigator_step)
    graph.add_node("data_extractor", workflow_instance.extractor_step)
    graph.add_node("validator", workflow_instance.validator_step)
    graph.add_node("comparator", workflow_instance.comparator_step)
    graph.add_node("notifier", workflow_instance.notifier_step)
    graph.add_node("retry_handler", workflow_instance.retry_step)
    graph.add_node("error_handler", workflow_instance.error_handler_step)
    
    # Set entry point
    graph.set_entry_point("planner")
    
    # Define workflow transitions (dynamic routing)
    def should_continue_to_navigator(state: WorkflowState) -> str:
        """Route from planner to navigator or error"""
        status = state.get("workflow_status", "unknown")
        retry_attempts = state.get("retry_attempts", 0)
        max_retries = state.get("max_retries", 3)
        
        if status == "planning_completed":
            return "site_navigator"
        elif status == "planning_failed":
            if retry_attempts < max_retries:
                return "retry_handler"
            else:
                return "error_handler"
        else:
            return "retry_handler"
    
    def should_continue_to_extractor(state: WorkflowState) -> str:
        """Route from navigator to extractor"""
        status = state.get("workflow_status", "unknown")
        retry_attempts = state.get("retry_attempts", 0)
        max_retries = state.get("max_retries", 3)
        
        if status == "navigation_completed":
            return "data_extractor"
        elif status == "navigation_failed":
            if retry_attempts < max_retries:
                return "retry_handler"
            else:
                return "error_handler"
        else:
            return "retry_handler"
    
    def should_continue_to_validator(state: WorkflowState) -> str:
        """Route from extractor to validator"""
        status = state.get("workflow_status", "unknown")
        retry_attempts = state.get("retry_attempts", 0)
        max_retries = state.get("max_retries", 3)
        
        if status == "extraction_completed":
            return "validator"
        elif status == "extraction_failed":
            if retry_attempts < max_retries:
                return "retry_handler"
            else:
                return "error_handler"
        else:
            return "retry_handler"
    
    def should_continue_to_comparator(state: WorkflowState) -> str:
        """Route from validator to comparator"""
        status = state.get("workflow_status", "unknown")
        retry_attempts = state.get("retry_attempts", 0)
        max_retries = state.get("max_retries", 3)
        
        if status == "validation_completed":
            return "comparator"
        elif status == "validation_failed":
            if retry_attempts < max_retries:
                return "retry_handler"
            else:
                return "error_handler"
        else:
            return "retry_handler"
    
    def should_continue_to_notifier(state: WorkflowState) -> str:
        """Route from comparator to notifier or end"""
        status = state.get("workflow_status", "unknown")
        retry_attempts = state.get("retry_attempts", 0)
        max_retries = state.get("max_retries", 3)
        
        if status == "comparison_completed":
            return "notifier"
        elif status == "comparison_failed":
            if retry_attempts < max_retries:
                return "retry_handler"
            else:
                return "error_handler"
        else:
            return "retry_handler"
    
    def should_continue_after_notifier(state: WorkflowState) -> str:
        """Route from notifier to end"""
        status = state.get("workflow_status", "unknown")
        
        if status in ["notification_completed", "notification_failed"]:
            return END
        else:
            return "retry_handler"
    
    def should_retry_or_fail(state: WorkflowState) -> str:
        """Route from retry handler back to appropriate step"""
        retry_attempts = state.get("retry_attempts", 0)
        max_retries = state.get("max_retries", 3)
        
        if retry_attempts >= max_retries:
            return "error_handler"
        
        # Route back to the step that failed
        current_step = state.get("current_step", "planner")
        if current_step == "planner":
            return "planner"
        elif current_step == "site_navigator":
            return "site_navigator"
        elif current_step == "data_extractor":
            return "data_extractor"
        elif current_step == "validator":
            return "validator"
        elif current_step == "comparator":
            return "comparator"
        elif current_step == "notifier":
            return "notifier"
        else:
            return "planner"
    
    # Add conditional edges for dynamic routing
    graph.add_conditional_edges(
        "planner", 
        should_continue_to_navigator,
        {
            "site_navigator": "site_navigator",
            "retry_handler": "retry_handler", 
            "error_handler": "error_handler"
        }
    )
    
    graph.add_conditional_edges(
        "site_navigator", 
        should_continue_to_extractor,
        {
            "data_extractor": "data_extractor",
            "retry_handler": "retry_handler",
            "error_handler": "error_handler"
        }
    )
    
    graph.add_conditional_edges(
        "data_extractor", 
        should_continue_to_validator,
        {
            "validator": "validator",
            "retry_handler": "retry_handler",
            "error_handler": "error_handler"
        }
    )
    
    graph.add_conditional_edges(
        "validator", 
        should_continue_to_comparator,
        {
            "comparator": "comparator",
            "retry_handler": "retry_handler",
            "error_handler": "error_handler"
        }
    )
    
    graph.add_conditional_edges(
        "comparator", 
        should_continue_to_notifier,
        {
            "notifier": "notifier",
            "retry_handler": "retry_handler",
            "error_handler": "error_handler"
        }
    )
    
    graph.add_conditional_edges(
        "notifier", 
        should_continue_after_notifier,
        {
            "retry_handler": "retry_handler",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "retry_handler", 
        should_retry_or_fail,
        {
            "planner": "planner",
            "site_navigator": "site_navigator",
            "data_extractor": "data_extractor", 
            "validator": "validator",
            "comparator": "comparator",
            "notifier": "notifier",
            "error_handler": "error_handler"
        }
    )
    
    # Error handler always ends
    graph.add_edge("error_handler", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    # Store reference in workflow instance
    workflow_instance.workflow = compiled_graph
    
    return compiled_graph