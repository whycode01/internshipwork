"""Main application entry point for the flight scraper agent."""

import os
import sys

from dotenv import load_dotenv

from flight_agent import FlightScraperAgent
from flight_sites_config import get_supported_sites


def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("FLIGHT SCRAPER AGENT")
    print("=" * 60)
    print("LangGraph + Browser-Use (Local) + Groq LLM")
    print(f"Supported sites: {', '.join(get_supported_sites())}")
    print("=" * 60)


def validate_environment():
    """Validate required environment variables."""
    required_vars = ["GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {missing_vars}")
        print("Please check your .env file and add the missing variables.")
        return False
    
    print("SUCCESS: Environment variables validated")
    return True


def get_user_input():
    """Get flight search parameters from user."""
    print("\nEnter flight search details:")
    
    # Site selection
    sites = get_supported_sites()
    while True:
        site = input(f"Select site ({'/'.join(sites)}) or 'quit': ").strip().lower()
        if site == 'quit':
            return None
        if site in sites:
            break
        print(f"Please enter one of: {', '.join(sites)}")
    
    # Flight details
    from_city = input("From city: ").strip()
    to_city = input("To city: ").strip()
    travel_date = input("Travel date (DD/MM/YYYY or DD-MMM-YYYY): ").strip()
    
    if not all([from_city, to_city, travel_date]):
        print("ERROR: All fields are required!")
        return None
    
    return {
        "site": site,
        "from_city": from_city,
        "to_city": to_city,
        "travel_date": travel_date
    }


def display_results(result: dict):
    """Display flight search results."""
    print("\n" + "=" * 70)
    print("FLIGHT SEARCH RESULTS")
    print("=" * 70)
    
    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return
    
    # Basic info
    success = result.get("success", False)
    site_used = result.get("site_used", "Unknown")
    
    print(f"Site: {site_used}")
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        print(f"Reason: {result.get('browser_result', 'Unknown error')}")
        return
    
    # Show raw browser results if no structured data
    browser_result = result.get("browser_result", "")
    
    # Structured flights
    flights = result.get("structured_flights", [])
    if flights:
        print(f"\nFound {len(flights)} flights:")
        print("-" * 70)
        
        for i, flight in enumerate(flights, 1):
            airline = flight.get('airline', 'N/A')
            departure = flight.get('departure_time', 'N/A')
            arrival = flight.get('arrival_time', 'N/A')
            price = flight.get('price', 'N/A')
            duration = flight.get('duration', '')
            stops = flight.get('stops', '')
            
            print(f"\n{i}. {airline}")
            print(f"   Departure: {departure}")
            print(f"   Arrival:   {arrival}")
            if duration:
                print(f"   Duration:  {duration}")
            if stops:
                print(f"   Stops:     {stops}")
            print(f"   Price:     {price}")
    else:
        # If no structured flights, show the raw browser data
        print("\nRaw Flight Data:")
        print("-" * 70)
        if browser_result and len(browser_result) > 100:
            print(browser_result)
        else:
            print("No flight data extracted. The browser may not have loaded results properly.")
    
    # LLM Analysis
    analysis = result.get("llm_analysis", "")
    if analysis and result.get("processing_success"):
        # Only show analysis if it's different from structured data or if there's no structured data
        if not flights or len(analysis) > 500:
            print(f"\n{'AI Analysis:':^70}")
            print("-" * 70)
            print(analysis)
    
    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\n{'Key Recommendations:':^70}")
        print("-" * 70)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    print("\n" + "=" * 70)


def main():
    """Main application function."""
    # Load environment variables
    load_dotenv()
    
    # Print banner
    print_banner()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Initialize agent
    try:
        print("\nInitializing flight scraper agent...")
        agent = FlightScraperAgent()
        print("SUCCESS: Agent initialized successfully!")
    except Exception as e:
        print(f"ERROR: Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            search_params = get_user_input()
            
            if search_params is None:
                print("\nGoodbye!")
                break
            
            # Execute search
            print(f"\nSearching flights from {search_params['from_city']} "
                  f"to {search_params['to_city']} on {search_params['travel_date']} "
                  f"using {search_params['site']}...")
            
            result = agent.search_flights(**search_params)
            
            # Display results
            display_results(result)
            
            # Ask if user wants to continue
            continue_search = input("\nSearch again? (y/n): ").strip().lower()
            if continue_search not in ['y', 'yes']:
                print("\nGoodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nERROR: An unexpected error occurred: {e}")
            continue


if __name__ == "__main__":
    main()
