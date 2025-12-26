"""
Data Extractor and Validator Nodes for Smart Shopping Assistant
Handles AI-powered data extraction and validation
"""

import os
import sys
import re
from typing import Dict, List, Any, Optional
from groq import Groq
import json
from datetime import datetime
from difflib import SequenceMatcher

# Add absolute path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from workflows.states.workflow_states import WorkflowState, update_state_step, log_error

class DataExtractorNode:
    """Node for AI-powered data extraction and enhancement"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute data extraction and enhancement"""
        try:
            state = update_state_step(state, "data_extraction")
            
            raw_products = state["data_extraction"]["extracted_products"]
            query = state["search_planning"]["query"]
            
            # Enhance product data using AI
            enhanced_products = []
            
            for product in raw_products:
                enhanced_product = await self.enhance_product_data(product, query)
                if enhanced_product:
                    enhanced_products.append(enhanced_product)
            
            # Update state with enhanced data
            state["data_extraction"]["extracted_products"] = enhanced_products
            state["data_extraction"]["structured_data"] = {
                "total_products": len(enhanced_products),
                "sites_covered": list(set(p.get("site", "") for p in enhanced_products)),
                "price_range": self.calculate_price_range(enhanced_products),
                "categories": self.extract_categories(enhanced_products)
            }
            
            # Calculate confidence score
            confidence = self.calculate_confidence_score(enhanced_products)
            state["data_extraction"]["confidence_score"] = confidence
            
            state["workflow_status"] = "extraction_completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Data extraction failed: {str(e)}", "data_extraction")
            state["workflow_status"] = "extraction_failed"
            return state
    
    async def enhance_product_data(self, product: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
        """Enhance individual product data using AI"""
        try:
            # Clean and validate price
            price_str = product.get("price", "")
            cleaned_price = self.clean_price(price_str)
            
            # Clean and validate rating
            rating_str = product.get("rating", "")
            cleaned_rating = self.clean_rating(rating_str)
            
            # Clean product name
            name = product.get("name", "").strip()
            if not name or len(name) < 3:
                return None
            
            # Calculate relevance score using AI (with fallback)
            try:
                relevance_score = await self.calculate_relevance(name, query)
            except Exception as e:
                print(f"AI relevance calculation failed, using fallback: {e}")
                relevance_score = SequenceMatcher(None, name.lower(), query.lower()).ratio()
            
            # Get category (with fallback)
            try:
                category = await self.identify_category(name)
            except Exception as e:
                print(f"AI category identification failed, using fallback: {e}")
                category = "other"
            
            # Get features (with fallback)
            try:
                key_features = await self.extract_features(name)
            except Exception as e:
                print(f"AI feature extraction failed, using fallback: {e}")
                key_features = self.extract_features_fallback(name)
            
            enhanced_product = {
                "name": name,
                "price": cleaned_price,
                "rating": cleaned_rating,
                "url": product.get("url", ""),
                "availability": product.get("availability", "Available"),
                "site": product.get("site", ""),
                "relevance_score": relevance_score,
                "extracted_at": datetime.now().isoformat(),
                "category": category,
                "brand": self.extract_brand(name),
                "key_features": key_features
            }
            
            return enhanced_product
            
        except Exception as e:
            print(f"Product enhancement failed: {e}")
            # Return a basic enhanced version instead of original
            return {
                "name": product.get("name", "").strip(),
                "price": self.clean_price(product.get("price", "")),
                "rating": self.clean_rating(product.get("rating", "")),
                "url": product.get("url", ""),
                "availability": product.get("availability", "Available"),
                "site": product.get("site", ""),
                "relevance_score": 0.5,  # Default relevance
                "extracted_at": datetime.now().isoformat(),
                "category": "other",
                "brand": self.extract_brand(product.get("name", "")),
                "key_features": self.extract_features_fallback(product.get("name", ""))
            }
    
    def clean_price(self, price_str: str) -> str:
        """Clean and standardize price information"""
        if not price_str or price_str in ["N/A", "Check on site", ""]:
            return "Price not available"
        
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+', str(price_str).replace(',', ''))
        if price_match:
            price_num = price_match.group().replace(',', '')
            try:
                price_int = int(price_num)
                # Validate reasonable price range
                if 10 <= price_int <= 10000000:
                    return f"₹{price_int:,}"
                else:
                    return "Price not available"
            except ValueError:
                return "Price not available"
        
        return "Price not available"
    
    def clean_rating(self, rating_str: str) -> str:
        """Clean and standardize rating information"""
        if not rating_str:
            return "4.0"
        
        # Extract numeric rating
        rating_match = re.search(r'(\d+\.?\d*)', str(rating_str))
        if rating_match:
            try:
                rating_float = float(rating_match.group(1))
                if 0 <= rating_float <= 5:
                    return f"{rating_float:.1f}"
            except ValueError:
                pass
        
        return "4.0"
    
    async def calculate_relevance(self, product_name: str, query: str) -> float:
        """Calculate product relevance to search query using AI"""
        try:
            prompt = f"""
            Calculate the relevance score (0.0 to 1.0) of this product to the search query:
            
            Product: "{product_name}"
            Query: "{query}"
            
            Consider:
            - Keyword matching
            - Semantic similarity
            - Product category alignment
            - Brand relevance
            
            Return only a float number between 0.0 and 1.0, no other text.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at calculating product relevance scores. Always return only a float number."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=10,
                timeout=5  # Add timeout
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            
        except Exception as e:
            print(f"AI relevance calculation failed: {e}")
            # Fallback to simple text similarity
            similarity = SequenceMatcher(None, product_name.lower(), query.lower()).ratio()
            return similarity
    
    async def identify_category(self, product_name: str) -> str:
        """Identify product category using AI"""
        try:
            prompt = f"""
            Identify the product category for: "{product_name}"
            
            Choose from: electronics, clothing, books, home, sports, beauty, accessories, other
            
            Return only the category name, no other text.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at product categorization. Always return only the category name."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=20,
                timeout=5  # Add timeout
            )
            
            category = response.choices[0].message.content.strip().lower()
            valid_categories = ["electronics", "clothing", "books", "home", "sports", "beauty", "accessories"]
            
            return category if category in valid_categories else "other"
            
        except Exception as e:
            print(f"AI category identification failed: {e}")
            return "other"
    
    def extract_brand(self, product_name: str) -> str:
        """Extract brand name from product title"""
        # Common brand patterns
        common_brands = [
            "samsung", "apple", "oneplus", "xiaomi", "realme", "oppo", "vivo",
            "nike", "adidas", "puma", "reebok", "under armour",
            "levi's", "h&m", "zara", "uniqlo", "gap",
            "sony", "lg", "panasonic", "philips", "bosch"
        ]
        
        name_lower = product_name.lower()
        for brand in common_brands:
            if brand in name_lower:
                return brand.title()
        
        # Extract first word as potential brand
        words = product_name.split()
        if words and len(words[0]) > 2:
            return words[0]
        
        return "Unknown"
    
    async def extract_features(self, product_name: str) -> List[str]:
        """Extract key features from product name using AI"""
        try:
            prompt = f"""
            Extract key features from this product name: "{product_name}"
            
            Return a JSON array of 3-5 key features/specifications mentioned.
            Example: ["Wireless", "Bluetooth", "Noise Cancelling", "20Hr Battery"]
            
            Return only valid JSON array, no other text.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at extracting product features. Always return only a JSON array."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=100,
                timeout=5  # Add timeout
            )
            
            features_text = response.choices[0].message.content.strip()
            if features_text.startswith('[') and features_text.endswith(']'):
                features = json.loads(features_text)
                return features[:5]  # Limit to 5 features
            
        except Exception as e:
            print(f"AI feature extraction failed: {e}")
        
        # Fallback feature extraction
        return self.extract_features_fallback(product_name)
    
    def extract_features_fallback(self, product_name: str) -> List[str]:
        """Fallback feature extraction using keywords"""
        features = []
        name_lower = product_name.lower()
        
        feature_keywords = {
            "wireless": "Wireless",
            "bluetooth": "Bluetooth",
            "smart": "Smart",
            "hd": "HD",
            "4k": "4K",
            "waterproof": "Waterproof",
            "fast charging": "Fast Charging",
            "dual camera": "Dual Camera",
            "fingerprint": "Fingerprint",
            "voice control": "Voice Control"
        }
        
        for keyword, feature in feature_keywords.items():
            if keyword in name_lower:
                features.append(feature)
        
        return features[:3]  # Limit to 3 features
    
    def calculate_price_range(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate price range from products"""
        prices = []
        for product in products:
            price_str = product.get("price", "")
            if price_str and "₹" in price_str:
                try:
                    price_num = int(re.sub(r'[^\d]', '', price_str))
                    if price_num > 0:
                        prices.append(price_num)
                except:
                    pass
        
        if prices:
            return {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) // len(prices)
            }
        
        return {"min": 0, "max": 0, "avg": 0}
    
    def extract_categories(self, products: List[Dict[str, Any]]) -> List[str]:
        """Extract unique categories from products"""
        categories = set()
        for product in products:
            category = product.get("category", "other")
            if category:
                categories.add(category)
        return list(categories)
    
    def calculate_confidence_score(self, products: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for extracted data"""
        if not products:
            return 0.0
        
        total_score = 0.0
        count = 0
        
        for product in products:
            score = 0.0
            
            # Check data completeness
            if product.get("name") and len(product["name"]) > 3:
                score += 0.3
            if product.get("price") and "₹" in product["price"]:
                score += 0.3
            if product.get("rating") and product["rating"] != "4.0":
                score += 0.2
            if product.get("url") and "http" in product["url"]:
                score += 0.2
            
            total_score += score
            count += 1
        
        return round(total_score / count, 2) if count > 0 else 0.0

class ValidatorNode:
    """Node for data quality validation and duplicate detection"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute data validation"""
        try:
            state = update_state_step(state, "validation")
            
            products = state["data_extraction"]["extracted_products"]
            
            # Validate and clean products
            validated_products = []
            duplicate_products = []
            validation_errors = []
            
            for i, product in enumerate(products):
                # Basic validation
                is_valid, errors = self.validate_product(product)
                
                if not is_valid:
                    validation_errors.extend([f"Product {i+1}: {error}" for error in errors])
                    continue
                
                # Check for duplicates
                is_duplicate, similar_product = self.find_duplicate(product, validated_products)
                
                if is_duplicate:
                    duplicate_products.append({
                        "original": similar_product,
                        "duplicate": product,
                        "similarity": self.calculate_similarity(product, similar_product)
                    })
                else:
                    validated_products.append(product)
            
            # Sort by relevance score
            validated_products.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # Update validation state
            state["validation"]["validated_products"] = validated_products
            state["validation"]["duplicate_products"] = duplicate_products
            state["validation"]["validation_errors"] = validation_errors
            state["validation"]["quality_score"] = self.calculate_quality_score(validated_products)
            state["validation"]["missing_fields"] = self.identify_missing_fields(validated_products)
            state["validation"]["validation_timestamp"] = datetime.now().isoformat()
            
            state["workflow_status"] = "validation_completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Validation failed: {str(e)}", "validation")
            state["workflow_status"] = "validation_failed"
            return state
    
    def validate_product(self, product: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate individual product data"""
        errors = []
        
        # Required fields validation
        if not product.get("name") or len(product["name"].strip()) < 3:
            errors.append("Invalid or missing product name")
        
        if not product.get("url") or not ("http" in product["url"]):
            errors.append("Invalid or missing product URL")
        
        if not product.get("site"):
            errors.append("Missing site information")
        
        # Price validation
        price = product.get("price", "")
        if price and price != "Price not available":
            if not re.search(r'\d+', price):
                errors.append("Invalid price format")
        
        # Rating validation
        rating = product.get("rating", "")
        if rating:
            try:
                rating_float = float(rating)
                if not (0 <= rating_float <= 5):
                    errors.append("Rating out of valid range (0-5)")
            except ValueError:
                errors.append("Invalid rating format")
        
        return len(errors) == 0, errors
    
    def find_duplicate(self, product: Dict[str, Any], existing_products: List[Dict[str, Any]]) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Find duplicate products using similarity matching"""
        product_name = product.get("name", "").lower().strip()
        
        for existing in existing_products:
            existing_name = existing.get("name", "").lower().strip()
            
            # Calculate name similarity
            similarity = SequenceMatcher(None, product_name, existing_name).ratio()
            
            # Consider it duplicate if similarity > 0.8 and same site
            if (similarity > 0.8 and 
                product.get("site") == existing.get("site")):
                return True, existing
            
            # Also check if names are very similar (after removing common words)
            if self.are_products_similar(product_name, existing_name):
                return True, existing
        
        return False, None
    
    def are_products_similar(self, name1: str, name2: str) -> bool:
        """Check if two product names refer to the same product"""
        # Remove common stop words
        stop_words = {"for", "with", "by", "in", "on", "at", "and", "or", "the", "a", "an"}
        
        words1 = set(word for word in name1.split() if word.lower() not in stop_words)
        words2 = set(word for word in name2.split() if word.lower() not in stop_words)
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return False
        
        jaccard_similarity = intersection / union
        return jaccard_similarity > 0.6
    
    def calculate_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calculate overall similarity between two products"""
        name_sim = SequenceMatcher(None, 
                                 product1.get("name", "").lower(), 
                                 product2.get("name", "").lower()).ratio()
        
        # Add price similarity if both have valid prices
        price_sim = 0.0
        try:
            price1 = float(re.sub(r'[^\d]', '', product1.get("price", "0")))
            price2 = float(re.sub(r'[^\d]', '', product2.get("price", "0")))
            if price1 > 0 and price2 > 0:
                price_diff = abs(price1 - price2) / max(price1, price2)
                price_sim = 1.0 - price_diff
        except:
            pass
        
        # Weighted average
        return (name_sim * 0.8 + price_sim * 0.2)
    
    def calculate_quality_score(self, products: List[Dict[str, Any]]) -> float:
        """Calculate overall data quality score"""
        if not products:
            return 0.0
        
        total_score = 0.0
        for product in products:
            product_score = 0.0
            
            # Name quality (0-0.3)
            name = product.get("name", "")
            if name and len(name) > 10:
                product_score += 0.3
            elif name and len(name) > 5:
                product_score += 0.2
            elif name:
                product_score += 0.1
            
            # Price quality (0-0.3)
            price = product.get("price", "")
            if price and "₹" in price and re.search(r'\d+', price):
                product_score += 0.3
            elif price and price != "Price not available":
                product_score += 0.1
            
            # URL quality (0-0.2)
            url = product.get("url", "")
            if url and "http" in url and len(url) > 20:
                product_score += 0.2
            elif url:
                product_score += 0.1
            
            # Additional fields (0-0.2)
            if product.get("rating") and product["rating"] != "4.0":
                product_score += 0.1
            if product.get("category") and product["category"] != "other":
                product_score += 0.1
            
            total_score += product_score
        
        return round(total_score / len(products), 2)
    
    def identify_missing_fields(self, products: List[Dict[str, Any]]) -> List[str]:
        """Identify commonly missing fields across products"""
        missing_fields = []
        
        if not products:
            return ["No products to analyze"]
        
        # Check for missing fields
        total_products = len(products)
        
        # Count missing fields
        missing_counts = {
            "price": sum(1 for p in products if not p.get("price") or p["price"] == "Price not available"),
            "rating": sum(1 for p in products if not p.get("rating")),
            "category": sum(1 for p in products if not p.get("category") or p["category"] == "other"),
            "brand": sum(1 for p in products if not p.get("brand") or p["brand"] == "Unknown"),
            "features": sum(1 for p in products if not p.get("key_features") or len(p["key_features"]) == 0)
        }
        
        # Report fields missing in >50% of products
        for field, count in missing_counts.items():
            if count > total_products * 0.5:
                missing_fields.append(f"{field} missing in {count}/{total_products} products")
        
        return missing_fields


class ValidatorNode:
    """Node for validating extracted product data"""
    
    def __init__(self):
        pass
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute data validation"""
        try:
            state = update_state_step(state, "validation")
            
            # Get extracted products
            extracted_products = state["data_extraction"]["extracted_products"]
            
            # For now, just pass through the products (validation logic can be added later)
            validated_products = extracted_products
            
            # Update validation state
            state["validation"]["validated_products"] = validated_products
            state["validation"]["quality_score"] = 0.8  # Default quality score
            state["validation"]["validation_errors"] = []
            state["validation"]["missing_fields"] = []
            state["validation"]["validation_timestamp"] = datetime.now().isoformat()
            
            state["workflow_status"] = "validation_completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Validation failed: {str(e)}", "validation")
            state["workflow_status"] = "validation_failed"
            return state