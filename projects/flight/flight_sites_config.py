"""Flight booking sites configuration."""

FLIGHT_SITES = {
    "makemytrip": {
        "url": "https://www.makemytrip.com/flights/",
        "name": "MakeMyTrip",
        "strategy": "Navigate to MakeMyTrip flights page, enter departure city, destination city, select travel date, search flights and extract results"
    },
    "booking": {
        "url": "https://www.booking.com/flights/",
        "name": "Booking.com Flights",
        "strategy": "Go to Booking.com flights section, fill in from and to locations, choose travel dates, search for flights and get flight information"
    },
    "skyscanner": {
        "url": "https://www.skyscanner.com/",
        "name": "Skyscanner",
        "strategy": "Visit Skyscanner homepage, enter departure and arrival locations, select travel date, search flights and collect flight details"
    }
}

def get_site_config(site_name: str) -> dict:
    """Get configuration for a specific flight booking site."""
    return FLIGHT_SITES.get(site_name.lower(), {})

def get_supported_sites() -> list:
    """Get list of supported flight booking sites."""
    return list(FLIGHT_SITES.keys())
