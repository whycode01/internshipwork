import asyncio
import schedule
import time
from datetime import datetime
from typing import List
from agents.browser_agent import BrowserAgent
from utils.notifications import NotificationManager
import logging

logger = logging.getLogger(__name__)

class PriceTracker:
    """Automated price tracking system"""
    
    def __init__(self, database):
        self.db = database
        try:
            self.browser_agent = BrowserAgent()
        except Exception as e:
            logger.warning(f"Failed to initialize BrowserAgent: {e}")
            self.browser_agent = None
        
        self.notification_manager = NotificationManager()
        self.is_running = False
    
    async def update_single_product_price(self, product_id: int) -> bool:
        """Update price for a single product"""
        try:
            if not self.browser_agent:
                logger.warning("BrowserAgent not available, skipping price update")
                return False
                
            product = self.db.get_product_by_id(product_id)
            if not product:
                return False
            
            # Get current price using browser agent
            result = await self.browser_agent.get_product_details(product.url)
            
            if 'error' in result:
                logger.error(f"Failed to get price for {product.name}: {result['error']}")
                return False
            
            new_price = self.extract_price_from_result(result)
            if new_price and new_price != product.current_price:
                old_price = product.current_price
                
                # Update database
                self.db.update_product_price(product_id, new_price)
                
                # Check for alerts
                await self.check_price_alerts(product, old_price, new_price)
                
                logger.info(f"Price updated for {product.name}: ₹{old_price} → ₹{new_price}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating price for product {product_id}: {e}")
            return False
    
    async def update_all_prices(self) -> dict:
        """Update prices for all tracked products"""
        products = self.db.get_all_products()
        results = {
            "updated": 0,
            "failed": 0,
            "total": len(products),
            "errors": []
        }
        
        for product in products:
            try:
                success = await self.update_single_product_price(product.id)
                if success:
                    results["updated"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Product {product.id}: {str(e)}")
                logger.error(f"Failed to update price for product {product.id}: {e}")
        
        logger.info(f"Price update completed: {results['updated']}/{results['total']} successful")
        return results
    
    async def check_price_alerts(self, product, old_price: float, new_price: float):
        """Check and trigger price alerts"""
        alerts = self.db.get_active_alerts()
        
        for alert in alerts:
            if alert.product_id != product.id:
                continue
            
            should_trigger = False
            
            if alert.alert_type == "price_drop":
                if alert.threshold_price:
                    should_trigger = new_price <= alert.threshold_price
                else:
                    should_trigger = new_price < old_price
            
            elif alert.alert_type == "back_in_stock":
                # Implement stock checking logic
                should_trigger = True  # Placeholder
            
            if should_trigger:
                await self.trigger_alert(alert, product, old_price, new_price)
    
    async def trigger_alert(self, alert, product, old_price: float, new_price: float):
        """Trigger alert notification"""
        try:
            # Send email alert
            if alert.email:
                success = self.notification_manager.send_price_drop_alert(
                    product.name, old_price, new_price, product.url, alert.email
                )
                if success:
                    logger.info(f"Email alert sent for {product.name}")
                else:
                    logger.error(f"Failed to send email alert for {product.name}")
            
            # Send WhatsApp alert
            if alert.phone:
                message = f"🎉 Price Drop Alert!\n\n{product.name}\n💰 ₹{old_price:,.0f} → ₹{new_price:,.0f}\n🎯 Save ₹{old_price-new_price:,.0f}\n\n🛒 {product.url}"
                success = self.notification_manager.send_whatsapp_message(alert.phone, message)
                if success:
                    logger.info(f"WhatsApp alert sent for {product.name}")
                else:
                    logger.error(f"Failed to send WhatsApp alert for {product.name}")
        
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    def extract_price_from_result(self, result: dict) -> float:
        """Extract price from browser agent result"""
        try:
            if 'price' in result:
                price_str = str(result['price'])
                # Remove currency symbols and extract numeric value
                import re
                numbers = re.findall(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                if numbers:
                    return float(numbers[0])
            return None
        except:
            return None
    
    def start_scheduler(self, interval_hours: int = 6):
        """Start automated price checking scheduler"""
        def job():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.update_all_prices())
            loop.close()
        
        schedule.every(interval_hours).hours.do(job)
        
        self.is_running = True
        logger.info(f"Price tracker scheduler started (interval: {interval_hours} hours)")
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the price tracking scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Price tracker scheduler stopped")
