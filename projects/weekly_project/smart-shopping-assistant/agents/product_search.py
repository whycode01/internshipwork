import os
from groq import Groq
from typing import Dict, List
import json
import re
from dotenv import load_dotenv

load_dotenv()

class ProductSearchAI:
    """AI-powered product search optimization using Groq"""
    
    def __init__(self):
        load_dotenv()
        
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                print("Warning: GROQ_API_KEY not found, disabling AI features")
                self.client = None
                self.model = None
                self.available = False
                return

            # Initialize Groq client (should work now with httpx 0.24.0)
            self.client = Groq(api_key=api_key)
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            self.available = True
            print("✅ ProductSearchAI initialized successfully")
        except Exception as e:
            print(f"Failed to initialize ProductSearchAI: {e}")
            print("Disabling AI features")
            self.client = None
            self.model = None
            self.available = False

    def normalize_product_data(self, products: List[Dict]) -> List[Dict]:
        """Normalize product data from different sources using AI"""
        if not self.available:
            print("AI not available, returning original data")
            return products
            
        prompt = f"""
        You are a product data normalization expert. 
        Normalize the following product data to have consistent fields:
        - name: standardized product name
        - price: numeric price in INR
        - rating: numeric rating out of 5
        - url: product URL
        - site: source website
        - availability: in_stock/out_of_stock
        
        Products data: {json.dumps(products)}
        
        Return only valid JSON array with normalized products.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a data normalization expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=2048,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return products
                
        except Exception as e:
            print(f"Error normalizing data: {e}")
            return products
    
    def generate_search_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions using AI"""
        if not self.available:
            # Return simple suggestions based on the query
            return [
                query,
                f"{query} alternative",
                f"best {query}",
                f"cheap {query}",
                f"{query} review"
            ]
            
        prompt = f"""
        Generate 5 relevant product search suggestions based on: "{query}"
        Consider:
        - Alternative product names
        - Related products
        - Popular variations
        - Brand alternatives
        
        Return only a JSON array of strings.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Generate search suggestions. Return only JSON array."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=512,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return [query]
                
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return [query]
    
    def recommend_alternatives(self, product_name: str, budget: float) -> List[Dict]:
        """Recommend alternative products within budget"""
        if not self.available:
            # Return basic recommendations
            return [
                {"name": f"{product_name} - Alternative 1", "estimated_price": budget * 0.8, "reason": "Budget-friendly option"},
                {"name": f"{product_name} - Alternative 2", "estimated_price": budget * 0.9, "reason": "Similar features"},
                {"name": f"{product_name} - Alternative 3", "estimated_price": budget * 0.7, "reason": "Value for money"}
            ]
            
        prompt = f"""
        Recommend 5 alternative products similar to "{product_name}" within budget of ₹{budget}.
        Consider:
        - Similar functionality
        - Better value for money
        - Popular alternatives
        - Different brands
        
        Return JSON array with: name, estimated_price, reason
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a shopping assistant. Provide product recommendations."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=1024,
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return []
                
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def analyze_price_trend(self, price_history: List[Dict]) -> Dict:
        """Analyze price trends using AI"""
        if not self.available:
            # Return basic analysis
            if not price_history:
                return {"trend": "unknown", "recommendation": "Monitor prices", "prediction": "Unable to predict", "confidence": "low"}
            
            prices = [item.get('price', 0) for item in price_history if item.get('price')]
            if len(prices) < 2:
                return {"trend": "stable", "recommendation": "Monitor prices", "prediction": "Stable pricing expected", "confidence": "medium"}
            
            trend = "increasing" if prices[-1] > prices[0] else "decreasing" if prices[-1] < prices[0] else "stable"
            return {"trend": trend, "recommendation": f"Price is {trend}", "prediction": f"Expect {trend} prices", "confidence": "medium"}
            
        prompt = f"""
        Analyze the following price history and provide insights:
        {json.dumps(price_history)}
        
        Provide analysis on:
        - Price trend (increasing/decreasing/stable)
        - Best time to buy
        - Price prediction for next week
        - Deal recommendation
        
        Return JSON with: trend, recommendation, prediction, confidence
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a price analysis expert. Provide actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=512,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"trend": "unknown", "recommendation": "Monitor prices"}
                
        except Exception as e:
            print(f"Error analyzing price trend: {e}")
            return {"trend": "unknown", "recommendation": "Monitor prices"}
