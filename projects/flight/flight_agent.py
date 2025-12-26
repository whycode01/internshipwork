"""Main flight scraper agent using LangGraph."""

from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from flight_scraper_node import FlightScraperNode
from flight_sites_config import get_supported_sites
from llm_processor_node import LLMProcessorNode


class FlightSearchState(TypedDict):
    """State structure for the flight search workflow."""
    # Input parameters
    site: str
    from_city: str
    to_city: str
    travel_date: str
    
    # Browser scraper outputs
    browser_result: str
    success: bool
    site_used: str
    
    # LLM processor outputs
    llm_analysis: str
    structured_flights: list
    recommendations: list
    processing_success: bool


def create_graph():
    """Create and return the compiled LangGraph workflow for LangGraph Studio."""
    scraper_node = FlightScraperNode()
    processor_node = LLMProcessorNode()
    
    # Build the LangGraph workflow
    workflow = StateGraph(FlightSearchState)
    
    # Add processing nodes
    workflow.add_node("browser_scraper", scraper_node.process)
    workflow.add_node("llm_processor", processor_node.process)
    
    # Define workflow flow
    workflow.add_edge(START, "browser_scraper")
    workflow.add_edge("browser_scraper", "llm_processor")
    workflow.add_edge("llm_processor", END)
    
    # Compile and return
    return workflow.compile()


class FlightScraperAgent:
    """LangGraph-based flight scraper agent using browser-use (local)."""
    
    def __init__(self):
        self.scraper_node = FlightScraperNode()
        self.processor_node = LLMProcessorNode()
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with nodes and edges."""
        workflow = StateGraph(FlightSearchState)
        
        # Add processing nodes
        workflow.add_node("browser_scraper", self.scraper_node.process)
        workflow.add_node("llm_processor", self.processor_node.process)
        
        # Define workflow flow
        workflow.add_edge(START, "browser_scraper")
        workflow.add_edge("browser_scraper", "llm_processor")
        workflow.add_edge("llm_processor", END)
        
        return workflow
    
    def search_flights(self, site: str, from_city: str, 
                      to_city: str, travel_date: str) -> Dict[str, Any]:
        """Execute the complete flight search workflow."""
        # Validate inputs
        if site not in get_supported_sites():
            return {
                "error": f"Unsupported site: {site}. Supported: {', '.join(get_supported_sites())}"
            }
        
        # Initial state
        initial_state = {
            "site": site.lower(),
            "from_city": from_city,
            "to_city": to_city,
            "travel_date": travel_date
        }
        
        try:
            # Execute the workflow
            result = self.app.invoke(initial_state)
            return result
            
        except Exception as e:
            return {
                "error": f"Workflow execution failed: {str(e)}",
                "success": False
            }
    
    def get_supported_sites(self) -> list:
        """Get list of supported flight booking sites."""
        return get_supported_sites()
