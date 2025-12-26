import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict
import csv
import io

class DataProcessor:
    """Handle data processing and export functionality"""
    
    def __init__(self):
        pass
    
    def create_products_dataframe(self, products: List) -> pd.DataFrame:
        """Create DataFrame from products list"""
        data = []
        for product in products:
            data.append({
                'ID': product.id,
                'Name': product.name,
                'Site': product.site,
                'Current Price': product.current_price,
                'Target Price': product.target_price,
                'Rating': product.rating,
                'Created': product.created_at,
                'Updated': product.updated_at,
                'URL': product.url
            })
        
        return pd.DataFrame(data)
    
    def create_price_history_dataframe(self, price_history: List) -> pd.DataFrame:
        """Create DataFrame from price history"""
        data = []
        for entry in price_history:
            data.append({
                'Product ID': entry.product_id,
                'Price': entry.price,
                'Timestamp': entry.timestamp,
                'Availability': entry.availability
            })
        
        return pd.DataFrame(data)
    
    def export_to_csv(self, dataframe: pd.DataFrame, filename: str = None) -> str:
        """Export DataFrame to CSV string"""
        if filename is None:
            filename = f"shopping_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output = io.StringIO()
        dataframe.to_csv(output, index=False)
        return output.getvalue()
    
    def generate_price_report(self, database) -> Dict:
        """Generate comprehensive price tracking report"""
        products = database.get_all_products()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_products': len(products),
                'active_products': len([p for p in products if p.is_active]),
                'sites_tracked': len(set(p.site for p in products)),
                'total_savings': 0.0,
                'average_price': 0.0
            },
            'products': [],
            'price_trends': {},
            'alerts_triggered': 0
        }
        
        total_price = 0
        price_count = 0
        
        for product in products:
            # Get price history
            history = database.get_price_history(product.id, days=30)
            
            if history:
                prices = [h.price for h in history]
                min_price = min(prices)
                max_price = max(prices)
                current_price = product.current_price or prices[-1]
                
                savings = max_price - current_price if current_price else 0
                report['summary']['total_savings'] += savings
                
                if current_price:
                    total_price += current_price
                    price_count += 1
                
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'site': product.site,
                    'current_price': current_price,
                    'min_price': min_price,
                    'max_price': max_price,
                    'savings': savings,
                    'price_changes': len(history),
                    'target_price': product.target_price,
                    'url': product.url
                }
                
                report['products'].append(product_data)
        
        # Calculate averages
        if price_count > 0:
            report['summary']['average_price'] = total_price / price_count
        
        return report
    
    def export_report_json(self, report: Dict) -> str:
        """Export report as JSON string"""
        return json.dumps(report, indent=2, default=str)
    
    def export_report_html(self, report: Dict) -> str:
        """Export report as HTML string"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart Shopping Assistant Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 10px; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 15px; background-color: #e8f5e8; border-radius: 5px; }}
                .products {{ margin: 20px 0; }}
                .product {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .savings {{ color: green; font-weight: bold; }}
                .price {{ color: #333; font-size: 1.1em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛒 Smart Shopping Assistant Report</h1>
                <p>Generated on: {report['generated_at']}</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>📦 Products Tracked</h3>
                    <p>{report['summary']['total_products']}</p>
                </div>
                <div class="metric">
                    <h3>💰 Total Savings</h3>
                    <p class="savings">₹{report['summary']['total_savings']:,.0f}</p>
                </div>
                <div class="metric">
                    <h3>📊 Average Price</h3>
                    <p class="price">₹{report['summary']['average_price']:,.0f}</p>
                </div>
                <div class="metric">
                    <h3>🌐 Sites</h3>
                    <p>{report['summary']['sites_tracked']}</p>
                </div>
            </div>
            
            <div class="products">
                <h2>📋 Product Details</h2>
        """
        
        for product in report['products']:
            html += f"""
                <div class="product">
                    <h3>{product['name']}</h3>
                    <p><strong>Site:</strong> {product['site']}</p>
                    <p><strong>Current Price:</strong> ₹{product['current_price']:,.0f}</p>
                    <p><strong>Price Range:</strong> ₹{product['min_price']:,.0f} - ₹{product['max_price']:,.0f}</p>
                    <p><strong>Savings:</strong> <span class="savings">₹{product['savings']:,.0f}</span></p>
                    <p><strong>Price Changes:</strong> {product['price_changes']}</p>
                    <p><a href="{product['url']}" target="_blank">🔗 View Product</a></p>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def calculate_savings_analytics(self, database) -> Dict:
        """Calculate detailed savings analytics"""
        products = database.get_all_products()
        analytics = {
            'total_savings': 0.0,
            'savings_by_site': {},
            'top_saving_products': [],
            'monthly_savings': 0.0,
            'potential_savings': 0.0
        }
        
        for product in products:
            history = database.get_price_history(product.id, days=30)
            if len(history) >= 2:
                max_price = max(h.price for h in history)
                min_price = min(h.price for h in history)
                current_price = product.current_price or history[-1].price
                
                savings = max_price - current_price
                analytics['total_savings'] += savings
                
                # Savings by site
                site = product.site
                if site not in analytics['savings_by_site']:
                    analytics['savings_by_site'][site] = 0
                analytics['savings_by_site'][site] += savings
                
                # Top saving products
                analytics['top_saving_products'].append({
                    'name': product.name,
                    'savings': savings,
                    'site': site
                })
        
        # Sort top saving products
        analytics['top_saving_products'].sort(key=lambda x: x['savings'], reverse=True)
        analytics['top_saving_products'] = analytics['top_saving_products'][:10]
        
        return analytics
