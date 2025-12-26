"""Browser automation node using browser-use library for flight scraping."""

import asyncio
import os
from typing import Any, Dict

from browser_use import Agent
from langchain_openai import ChatOpenAI
from pydantic import ConfigDict, Field

from flight_sites_config import get_site_config


class ChatOpenAIWithProvider(ChatOpenAI):
    """ChatOpenAI wrapper with provider attribute for browser-use compatibility."""
    
    provider: str = Field(default="openai")
    
    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True
    )
    
    @property
    def model(self):
        """Return the model name dynamically."""
        return getattr(self, 'model_name', 'gpt-4o-mini')


class FlightScraperNode:
    """Node for browser automation using browser-use library (local version)."""
    
    def __init__(self):
        # Try to use OpenAI (better compatibility with browser-use)
        # If not available, fall back to Groq
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if openai_key:
            # Use OpenAI - best compatibility
            self.llm = ChatOpenAIWithProvider(
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0,
                provider="openai"
            )
        elif groq_key:
            # Use Groq with OpenAI-compatible endpoint
            self.llm = ChatOpenAIWithProvider(
                model="llama-3.3-70b-versatile",
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                temperature=0,
                provider="groq"
            )
        else:
            raise ValueError("Either OPENAI_API_KEY or GROQ_API_KEY must be set in .env")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser automation to search for flights."""
        site = state.get("site", "makemytrip")
        from_city = state.get("from_city", "")
        to_city = state.get("to_city", "")
        travel_date = state.get("travel_date", "")
        
        site_config = get_site_config(site)
        if not site_config:
            return {
                "browser_result": f"Unsupported site: {site}",
                "success": False,
                "site_used": site
            }
        
        # Create detailed task for the browser agent
        task = self._create_flight_search_task(
            site_config, from_city, to_city, travel_date
        )
        
        try:
            # Run browser automation asynchronously
            result = self._run_browser_agent(task)
            
            return {
                "browser_result": result,
                "success": True,
                "site_used": site_config["name"]
            }
            
        except Exception as e:
            return {
                "browser_result": f"Browser automation failed: {str(e)}",
                "success": False,
                "site_used": site
            }
    
    def _create_flight_search_task(self, site_config: dict, from_city: str, 
                                 to_city: str, travel_date: str) -> str:
        """Create a detailed task description for the browser agent."""
        return f"""Search for flights from {from_city} to {to_city} on {travel_date} at {site_config['url']}.

Fill in the flight search form and click search. Wait for results. Extract flight details: airline, times, price, duration, stops. Return formatted list of all flights found."""
    
    def _run_browser_agent(self, task: str) -> str:
        """Run the browser agent with async-compatible LLM."""
        try:
            print("DEBUG: Creating browser agent...")
            # Create agent with async-compatible LLM and better configuration
            agent = Agent(
                task=task,
                llm=self.llm,
                max_failures=3,
                retry_delay=1,
                max_actions_per_step=5
            )
            
            print("DEBUG: Running browser agent...")
            # Run the agent synchronously
            result = asyncio.run(self._async_run_agent(agent))
            
            print(f"DEBUG: Result type: {type(result)}")
            print(f"DEBUG: Result value: {result}")
            
            # Extract the actual content from the result
            if result:
                # browser-use returns AgentHistoryList, try different extraction methods
                result_str = None
                
                # Method 1: Check if it's a list-like object with history
                if hasattr(result, 'final_result'):
                    print("DEBUG: Extracting via final_result()")
                    result_str = str(result.final_result())
                elif hasattr(result, '__iter__') and not isinstance(result, str):
                    print("DEBUG: Extracting from iterable")
                    # Try to get the last item's result
                    try:
                        items = list(result)
                        if items:
                            last_item = items[-1]
                            if hasattr(last_item, 'result'):
                                result_str = str(last_item.result)
                            elif hasattr(last_item, 'model_output'):
                                result_str = str(last_item.model_output)
                    except Exception as e:
                        print(f"DEBUG: Error extracting from iterable: {e}")
                
                # Method 2: Try standard attributes
                if not result_str:
                    if hasattr(result, 'content'):
                        print("DEBUG: Extracting via content")
                        result_str = str(result.content)
                    elif hasattr(result, 'text'):
                        print("DEBUG: Extracting via text")
                        result_str = str(result.text)
                
                # Method 3: Just stringify
                if not result_str:
                    print("DEBUG: Using str() conversion")
                    result_str = str(result)
                
                print(f"DEBUG: Extracted result length: {len(result_str)}")
                
                # Check if we got meaningful data
                if result_str and len(result_str) > 50:
                    return result_str
                else:
                    return f"Browser completed but extracted data was too short: {result_str}"
            else:
                return "No results returned from browser agent"
            
        except Exception as e:
            import traceback
            full_trace = traceback.format_exc()
            print(f"DEBUG: Exception occurred: {full_trace}")
            error_msg = str(e)
            # Don't include full traceback in user output, just the error
            if "consecutive failures" in error_msg.lower():
                return f"Browser automation failed after multiple attempts. The website may have protection mechanisms or the task was too complex. Error: {error_msg}"
            return f"Browser automation encountered an issue: {error_msg}"
    
    async def _async_run_agent(self, agent):
        """Async helper method to run the browser agent."""
        try:
            # Try async run first
            return await agent.run()
        except AttributeError:
            # Fallback to sync run if async not available
            return agent.run()
