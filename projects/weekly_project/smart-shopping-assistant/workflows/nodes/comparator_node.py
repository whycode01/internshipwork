"""
Comparator and Notification Nodes for Smart Shopping Assistant
Handles product comparison and smart notifications
"""

import os
import sys
from typing import Dict, List, Any, Optional
from groq import Groq
import json
from datetime import datetime
from difflib import SequenceMatcher
import statistics

# Add absolute path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from workflows.states.workflow_states import WorkflowState, update_state_step, log_error

# Import notification service with error handling
try:
    from services.notification_service import NotificationService
    NOTIFICATION_SERVICE_AVAILABLE = True
except ImportError:
    NOTIFICATION_SERVICE_AVAILABLE = False
    print("⚠️ NotificationService not available")

class ComparatorNode:
    """Node for intelligent product comparison and matching"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute product comparison and analysis"""
        try:
            state = update_state_step(state, "comparison")
            
            validated_products = state["validation"]["validated_products"]
            user_preferences = state["search_planning"]["user_preferences"]
            
            if not validated_products:
                state["workflow_status"] = "comparison_completed"
                return state
            
            # Match similar products across sites
            matched_products = await self.match_similar_products(validated_products)
            
            # Generate price comparisons
            price_comparisons = self.generate_price_comparisons(matched_products)
            
            # Identify best deals
            best_deals = await self.identify_best_deals(validated_products, user_preferences)
            
            # Calculate product similarities
            similarities = self.calculate_product_similarities(validated_products)
            
            # Generate comparison metrics
            metrics = self.generate_comparison_metrics(validated_products)
            
            # Calculate recommendation score
            recommendation_score = await self.calculate_recommendation_score(validated_products, user_preferences)
            
            # Update comparison state
            state["comparison"]["matched_products"] = matched_products
            state["comparison"]["price_comparisons"] = price_comparisons
            state["comparison"]["best_deals"] = best_deals
            state["comparison"]["product_similarities"] = similarities
            state["comparison"]["comparison_metrics"] = metrics
            state["comparison"]["recommendation_score"] = recommendation_score
            state["comparison"]["comparison_timestamp"] = datetime.now().isoformat()
            
            state["workflow_status"] = "comparison_completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Comparison failed: {str(e)}", "comparison")
            state["workflow_status"] = "comparison_failed"
            return state
    
    async def match_similar_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match similar products across different sites"""
        matched_groups = []
        processed_indices = set()
        
        for i, product1 in enumerate(products):
            if i in processed_indices:
                continue
            
            group = {
                "primary_product": product1,
                "similar_products": [],
                "sites": [product1.get("site", "")],
                "price_range": {"min": None, "max": None, "avg": None},
                "best_price": None,
                "best_rating": None
            }
            
            # Find similar products
            for j, product2 in enumerate(products[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                
                similarity = await self.calculate_product_similarity(product1, product2)
                
                if similarity > 0.7:  # Threshold for considering products similar
                    group["similar_products"].append({
                        "product": product2,
                        "similarity": similarity
                    })
                    group["sites"].append(product2.get("site", ""))
                    processed_indices.add(j)
            
            # Calculate group metrics
            all_products = [product1] + [sp["product"] for sp in group["similar_products"]]
            group["price_range"] = self.calculate_group_price_range(all_products)
            group["best_price"] = self.find_best_price(all_products)
            group["best_rating"] = self.find_best_rating(all_products)
            
            matched_groups.append(group)
            processed_indices.add(i)
        
        return matched_groups
    
    async def calculate_product_similarity(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> float:
        """Calculate similarity between two products using AI"""
        try:
            prompt = f"""
            Calculate similarity (0.0 to 1.0) between these two products:
            
            Product 1: "{product1.get('name', '')}"
            Category 1: "{product1.get('category', '')}"
            Brand 1: "{product1.get('brand', '')}"
            
            Product 2: "{product2.get('name', '')}"
            Category 2: "{product2.get('category', '')}"
            Brand 2: "{product2.get('brand', '')}"
            
            Consider:
            - Product name similarity
            - Category match
            - Brand match
            - Feature overlap
            
            Return only a float number between 0.0 and 1.0, no other text.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at calculating product similarity. Always return only a float number."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=10
            )
            
            similarity = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            # Fallback to name similarity
            name_sim = SequenceMatcher(None, 
                                     product1.get("name", "").lower(), 
                                     product2.get("name", "").lower()).ratio()
            return name_sim
    
    def generate_price_comparisons(self, matched_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate price comparison data"""
        comparisons = []
        
        for group in matched_groups:
            if len(group["similar_products"]) > 0:
                all_products = [group["primary_product"]] + [sp["product"] for sp in group["similar_products"]]
                
                price_data = []
                for product in all_products:
                    price_str = product.get("price", "")
                    if price_str and "₹" in price_str:
                        try:
                            price_num = int(price_str.replace("₹", "").replace(",", ""))
                            price_data.append({
                                "site": product.get("site", ""),
                                "price": price_num,
                                "product_name": product.get("name", ""),
                                "url": product.get("url", ""),
                                "rating": product.get("rating", "")
                            })
                        except:
                            pass
                
                if len(price_data) > 1:
                    # Sort by price
                    price_data.sort(key=lambda x: x["price"])
                    
                    # Calculate savings
                    min_price = price_data[0]["price"]
                    max_price = price_data[-1]["price"]
                    savings = max_price - min_price
                    savings_percent = (savings / max_price) * 100 if max_price > 0 else 0
                    
                    comparisons.append({
                        "product_group": group["primary_product"]["name"],
                        "prices": price_data,
                        "min_price": min_price,
                        "max_price": max_price,
                        "savings": savings,
                        "savings_percent": round(savings_percent, 1),
                        "best_deal": price_data[0]
                    })
        
        return comparisons
    
    async def identify_best_deals(self, products: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify best deals based on user preferences"""
        priority = user_preferences.get("priority", "price")
        deals = []
        
        for product in products:
            deal_score = await self.calculate_deal_score(product, priority)
            
            if deal_score > 0.7:  # Threshold for good deals
                deals.append({
                    "product": product,
                    "deal_score": deal_score,
                    "deal_type": self.identify_deal_type(product, deal_score),
                    "recommendation_reason": await self.generate_recommendation_reason(product, deal_score, priority)
                })
        
        # Sort by deal score
        deals.sort(key=lambda x: x["deal_score"], reverse=True)
        
        return deals[:5]  # Return top 5 deals
    
    async def calculate_deal_score(self, product: Dict[str, Any], priority: str) -> float:
        """Calculate deal score for a product"""
        score = 0.0
        
        # Base score from relevance
        relevance = product.get("relevance_score", 0.5)
        score += relevance * 0.3
        
        # Rating contribution
        try:
            rating = float(product.get("rating", "4.0"))
            rating_score = rating / 5.0
            score += rating_score * 0.3
        except:
            score += 0.24  # Default rating score
        
        # Price competitiveness (assume lower price is better for now)
        price_str = product.get("price", "")
        if price_str and "₹" in price_str:
            try:
                price = int(price_str.replace("₹", "").replace(",", ""))
                # Normalize price score (this is simplified)
                if price < 1000:
                    price_score = 1.0
                elif price < 5000:
                    price_score = 0.8
                elif price < 20000:
                    price_score = 0.6
                else:
                    price_score = 0.4
                score += price_score * 0.2
            except:
                score += 0.1
        
        # Availability and site reliability
        site = product.get("site", "")
        if site in ["amazon.in", "flipkart.com"]:
            score += 0.2
        elif site in ["myntra.com", "ajio.com"]:
            score += 0.15
        
        return min(1.0, score)
    
    def identify_deal_type(self, product: Dict[str, Any], deal_score: float) -> str:
        """Identify the type of deal"""
        if deal_score > 0.9:
            return "Excellent Deal"
        elif deal_score > 0.8:
            return "Great Deal"
        elif deal_score > 0.7:
            return "Good Deal"
        else:
            return "Regular Price"
    
    async def generate_recommendation_reason(self, product: Dict[str, Any], deal_score: float, priority: str) -> str:
        """Generate AI-powered recommendation reason"""
        try:
            prompt = f"""
            Generate a brief recommendation reason for this product:
            
            Product: "{product.get('name', '')}"
            Price: "{product.get('price', '')}"
            Rating: "{product.get('rating', '')}"
            Site: "{product.get('site', '')}"
            Deal Score: {deal_score}
            User Priority: {priority}
            
            Generate a concise reason (1-2 sentences) why this is recommended.
            Focus on the user's priority and the deal score.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a shopping assistant. Generate brief, helpful recommendation reasons."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback recommendation
            if deal_score > 0.8:
                return f"Excellent value for money with {product.get('rating', 'good')} rating."
            else:
                return f"Good option based on your {priority} preference."
    
    def calculate_group_price_range(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate price range for a group of similar products"""
        prices = []
        for product in products:
            price_str = product.get("price", "")
            if price_str and "₹" in price_str:
                try:
                    price = int(price_str.replace("₹", "").replace(",", ""))
                    prices.append(price)
                except:
                    pass
        
        if prices:
            return {
                "min": min(prices),
                "max": max(prices),
                "avg": int(statistics.mean(prices))
            }
        
        return {"min": None, "max": None, "avg": None}
    
    def find_best_price(self, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find product with best price"""
        best_product = None
        best_price = float('inf')
        
        for product in products:
            price_str = product.get("price", "")
            if price_str and "₹" in price_str:
                try:
                    price = int(price_str.replace("₹", "").replace(",", ""))
                    if price < best_price:
                        best_price = price
                        best_product = product
                except:
                    pass
        
        return best_product
    
    def find_best_rating(self, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find product with best rating"""
        best_product = None
        best_rating = 0.0
        
        for product in products:
            try:
                rating = float(product.get("rating", "0"))
                if rating > best_rating:
                    best_rating = rating
                    best_product = product
            except:
                pass
        
        return best_product
    
    def calculate_product_similarities(self, products: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate similarity matrix for all products"""
        similarities = {}
        
        for i, product1 in enumerate(products):
            for j, product2 in enumerate(products[i+1:], start=i+1):
                key = f"{i}-{j}"
                similarity = SequenceMatcher(None, 
                                           product1.get("name", "").lower(), 
                                           product2.get("name", "").lower()).ratio()
                similarities[key] = similarity
        
        return similarities
    
    def generate_comparison_metrics(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overall comparison metrics"""
        if not products:
            return {}
        
        # Site distribution
        sites = {}
        for product in products:
            site = product.get("site", "unknown")
            sites[site] = sites.get(site, 0) + 1
        
        # Category distribution
        categories = {}
        for product in products:
            category = product.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        
        # Price statistics
        prices = []
        for product in products:
            price_str = product.get("price", "")
            if price_str and "₹" in price_str:
                try:
                    price = int(price_str.replace("₹", "").replace(",", ""))
                    prices.append(price)
                except:
                    pass
        
        price_stats = {}
        if prices:
            price_stats = {
                "min": min(prices),
                "max": max(prices),
                "avg": int(statistics.mean(prices)),
                "median": int(statistics.median(prices))
            }
        
        # Rating statistics
        ratings = []
        for product in products:
            try:
                rating = float(product.get("rating", "0"))
                if rating > 0:
                    ratings.append(rating)
            except:
                pass
        
        rating_stats = {}
        if ratings:
            rating_stats = {
                "avg": round(statistics.mean(ratings), 1),
                "max": max(ratings),
                "min": min(ratings)
            }
        
        return {
            "total_products": len(products),
            "site_distribution": sites,
            "category_distribution": categories,
            "price_statistics": price_stats,
            "rating_statistics": rating_stats
        }
    
    async def calculate_recommendation_score(self, products: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> float:
        """Calculate overall recommendation score for the search results"""
        if not products:
            return 0.0
        
        # Average relevance score
        relevance_scores = [p.get("relevance_score", 0.5) for p in products]
        avg_relevance = statistics.mean(relevance_scores)
        
        # Data quality score
        quality_scores = []
        for product in products:
            quality = 0.0
            if product.get("name") and len(product["name"]) > 5:
                quality += 0.25
            if product.get("price") and "₹" in product["price"]:
                quality += 0.25
            if product.get("rating") and product["rating"] != "4.0":
                quality += 0.25
            if product.get("url") and "http" in product["url"]:
                quality += 0.25
            quality_scores.append(quality)
        
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.0
        
        # Diversity score (variety of sites and prices)
        sites = set(p.get("site", "") for p in products)
        diversity_score = min(1.0, len(sites) / 4.0)  # Normalize by max expected sites
        
        # Combine scores
        overall_score = (avg_relevance * 0.5 + avg_quality * 0.3 + diversity_score * 0.2)
        
        return round(overall_score, 2)

class NotificationNode:
    """Node for intelligent notification management"""
    
    def __init__(self):
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from services.notification_service import NotificationService
        self.notification_service = NotificationService()
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute notification processing"""
        try:
            state = update_state_step(state, "notification")
            
            best_deals = state["comparison"]["best_deals"]
            user_preferences = state["search_planning"]["user_preferences"]
            
            # Generate alert triggers
            alert_triggers = self.generate_alert_triggers(best_deals, user_preferences)
            
            # Process notifications
            notification_queue = []
            sent_notifications = []
            
            for trigger in alert_triggers:
                notification = await self.create_notification(trigger, state)
                if notification:
                    notification_queue.append(notification)
                    
                    # Send notification if conditions are met
                    if self.should_send_notification(trigger, user_preferences):
                        success = await self.send_notification(notification)
                        if success:
                            sent_notifications.append(notification)
            
            # Update notification state
            state["notification"]["alert_triggers"] = alert_triggers
            state["notification"]["user_preferences"] = user_preferences
            state["notification"]["notification_queue"] = notification_queue
            state["notification"]["sent_notifications"] = sent_notifications
            state["notification"]["notification_status"] = "completed"
            state["notification"]["alert_timestamp"] = datetime.now().isoformat()
            
            state["workflow_status"] = "notification_completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Notification processing failed: {str(e)}", "notification")
            state["workflow_status"] = "notification_failed"
            return state
    
    def generate_alert_triggers(self, best_deals: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alert triggers based on deals and preferences"""
        triggers = []
        
        for deal in best_deals:
            product = deal["product"]
            deal_score = deal["deal_score"]
            
            trigger = {
                "trigger_id": f"deal_{int(datetime.now().timestamp())}_{len(triggers)}",
                "trigger_type": "price_deal",
                "product": product,
                "deal_score": deal_score,
                "deal_type": deal["deal_type"],
                "recommendation_reason": deal["recommendation_reason"],
                "priority": self.calculate_trigger_priority(deal_score),
                "created_at": datetime.now().isoformat()
            }
            
            triggers.append(trigger)
        
        return triggers
    
    def calculate_trigger_priority(self, deal_score: float) -> str:
        """Calculate notification priority based on deal score"""
        if deal_score > 0.9:
            return "high"
        elif deal_score > 0.8:
            return "medium"
        else:
            return "low"
    
    async def create_notification(self, trigger: Dict[str, Any], state: WorkflowState) -> Optional[Dict[str, Any]]:
        """Create notification from trigger"""
        try:
            product = trigger["product"]
            query = state["search_planning"]["query"]
            
            notification = {
                "id": trigger["trigger_id"],
                "title": f"Great Deal Found: {product.get('name', 'Product')[:50]}...",
                "message": self.generate_notification_message(trigger, query),
                "type": "deal_alert",
                "priority": trigger["priority"],
                "product_data": product,
                "deal_info": {
                    "score": trigger["deal_score"],
                    "type": trigger["deal_type"],
                    "reason": trigger["recommendation_reason"]
                },
                "created_at": datetime.now().isoformat(),
                "read": False
            }
            
            return notification
            
        except Exception as e:
            print(f"Failed to create notification: {e}")
            return None
    
    def generate_notification_message(self, trigger: Dict[str, Any], query: str) -> str:
        """Generate notification message"""
        product = trigger["product"]
        deal_type = trigger["deal_type"]
        reason = trigger["recommendation_reason"]
        
        message = f"""
🎉 {deal_type} Alert for "{query}"!

📱 {product.get('name', 'Product')[:100]}
💰 Price: {product.get('price', 'N/A')}
⭐ Rating: {product.get('rating', 'N/A')}/5
🏪 Available on: {product.get('site', 'Unknown')}

💡 Why we recommend: {reason}

🔗 View Product: {product.get('url', '')}
        """.strip()
        
        return message
    
    def should_send_notification(self, trigger: Dict[str, Any], user_preferences: Dict[str, Any]) -> bool:
        """Determine if notification should be sent"""
        # For now, send all high priority notifications
        return trigger["priority"] in ["high", "medium"]
    
    async def send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send notification using notification service"""
        try:
            # Save in-app notification
            success = self.notification_service.save_in_app_notification(
                notification["title"],
                notification["message"],
                notification["type"],
                notification.get("product_data", {}).get("id")
            )
            
            return success
            
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False


class NotificationNode:
    """Node for handling notifications and alerts"""
    
    def __init__(self):
        pass
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute notification processing"""
        try:
            state = update_state_step(state, "notification")
            
            # For now, just mark as complete (notification logic can be added later)
            state["notification"]["notification_status"] = "completed"
            state["notification"]["alert_timestamp"] = datetime.now().isoformat()
            
            state["workflow_status"] = "completed"
            
            return state
            
        except Exception as e:
            state = log_error(state, f"Notification failed: {str(e)}", "notification")
            state["workflow_status"] = "notification_failed"
            return state