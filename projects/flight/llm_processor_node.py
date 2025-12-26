"""LLM processing node for flight data analysis using Groq."""

import json
import os
import re
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class LLMProcessorNode:
    """Node for processing and analyzing flight data using LLM."""
    
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.2-11b-text-preview",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2
        )
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a flight booking assistant analyzing scraped flight data. 

Your tasks:
1. Parse and structure the raw flight data
2. Identify the best options based on different criteria (price, duration, convenience)
3. Extract key information: airlines, times, prices, stops
4. Provide clear recommendations
5. Format everything in a user-friendly way

If the data is messy or incomplete, do your best to extract what you can and note any limitations."""),
            
            ("user", """
Flight Search Details:
- From: {from_city}
- To: {to_city} 
- Date: {travel_date}
- Site: {site_used}
- Success: {success}

Raw Browser Data:
{browser_result}

Please analyze this data and provide:
1. Structured flight information
2. Best options for different priorities (cheapest, fastest, best value)
3. Any important notes or warnings
4. Clear recommendations
""")
        ])
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process flight data using LLM analysis."""
        try:
            # Get LLM analysis
            analysis_response = self.llm.invoke(
                self.analysis_prompt.format(
                    from_city=state.get("from_city", ""),
                    to_city=state.get("to_city", ""),
                    travel_date=state.get("travel_date", ""),
                    site_used=state.get("site_used", ""),
                    success=state.get("success", False),
                    browser_result=state.get("browser_result", "")
                )
            )
            
            # Extract structured data from analysis
            structured_flights = self._extract_flight_data(analysis_response.content)
            recommendations = self._extract_recommendations(analysis_response.content)
            
            return {
                "llm_analysis": analysis_response.content,
                "structured_flights": structured_flights,
                "recommendations": recommendations,
                "processing_success": True
            }
            
        except Exception as e:
            return {
                "llm_analysis": f"LLM processing failed: {str(e)}",
                "structured_flights": [],
                "recommendations": [],
                "processing_success": False
            }
    
    def _extract_flight_data(self, analysis: str) -> List[Dict[str, str]]:
        """Extract structured flight data from LLM analysis."""
        flights = []
        
        # Pattern 1: Standard format with airline, times, and price
        patterns = [
            # Airline - Time to Time - Price
            r'(?:^|\n)\s*(?:\d+\.\s*)?([A-Za-z\s]+(?:Airways|Airlines|Air|Express|Jet)?)\s*[-–:]\s*(\d{1,2}:\d{2})\s*(?:to|->|→|–|-)\s*(\d{1,2}:\d{2})\s*[-–,]\s*([₹$€£]?\s*\d+[,\d]*)',
            # Airline: Time - Time, Price
            r'(?:^|\n)\s*(?:\d+\.\s*)?([A-Za-z\s]+(?:Airways|Airlines|Air|Express|Jet)?)\s*:\s*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\s*,?\s*([₹$€£]?\s*\d+[,\d]*)',
            # Airline | Time - Time | Price
            r'(?:^|\n)\s*(?:\d+\.\s*)?([A-Za-z\s]+(?:Airways|Airlines|Air|Express|Jet)?)\s*\|\s*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\s*\|\s*([₹$€£]?\s*\d+[,\d]*)',
            # Numbered list: 1. Airline Time-Time Price
            r'(?:^|\n)\s*\d+\.\s*([A-Za-z\s]+(?:Airways|Airlines|Air|Express|Jet)?)\s+(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\s+([₹$€£]?\s*\d+[,\d]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, analysis, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if len(match) >= 4:
                    airline = match[0].strip()
                    # Skip if airline is too short or looks like metadata
                    if len(airline) < 2 or airline.lower() in ['flight', 'option', 'from', 'to', 'date', 'site']:
                        continue
                    
                    flight_info = {
                        'airline': airline,
                        'departure_time': match[1].strip(),
                        'arrival_time': match[2].strip(), 
                        'price': match[3].strip()
                    }
                    
                    # Avoid duplicates
                    if flight_info not in flights:
                        flights.append(flight_info)
        
        # Pattern 2: Look for tabular or structured data with more details
        # Try to find lines with duration and stops info
        detail_pattern = r'([A-Za-z\s]+(?:Airways|Airlines|Air|Express|Jet)?)\s*[:\-|]\s*(\d{1,2}:\d{2})\s*(?:to|->|–|-)\s*(\d{1,2}:\d{2})\s*[,\-|]\s*(\d+h\s*\d*m?|\d+\s*hr|\d+\s*min)\s*[,\-|]?\s*(\d+\s*stop|non-stop|direct)?\s*[,\-|]\s*([₹$€£]?\s*\d+[,\d]*)'
        detail_matches = re.findall(detail_pattern, analysis, re.IGNORECASE)
        for match in detail_matches:
            airline = match[0].strip()
            if len(airline) < 2:
                continue
            
            flight_info = {
                'airline': airline,
                'departure_time': match[1].strip(),
                'arrival_time': match[2].strip(),
                'duration': match[3].strip() if match[3] else '',
                'stops': match[4].strip() if match[4] else '',
                'price': match[5].strip()
            }
            
            # Check if this is a duplicate or enhancement of existing flight
            is_duplicate = False
            for existing in flights:
                if (existing.get('airline') == flight_info['airline'] and 
                    existing.get('departure_time') == flight_info['departure_time']):
                    # Update with more details
                    existing.update(flight_info)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                flights.append(flight_info)
        
        # If still no flights found, try a more lenient search
        if not flights:
            # Look for any mention of prices with context
            price_context_pattern = r'([A-Za-z\s]{5,30})\s*[-:,]\s*([₹$€£]?\s*\d+[,\d]+)'
            price_matches = re.findall(price_context_pattern, analysis)
            
            for i, match in enumerate(price_matches[:10]):
                context = match[0].strip()
                price = match[1].strip()
                
                # Try to extract time if present in context
                time_in_context = re.findall(r'(\d{1,2}:\d{2})', context)
                
                if 'flight' in context.lower() or 'airline' in context.lower() or time_in_context:
                    flights.append({
                        'airline': context if len(context) < 50 else f'Flight {i+1}',
                        'departure_time': time_in_context[0] if len(time_in_context) > 0 else 'N/A',
                        'arrival_time': time_in_context[1] if len(time_in_context) > 1 else 'N/A',
                        'price': price
                    })
        
        return flights[:15]  # Limit to 15 flights
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract key recommendations from LLM analysis."""
        recommendations = []
        
        # Look for recommendation patterns
        rec_patterns = [
            r'recommend[^.]*\.',
            r'best\s+(?:option|choice|flight)[^.]*\.',
            r'(?:cheapest|fastest|most convenient)[^.]*\.',
            r'consider[^.]*\.',
            r'(?:tip|advice|suggestion)[^.]*\.'
        ]
        
        for pattern in rec_patterns:
            matches = re.findall(pattern, analysis, re.IGNORECASE)
            recommendations.extend([match.strip() for match in matches])
        
        # Also look for numbered recommendations
        numbered_recs = re.findall(r'\d+\.\s*([^.\n]+)', analysis)
        recommendations.extend(numbered_recs)
        
        # Clean and deduplicate
        clean_recs = []
        for rec in recommendations:
            rec = rec.strip()
            if len(rec) > 10 and rec not in clean_recs:  # Avoid very short or duplicate recs
                clean_recs.append(rec)
        
        return clean_recs[:8]  # Top 8 recommendations
