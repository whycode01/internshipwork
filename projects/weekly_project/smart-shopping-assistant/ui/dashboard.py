import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import hashlib
import time
from typing import Dict, List

# Import workflow system instead of old agents
try:
    from workflows.workflow_manager import WorkflowManager
    from workflows.states.workflow_states import WorkflowState
    WORKFLOW_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Workflow import failed: {e}")
    WORKFLOW_AVAILABLE = False

# Import utilities safely
try:
    from utils.notifications import NotificationManager
    from utils.data_processor import DataProcessor
    from services.notification_service import NotificationService
except ImportError as e:
    print(f"⚠️ Utils import failed: {e}")
    NotificationManager = None
    DataProcessor = None
    NotificationService = None

# Import workflow manager safely
try:
    from workflows.workflow_manager import get_workflow_manager
except ImportError:
    def get_workflow_manager():
        return None

# Fallback AI class for legacy compatibility
class FallbackProductAI:
    """Simple fallback for product AI when main workflow not available"""
    
    def generate_search_suggestions(self, query: str) -> List[str]:
        """Generate simple search suggestions"""
        if not query:
            return []
        
        # Basic keyword-based suggestions
        base_suggestions = [
            f"{query} best price",
            f"{query} with discount",
            f"cheapest {query}",
            f"{query} on sale",
            f"top rated {query}"
        ]
        
        # Add category-specific suggestions
        if any(word in query.lower() for word in ['laptop', 'computer', 'pc']):
            base_suggestions.extend([
                f"{query} gaming",
                f"{query} business",
                f"{query} student"
            ])
        elif any(word in query.lower() for word in ['phone', 'mobile', 'smartphone']):
            base_suggestions.extend([
                f"{query} 5G",
                f"{query} camera",
                f"{query} battery life"
            ])
        elif any(word in query.lower() for word in ['clothes', 'shirt', 'dress', 'fashion']):
            base_suggestions.extend([
                f"{query} cotton",
                f"{query} formal",
                f"{query} casual"
            ])
        
        return base_suggestions[:5]  # Return top 5 suggestions
    
    def categorize_query(self, query: str) -> str:
        """Simple query categorization"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['laptop', 'computer', 'pc', 'desktop']):
            return "Electronics - Computers"
        elif any(word in query_lower for word in ['phone', 'mobile', 'smartphone']):
            return "Electronics - Mobile"
        elif any(word in query_lower for word in ['shirt', 'dress', 'clothes', 'fashion', 'jeans']):
            return "Fashion"
        elif any(word in query_lower for word in ['book', 'novel', 'textbook']):
            return "Books"
        elif any(word in query_lower for word in ['shoes', 'sneakers', 'boots']):
            return "Footwear"
        else:
            return "General"
    
    def analyze_price_trend(self, price_history: List[Dict]) -> Dict[str, str]:
        """Analyze price trend from history data"""
        if not price_history or len(price_history) < 2:
            return {"recommendation": "Not enough price data to analyze trends"}
        
        try:
            # Extract prices and calculate trend
            prices = [float(item.get('price', 0)) for item in price_history]
            prices = [p for p in prices if p > 0]  # Filter out invalid prices
            
            if len(prices) < 2:
                return {"recommendation": "Monitor prices regularly for better analysis"}
            
            # Simple trend analysis
            latest_price = prices[-1]
            previous_price = prices[-2] if len(prices) > 1 else prices[0]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            # Calculate percentage change
            if previous_price > 0:
                change_percent = ((latest_price - previous_price) / previous_price) * 100
            else:
                change_percent = 0
            
            # Generate recommendation based on trend
            if change_percent < -5:
                recommendation = f"📉 Price dropped {abs(change_percent):.1f}%! Good time to buy."
            elif change_percent > 5:
                recommendation = f"📈 Price increased {change_percent:.1f}%. Consider waiting."
            elif latest_price <= min_price * 1.05:  # Within 5% of minimum
                recommendation = f"💰 Near lowest price (₹{min_price:.0f}). Great deal!"
            elif latest_price >= max_price * 0.95:  # Within 5% of maximum
                recommendation = f"⚠️ Near highest price (₹{max_price:.0f}). Consider waiting."
            elif latest_price <= avg_price * 0.9:  # 10% below average
                recommendation = f"✅ Below average price (₹{avg_price:.0f}). Good value!"
            else:
                recommendation = f"📊 Current price: ₹{latest_price:.0f} (Avg: ₹{avg_price:.0f})"
            
            return {"recommendation": recommendation}
            
        except Exception as e:
            return {"recommendation": f"Unable to analyze price trend: {str(e)}"}

class SmartShoppingDashboard:
    """Main dashboard for Smart Shopping Assistant"""
    
    def __init__(self, database, price_tracker):
        self.db = database
        self.price_tracker = price_tracker
        
        # Initialize workflow manager for AI-powered searches
        self.workflow_manager = None
        if WORKFLOW_AVAILABLE:
            try:
                # Try to get existing workflow manager
                existing_manager = get_workflow_manager()
                if existing_manager:
                    self.workflow_manager = existing_manager
                else:
                    # Create new workflow manager with database and price tracker
                    from workflows.workflow_manager import WorkflowManager
                    self.workflow_manager = WorkflowManager(database, price_tracker)
                    print("✅ Workflow manager initialized successfully")
            except Exception as e:
                print(f"⚠️ Workflow manager initialization failed: {e}")
                self.workflow_manager = None
        
        # Fallback mode if workflow not available
        if self.workflow_manager is None:
            print("📦 Running in fallback mode without AI workflow")
        
        # Initialize product AI (fallback mode for legacy compatibility)
        self.product_ai = FallbackProductAI()
        
        # Re-enable notification service - datetime issue fixed
        self.notification_service = NotificationService()
        
        # Initialize session state for notifications
        if 'user_email' not in st.session_state:
            st.session_state.user_email = ""
        if 'notification_preferences' not in st.session_state:
            st.session_state.notification_preferences = {
                'email_alerts': True,
                'price_drop_threshold': 10.0  # Percentage
            }
    
    def render(self):
        """Render the main dashboard"""
        st.title("🛒 Smart Shopping Assistant")
        st.markdown("Find the best deals across multiple websites with AI-powered automation")
        
        # Sidebar
        self.render_sidebar()
        
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Product Search", "📊 Price Tracking", "🔔 Alerts", "📈 Analytics"])
        
        with tab1:
            self.render_search_tab()
        
        with tab2:
            self.render_price_tracking_tab()
        
        with tab3:
            self.render_alerts_tab()
        
        with tab4:
            self.render_analytics_tab()
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        st.sidebar.header("🎛️ Controls")
        
        # Email configuration
        st.sidebar.subheader("📧 Email Settings")
        user_email = st.sidebar.text_input(
            "Your Email", 
            value=st.session_state.get('user_email', ''),
            placeholder="Enter your email for notifications",
            help="Enter your email to receive price drop alerts"
        )
        if user_email != st.session_state.get('user_email', ''):
            st.session_state.user_email = user_email
            if user_email and '@' in user_email:
                st.sidebar.success("✅ Email saved!")
            elif user_email:
                st.sidebar.warning("⚠️ Please enter a valid email")
        
        # Quick actions
        st.sidebar.subheader("Quick Actions")
        
        if st.sidebar.button("🔄 Refresh All Prices"):
            with st.spinner("Updating prices..."):
                self.refresh_all_prices()
                st.success("Prices updated!")
        
        if st.sidebar.button("📧 Test Notifications"):
            self.test_notifications()
        
        if st.sidebar.button("🔄 Check for Price Updates"):
            self.check_all_price_updates()
    
    def test_notifications(self):
        """Test email notification system"""
        try:
            # Test in-app notification
            in_app_success = self.notification_service.save_in_app_notification(
                "Test Notification",
                "This is a test notification to verify the system is working properly.",
                "info"
            )
            
            if in_app_success:
                st.sidebar.success("✅ In-app notification system test successful!")
            else:
                st.sidebar.error("❌ In-app notification test failed")
            
            # Test email notification if email is provided
            user_email = st.session_state.get('user_email', '')
            if user_email and '@' in user_email:
                email_success = self.notification_service.send_test_email(user_email)
                if email_success:
                    st.sidebar.success(f"✅ Test email sent successfully to {user_email}!")
                else:
                    st.sidebar.error("⚠️ Email test failed - check your email configuration")
                    with st.sidebar.expander("📧 Email Setup Help"):
                        st.markdown("""
                        **To fix Gmail authentication:**
                        
                        1. **Enable 2-Factor Authentication** on your Gmail account
                        2. **Generate App Password:**
                           - Go to [Google Account Settings](https://myaccount.google.com/)
                           - Security → 2-Step Verification
                           - App passwords → Generate new
                        3. **Update .env file:**
                           - Replace `EMAIL_PASSWORD=Mishra@2101`
                           - With `EMAIL_PASSWORD=your_16_character_app_password`
                        4. **Restart the application**
                        
                        📧 Current email: `workisscalar@gmail.com`
                        """)
            else:
                st.sidebar.info("ℹ️ Enter your email in sidebar to test email notifications")
                
        except Exception as e:
            st.sidebar.error(f"❌ Notification test failed: {str(e)}")
            print(f"Notification test error: {e}")
    
    def check_all_price_updates(self):
        """Check for price updates on all tracked products"""
        try:
            products = self.db.get_all_products()
            if not products:
                st.info("No products to update")
                return
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, product in enumerate(products):
                status_text.text(f"Updating {product.name}...")
                progress_bar.progress((i + 1) / len(products))
                
                # Check for price updates
                self.update_single_price_with_notifications(product.id)
                time.sleep(0.5)  # Small delay to avoid rate limiting
            
            status_text.text("✅ All prices updated!")
            st.success(f"Updated {len(products)} products")
            
        except Exception as e:
            st.error(f"Failed to update prices: {e}")
    
    def show_notifications_popup(self):
        """Show notifications in a popup"""
        notifications = self.notification_service.get_all_notifications(20)
        
        if not notifications:
            st.info("No notifications yet")
            return
        
        st.subheader("🔔 Recent Notifications")
        
        for notification in notifications:
            notification_type = notification.get('type', 'info')
            timestamp = datetime.fromisoformat(notification['timestamp']).strftime('%Y-%m-%d %H:%M')
            
            # Choose appropriate emoji and color
            if notification_type == 'success':
                emoji = "✅"
                color = "green"
            elif notification_type == 'warning':
                emoji = "⚠️"
                color = "orange"
            elif notification_type == 'error':
                emoji = "❌"
                color = "red"
            else:
                emoji = "ℹ️"
                color = "blue"
            
            # Display notification
            with st.expander(f"{emoji} {notification['title']} - {timestamp}"):
                st.write(notification['message'])
                if not notification.get('read', False):
                    if st.button("Mark as read", key=f"read_{notification['id']}"):
                        self.notification_service.mark_notification_as_read(notification['id'])
                        st.rerun()
        
        # Settings
        st.sidebar.subheader("⚙️ Settings")
        
        # Notification Settings
        st.sidebar.subheader("🔔 Notification Preferences")
        
        # Email settings
        email = st.sidebar.text_input("📧 Email for alerts", 
                                     value=st.session_state.get('user_email', ''),
                                     help="Enter your email to receive price alerts")
        
        if email:
            st.session_state.user_email = email
        
        # Notification preferences
        email_alerts = st.sidebar.checkbox("📧 Email notifications", 
                                         value=st.session_state.notification_preferences['email_alerts'])
        
        desktop_alerts = st.sidebar.checkbox("�️ Desktop notifications", 
                                           value=st.session_state.notification_preferences['desktop_alerts'])
        
        price_threshold = st.sidebar.slider("💰 Price drop alert threshold (%)", 
                                          min_value=1.0, max_value=50.0, 
                                          value=st.session_state.notification_preferences['price_drop_threshold'],
                                          help="Get notified when price drops by this percentage")
        
        # Update preferences
        st.session_state.notification_preferences.update({
            'email_alerts': email_alerts,
            'desktop_alerts': desktop_alerts, 
            'price_drop_threshold': price_threshold
        })
        
        # Show unread notifications count
        unread_notifications = self.notification_service.get_unread_notifications()
        if unread_notifications:
            st.sidebar.info(f"🔔 {len(unread_notifications)} unread notification(s)")
            if st.sidebar.button("📋 View Notifications"):
                self.show_notifications_popup()
        
        # WhatsApp settings (placeholder for future)
        # phone = st.sidebar.text_input("📱 Phone for WhatsApp", value="")
        # if phone:
        #     st.session_state.user_phone = phone
        
        # Auto-refresh settings
        auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh prices", value=False)
        if auto_refresh:
            refresh_interval = st.sidebar.selectbox("Refresh interval", [1, 6, 12, 24], index=1)
            st.sidebar.info(f"Prices will update every {refresh_interval} hours")
        
        # Data export
        st.sidebar.subheader("📤 Export Data")
        if st.sidebar.button("📊 Download CSV"):
            self.export_data_csv()
        
        if st.sidebar.button("📋 Download Report"):
            self.export_report()
    
    def render_search_tab(self):
        """Render product search interface"""
        st.header("🔍 Product Search")
        
        # Website selection
        st.subheader("🌐 Select Shopping Websites")
        available_sites = {
            "amazon.in": "🛍️ Amazon India",
            "flipkart.com": "📦 Flipkart", 
            "myntra.com": "👗 Myntra",
            "ajio.com": "✨ AJIO"
        }
        
        selected_sites = st.multiselect(
            "Choose websites to search",
            options=list(available_sites.keys()),
            default=["amazon.in", "flipkart.com", "myntra.com", "ajio.com"],
            format_func=lambda x: available_sites[x],
            help="Select one or more websites to search for products"
        )
        
        if not selected_sites:
            st.warning("⚠️ Please select at least one website to search")
            return
        
        # Search form
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("🔎 Search for products", placeholder="e.g., iPhone 15, Sony headphones")
        
        with col2:
            st.write("")  # Empty space for alignment
            search_button = st.button("🔍 Search", type="primary")
        
        # Search suggestions
        if search_query and len(search_query) > 3:
            suggestions = self.product_ai.generate_search_suggestions(search_query)
            if suggestions:
                st.write("💡 **Suggestions:**")
                suggestion_cols = st.columns(len(suggestions[:3]))
                for i, suggestion in enumerate(suggestions[:3]):
                    if suggestion_cols[i].button(f"🎯 {suggestion}", key=f"suggestion_{i}"):
                        search_query = suggestion
                        search_button = True
        
        # Initialize session state for search results
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        if 'last_search_query' not in st.session_state:
            st.session_state.last_search_query = ""
        
        # Perform search
        if search_button and search_query:
            st.session_state.last_search_query = search_query
            st.session_state.selected_sites = selected_sites  # Store selected sites
            st.session_state.search_results = self.perform_product_search(search_query, selected_sites)
        
        # Display search results if available
        if st.session_state.search_results and st.session_state.last_search_query:
            st.subheader(f"🔍 Search Results for '{st.session_state.last_search_query}'")
            self.display_search_results(st.session_state.search_results)
        
        # Budget filter
        st.subheader("💰 Budget Filter")
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min Price (₹)", min_value=0, value=0)
        with col2:
            max_price = st.number_input("Max Price (₹)", min_value=0, value=100000)
        
        # Recently searched products
        self.show_recent_searches()
    
    def perform_product_search(self, query: str, selected_sites: List[str] = None):
        """Perform multi-site product search using AI workflows with fallback"""
        if selected_sites is None:
            selected_sites = ["amazon.in", "flipkart.com", "myntra.com", "ajio.com"]
        
        with st.spinner(f"🔍 Searching for '{query}' on {len(selected_sites)} website(s) with AI-powered workflows..."):
            # Try AI workflow first if available
            if self.workflow_manager:
                try:
                    st.info(f"🤖 Using AI-powered workflow for intelligent product search on: {', '.join(selected_sites)}")
                    
                    # Run workflow search
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Use workflow manager for AI-powered search with selected sites
                        workflow_results = loop.run_until_complete(
                            self.workflow_manager.search_product_workflow(
                                product_name=query,
                                websites=selected_sites
                            )
                        )
                        
                        # Check if workflow was successful
                        if workflow_results and workflow_results.get('success', False):
                            st.success("✅ AI workflow search completed successfully!")
                            products = workflow_results.get('products', [])
                            if products:
                                # Convert workflow results to display format
                                results = self.convert_workflow_to_display_format(workflow_results, selected_sites)
                                # Log search query
                                sites_count = len(results.get('sites', {})) if 'sites' in results else 0
                                self.db.log_search_query(query, sites_count)
                                return results
                            else:
                                st.warning("⚠️ AI workflow completed but found no products. Generating fallback results...")
                        else:
                            error_msg = workflow_results.get('error', 'Unknown workflow error')
                            st.warning(f"⚠️ AI workflow failed: {error_msg}. Generating fallback results...")
                    
                    except Exception as workflow_error:
                        st.warning(f"⚠️ AI workflow error: {str(workflow_error)}. Generating fallback results...")
                    
                    finally:
                        loop.close()
                
                except Exception as e:
                    st.warning(f"⚠️ Workflow initialization error: {str(e)}. Generating fallback results...")
            
            else:
                st.info("🔄 AI workflow not available, generating fallback results...")
            
            # Generate fallback results
            st.info("🔄 Generating realistic mock results for demo purposes...")
            results = self.generate_fallback_search_results(query, selected_sites)
            
            # Log search query
            sites_count = len(results.get('sites', {})) if 'sites' in results else 0
            self.db.log_search_query(query, sites_count)
            
            return results
    
    def _convert_workflow_results(self, workflow_results: dict, query: str) -> dict:
        """Convert workflow results to dashboard-expected format"""
        try:
            # Extract products from workflow results
            workflow_products = workflow_results.get('products', [])
            
            # Group products by site
            sites = {}
            all_prices = []
            
            for product in workflow_products:
                site_name = product.get('site', 'unknown')
                if site_name not in sites:
                    sites[site_name] = {
                        'products': [],
                        'success': True,
                        'total_found': 0
                    }
                
                # Convert product format
                converted_product = {
                    'name': product.get('name', f'{query} Product'),
                    'price': product.get('price', 'N/A'),
                    'url': product.get('link', product.get('url', '#')),
                    'rating': product.get('rating', '4.0'),
                    'availability': product.get('availability', 'Available')
                }
                
                sites[site_name]['products'].append(converted_product)
                sites[site_name]['total_found'] += 1
                
                # Extract price for summary
                price_str = str(product.get('price', ''))
                if price_str and price_str != 'N/A':
                    import re
                    price_match = re.search(r'(\d+)', price_str.replace(',', ''))
                    if price_match:
                        try:
                            price_val = float(price_match.group(1))
                            if 10 <= price_val <= 1000000:
                                all_prices.append(price_val)
                        except:
                            continue
            
            # Calculate summary
            summary = {
                'total_products': len(workflow_products),
                'min_price': min(all_prices) if all_prices else None,
                'max_price': max(all_prices) if all_prices else None,
                'avg_price': sum(all_prices) / len(all_prices) if all_prices else None
            }
            
            return {
                'product_name': query,
                'sites': sites,
                'summary': summary,
                'source': 'ai_workflow'
            }
            
        except Exception as e:
            st.error(f"Error converting workflow results: {str(e)}")
            return {
                'product_name': query,
                'sites': {},
                'summary': {'total_products': 0},
                'source': 'ai_workflow_error'
            }

    def display_search_results(self, results: dict):
        """Display search results"""
        if not results:
            return
        
        total_products = results['summary'].get('total_products', 0)
        st.success(f"✅ Found {total_products} products")
        
        # Display summary
        if total_products > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                min_price = results['summary'].get('min_price')
                st.metric("💰 Min Price", f"₹{min_price:,.0f}" if min_price else "N/A")
            with col2:
                max_price = results['summary'].get('max_price')
                st.metric("💸 Max Price", f"₹{max_price:,.0f}" if max_price else "N/A")
            with col3:
                avg_price = results['summary'].get('avg_price')
                st.metric("📊 Avg Price", f"₹{avg_price:,.0f}" if avg_price else "N/A")
        
        # Display products by site
        sites_data = results.get('sites', {})
        if not isinstance(sites_data, dict):
            st.warning("⚠️ Sites data format issue")
            return
        
        for site_name, site_data in sites_data.items():
            # Ensure site_data is a dictionary
            if not isinstance(site_data, dict):
                st.warning(f"❌ {site_name}: Invalid data format")
                continue
                
            if 'error' in site_data:
                st.warning(f"❌ {site_name}: {site_data['error']}")
                continue
            
            st.subheader(f"🛒 {site_name.title()}")
            
            # Handle nested products structure
            products_data = site_data.get('products', [])
            if isinstance(products_data, dict):
                # If products is a dict with a 'products' key (nested structure)
                if "products" in products_data:
                    actual_products = products_data["products"]
                elif "error" in products_data:
                    st.warning(f"❌ {site_name}: {products_data['error']}")
                    continue
                else:
                    actual_products = []
            elif isinstance(products_data, list):
                # If products is already a list (correct structure)
                actual_products = products_data
            else:
                actual_products = []
            
            if isinstance(actual_products, list) and actual_products:
                for i, product in enumerate(actual_products):
                    self.render_product_card(product, site_name)
            else:
                st.info(f"No products found on {site_name.title()}")
    
    def render_product_card(self, product: dict, site: str):
        """Render individual product card"""
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**{product.get('name', 'Unknown Product')}**")
                if product.get('rating'):
                    st.write(f"⭐ {product['rating']}/5")
            
            with col2:
                price = product.get('price', 'N/A')
                if price and price != 'N/A':
                    # Handle prices with ₹ symbol like "₹799"
                    if '₹' in str(price):
                        # Extract number from price like "₹799" or "₹1,299"
                        price_str = str(price).replace('₹', '').replace(',', '').strip()
                        try:
                            price_num = float(price_str)
                            formatted_price = f"₹{price_num:,.0f}"
                            st.metric("💰 Price", formatted_price)
                        except ValueError:
                            # If it's a message like "Check on Flipkart", show as is
                            st.write(f"💰 {price}")
                    elif isinstance(price, (int, float)):
                        # Handle pure numeric prices
                        st.metric("💰 Price", f"₹{price:,.0f}")
                    elif str(price).replace(',', '').isdigit():
                        # Handle string numbers like "1299"
                        price_num = float(str(price).replace(',', ''))
                        st.metric("💰 Price", f"₹{price_num:,.0f}")
                    else:
                        # Handle placeholder messages
                        st.write(f"💰 {price}")
                else:
                    st.write("💰 Price not available")
            
            with col3:
                # Create unique key using product name, site, and index
                import hashlib
                product_name = product.get('name', 'unknown')
                unique_string = f"{site}_{product_name}_{product.get('price', '')}_{product.get('rating', '')}"
                unique_key = f"track_{hashlib.md5(unique_string.encode()).hexdigest()[:8]}"
                
                if st.button(f"➕ Track", key=unique_key):
                    with st.spinner("Adding to tracking..."):
                        success = self.add_product_to_tracking(product, site)
                        if success:
                            st.success("✅ Product added to tracking!")
                            # Don't call st.rerun() to preserve search results
                        else:
                            st.error("❌ Failed to add product")
                
                if product.get('url'):
                    st.link_button("🔗 View", product['url'])
            
            st.divider()
    
    def convert_workflow_to_display_format(self, workflow_results: dict, selected_sites: List[str]) -> dict:
        """Convert workflow results to display format"""
        try:
            # Extract products from workflow results
            workflow_products = workflow_results.get('products', [])
            
            # Group products by site
            sites = {}
            all_prices = []
            
            for product in workflow_products:
                site_name = product.get('site', 'unknown')
                if site_name not in sites:
                    sites[site_name] = {
                        'products': [],
                        'success': True,
                        'total_found': 0
                    }
                
                # Convert product format
                converted_product = {
                    'name': product.get('name', 'Unknown Product'),
                    'price': product.get('price', 'Price not available'),
                    'rating': product.get('rating', '4.0'),
                    'url': product.get('url', ''),
                    'availability': product.get('availability', 'Available'),
                    'site': site_name
                }
                
                sites[site_name]['products'].append(converted_product)
                sites[site_name]['total_found'] += 1
                
                # Extract price for summary
                price_str = str(product.get('price', ''))
                if price_str and price_str != 'N/A':
                    import re
                    price_match = re.search(r'(\d+)', price_str.replace(',', ''))
                    if price_match:
                        try:
                            price_val = float(price_match.group(1))
                            if 10 <= price_val <= 1000000:
                                all_prices.append(price_val)
                        except:
                            continue
            
            # Calculate summary
            summary = {
                'total_products': len(workflow_products),
                'min_price': min(all_prices) if all_prices else None,
                'max_price': max(all_prices) if all_prices else None,
                'avg_price': sum(all_prices) / len(all_prices) if all_prices else None
            }
            
            return {
                'product_name': workflow_results.get('query', 'Unknown Query'),
                'sites': sites,
                'summary': summary,
                'source': 'ai_workflow'
            }
            
        except Exception as e:
            st.error(f"Error converting workflow results: {str(e)}")
            return {
                'product_name': workflow_results.get('query', 'Unknown Query'),
                'sites': {},
                'summary': {'total_products': 0},
                'source': 'ai_workflow_error'
            }
    
    def generate_fallback_search_results(self, query: str, selected_sites: List[str]) -> dict:
        """Generate realistic fallback search results for demo purposes"""
        try:
            sites = {}
            all_prices = []
            
            for i, site in enumerate(selected_sites):
                site_name = site.replace(".com", "").replace(".in", "").title()
                
                # Generate 3-5 realistic products per site
                products = []
                num_products = 3 + (i % 3)  # 3-5 products
                
                for j in range(num_products):
                    base_price = 999 + (i * 150) + (j * 100) + (hash(query) % 1000)
                    
                    # Generate realistic product name
                    product_name = f"{query.title()} - {site_name} {['Basic', 'Pro', 'Premium', 'Elite'][j % 4]} Model"
                    
                    # Generate realistic ratings
                    rating = round(3.5 + (i * 0.1) + (j * 0.1), 1)
                    if rating > 5.0:
                        rating = 5.0
                    
                    product = {
                        'name': product_name,
                        'price': f"₹{base_price:,}",
                        'rating': f"{rating}",
                        'url': f"https://www.{site}/search?q={query.replace(' ', '+')}&product={j}",
                        'availability': 'Available' if j < 3 else 'Limited Stock',
                        'site': site
                    }
                    
                    products.append(product)
                    all_prices.append(base_price)
                
                sites[site] = {
                    'products': products,
                    'success': True,
                    'total_found': len(products)
                }
            
            # Calculate summary
            summary = {
                'total_products': sum(len(site_data['products']) for site_data in sites.values()),
                'min_price': min(all_prices) if all_prices else None,
                'max_price': max(all_prices) if all_prices else None,
                'avg_price': sum(all_prices) / len(all_prices) if all_prices else None
            }
            
            return {
                'product_name': query,
                'sites': sites,
                'summary': summary,
                'source': 'fallback_demo'
            }
            
        except Exception as e:
            st.error(f"Error generating fallback results: {str(e)}")
            return {
                'product_name': query,
                'sites': {},
                'summary': {'total_products': 0},
                'source': 'fallback_error'
            }
    
    def add_product_to_tracking(self, product: dict, site: str) -> bool:
        """Add product to tracking database with improved cache handling"""
        try:
            # Extract price value with better handling
            price_str = product.get('price', '')
            price_value = None
            
            if price_str and price_str not in ['Price not available', 'N/A', '']:
                # Handle different price formats
                if '₹' in str(price_str):
                    # Extract number from ₹799 format
                    import re
                    numbers = re.findall(r'[\d,]+', str(price_str).replace('₹', ''))
                    if numbers:
                        clean_number = numbers[0].replace(',', '')
                        try:
                            price_value = float(clean_number)
                        except ValueError:
                            price_value = None
                elif isinstance(price_str, (int, float)):
                    price_value = float(price_str)
                else:
                    # Try to extract any number from string
                    import re
                    numbers = re.findall(r'\d+', str(price_str).replace(',', ''))
                    if numbers:
                        price_value = float(numbers[0])
            
            # If no price found, use a reasonable default based on site
            if price_value is None:
                site_defaults = {
                    'amazon.in': 999.0,
                    'flipkart.com': 899.0,
                    'myntra.com': 1299.0,
                    'ajio.com': 1199.0
                }
                price_value = site_defaults.get(site, 999.0)
                print(f"Using default price ₹{price_value} for {product.get('name', 'Unknown')}")
            
            # Create product URL if missing
            product_url = product.get('url', '')
            if not product_url:
                import time
                product_url = f"https://www.{site}/product/{int(time.time())}"
            
            # Check if product already exists by URL or name+site combination
            existing_product = self.db.find_product_by_url(product_url)
            if not existing_product:
                # Also check by name+site to prevent duplicates
                similar_products = self.db.get_all_products()
                for existing in similar_products:
                    if (existing.name.lower().strip() == product.get('name', '').lower().strip() 
                        and existing.site.lower() == site.lower()):
                        print(f"ℹ️ Product already exists: {existing.name}")
                        return False
            
            # Prepare product data
            product_name = product.get('name', 'Unknown Product')
            
            # Add to database
            product_data = {
                'name': product_name,
                'url': product_url,
                'price': price_value,
                'site': site,
                'rating': product.get('rating'),
                'image_url': product.get('image_url'),
                'target_price': product.get('target_price')
            }
            
            added_product = self.db.add_product(product_data)
            
            if added_product:
                print(f"✅ Successfully added {product_name} to tracking (₹{price_value})")
                
                # Clear comprehensive session state to force refresh
                cache_keys_to_clear = [
                    'tracked_products',
                    'tracking_page_data',
                    'product_cache',
                    'products_list',
                    'dashboard_products',
                    'tracking_products'
                ]
                for key in cache_keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Also clear any memoized functions
                st.cache_data.clear()
                
                return True
            else:
                print(f"❌ Failed to add product to database")
                return False
            
        except Exception as e:
            import traceback
            print(f"❌ Error adding product to tracking: {e}")
            print(f"📋 Traceback: {traceback.format_exc()}")
            return False
    
    def extract_price(self, price_str):
        """Extract numeric price from string"""
        if not price_str:
            return None
        try:
            import re
            # Convert to string and clean
            clean_str = str(price_str).replace('₹', '').replace(',', '').strip()
            
            # Handle "Check on Flipkart" type strings - return None but don't error
            if any(word in clean_str.lower() for word in ['check', 'visit', 'site', 'flipkart', 'amazon', 'myntra', 'ajio', 'request']):
                st.write(f"🔍 Debug: Price contains placeholder text: {clean_str}")
                return None
            
            # Extract numbers from the string
            numbers = re.findall(r'\d+\.?\d*', clean_str)
            if numbers:
                price_value = float(numbers[0])
                # Validate reasonable price range (₹1 to ₹10,00,000)
                if 1 <= price_value <= 1000000:
                    st.write(f"🔍 Debug: Valid price extracted: {price_value}")
                    return price_value
                else:
                    st.write(f"🔍 Debug: Price out of range: {price_value}")
            else:
                st.write(f"🔍 Debug: No numbers found in price string: {clean_str}")
            return None
        except Exception as e:
            st.write(f"🔍 Debug: Price extraction error: {e}")
            return None
    
    def extract_rating(self, rating_str):
        """Extract numeric rating from string"""
        if not rating_str:
            return None
        try:
            import re
            # Extract numbers from rating string
            numbers = re.findall(r'\d+\.?\d*', str(rating_str))
            if numbers:
                rating = float(numbers[0])
                # Ensure rating is between 0 and 5
                return max(0, min(5, rating))
            else:
                return None
        except Exception as e:
            print(f"Rating extraction error: {e}")
            return None
    
    def render_price_tracking_tab(self):
        """Render price tracking interface"""
        st.header("📊 Price Tracking")
        
        # Debug section
        with st.expander("🔧 Debug Info", expanded=False):
            st.write("Database connection test:")
            try:
                # Check if database file exists
                import os
                db_paths = ["shopping_assistant.db", "data/products.db", "products.db"]
                db_found = False
                
                for db_path in db_paths:
                    if os.path.exists(db_path):
                        st.write(f"✅ Database file exists: {db_path}")
                        st.write(f"📁 File size: {os.path.getsize(db_path)} bytes")
                        db_found = True
                        break
                
                if not db_found:
                    st.write(f"❌ Database file not found in any of these locations: {db_paths}")
                    st.write("📁 Current directory contents:")
                    current_dir = os.getcwd()
                    st.write(f"Current working directory: {current_dir}")
                    files = os.listdir(current_dir)
                    db_files = [f for f in files if f.endswith('.db')]
                    st.write(f"DB files found: {db_files}")
                    
                    # Check data directory
                    if os.path.exists("data"):
                        data_files = os.listdir("data")
                        st.write(f"Files in data directory: {data_files}")
                
                # Test database connection
                products = self.db.get_all_products()
                st.write(f"Found {len(products)} products in database")
                
                # Check database tables using the correct class
                engine = self.db.engine
                from sqlalchemy import inspect
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                st.write(f"� Tables in database: {tables}")
                
                # Test adding a sample product
                st.write("🧪 Testing add_product function:")
                
                test_product = {
                    'name': 'Test Product',
                    'url': f'https://test.com/product/{int(__import__("time").time())}',
                    'site': 'test',
                    'price': 100.0,
                    'rating': 4.5,
                    'image_url': None
                }
                    
                if st.button("🧪 Add Test Product"):
                    try:
                        st.write("🧪 Attempting to add test product...")
                        result = self.db.add_product(test_product)
                        st.write(f"🧪 add_product returned: {result}")
                        if result:
                            st.success(f"✅ Test product added: {result.name}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to add test product - returned None")
                    except Exception as test_error:
                        st.error(f"🧪 Test add_product failed: {test_error}")
                        import traceback
                        st.code(traceback.format_exc())
                
                # Add a test with a real-looking product
                if st.button("🧪 Add Realistic Test Product"):
                    try:
                        realistic_product = {
                            'name': 'Samsung Galaxy M34 5G',
                            'url': f'https://amazon.in/product/{int(__import__("time").time())}',
                            'site': 'amazon.in',
                            'price': 15999.0,
                            'rating': 4.2,
                            'image_url': None
                        }
                        result = self.db.add_product(realistic_product)
                        if result:
                            st.success(f"✅ Realistic test product added: {result.name}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to add realistic test product")
                    except Exception as test_error:
                        st.error(f"🧪 Realistic test failed: {test_error}")
                        import traceback
                        st.code(traceback.format_exc())
                
                for product in products:
                    st.write(f"- {product.name} (₹{product.current_price}) from {product.site}")
                    
            except Exception as e:
                st.error(f"Database error: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        # Get tracked products
        products = self.db.get_all_products()
        
        if not products:
            st.info("🎯 No products being tracked. Add some products from the search tab!")
            return
        
        # Display tracked products
        for product in products:
            self.render_price_tracking_card(product)
    
    def render_price_tracking_card(self, product):
        """Render price tracking card for a product"""
        with st.expander(f"📦 {product.name}", expanded=True):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{product.site.title()}**")
                st.write(f"Added: {product.created_at.strftime('%Y-%m-%d')}")
            
            with col2:
                if product.current_price:
                    st.metric("💰 Current", f"₹{product.current_price:,.0f}")
                else:
                    st.write("💰 Price: Not available")
                    st.caption("Set a target price to start monitoring")
            
            with col3:
                if product.target_price:
                    st.metric("🎯 Target", f"₹{product.target_price:,.0f}")
                else:
                    target = st.number_input(f"Set target price", min_value=0.0, key=f"target_{product.id}")
                    if st.button("Set", key=f"set_target_{product.id}"):
                        self.set_target_price(product.id, target)
            
            with col4:
                if st.button("🗑️ Remove", key=f"remove_{product.id}"):
                    self.remove_product_tracking(product.id)
                
                if st.button("🔄 Update", key=f"update_{product.id}"):
                    self.update_single_price(product.id)
                    st.rerun()  # Refresh to show updated price
            
            # Price history chart
            self.render_price_chart(product)
        
        # Alert settings OUTSIDE the expander (to avoid nesting)
        st.subheader(f"🔔 Alert Settings for {product.name}")
        col_alert1, col_alert2 = st.columns(2)
        
        with col_alert1:
            # Quick target price setting
            if not product.target_price:
                quick_target = st.selectbox(
                    "Quick target",
                    ["Custom", "10% off", "20% off", "30% off"],
                    key=f"quick_target_{product.id}"
                )
                
                if quick_target != "Custom" and product.current_price:
                    discount = int(quick_target.split("%")[0])
                    suggested_price = product.current_price * (1 - discount/100)
                    if st.button(f"Set to ₹{suggested_price:,.0f}", key=f"quick_set_{product.id}"):
                        self.set_target_price(product.id, suggested_price)
                        st.rerun()
        
        with col_alert2:
            # Show price change percentage
            if product.current_price:
                # Get price from 7 days ago
                week_ago_price = self.get_price_days_ago(product.id, 7)
                if week_ago_price:
                    change_percent = ((product.current_price - week_ago_price) / week_ago_price) * 100
                    if change_percent > 0:
                        st.metric("📈 7-day change", f"+{change_percent:.1f}%", delta=f"+₹{product.current_price - week_ago_price:,.0f}")
                    else:
                        st.metric("📉 7-day change", f"{change_percent:.1f}%", delta=f"-₹{week_ago_price - product.current_price:,.0f}")
        
        # Alert status
        if product.target_price and product.current_price:
            if product.current_price <= product.target_price:
                st.success("🎯 Target price reached! Time to buy!")
            else:
                diff = product.current_price - product.target_price
                st.info(f"💰 ₹{diff:,.0f} away from target price")
        
        st.divider()  # Add separator between products
    
    def render_price_chart(self, product):
        """Render price history chart"""
        history = self.db.get_price_history(product.id, days=30)
        
        if len(history) < 2:
            st.info("📈 Price history will appear after multiple price updates")
            return
        
        # Create DataFrame
        df = pd.DataFrame([{
            'Date': h.timestamp,
            'Price': h.price
        } for h in history])
        
        # Create chart
        fig = px.line(df, x='Date', y='Price', 
                     title=f"Price History - {product.name}",
                     markers=True)
        
        # Add target price line if set
        if product.target_price:
            fig.add_hline(y=product.target_price, 
                         line_dash="dash", 
                         line_color="red",
                         annotation_text="Target Price")
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Price analysis
        analysis = self.product_ai.analyze_price_trend([{
            'timestamp': h.timestamp.isoformat(),
            'price': h.price
        } for h in history])
        
        if analysis:
            st.info(f"📊 **Analysis:** {analysis.get('recommendation', 'Monitor prices')}")
    
    def render_alerts_tab(self):
        """Render alerts management interface"""
        st.header("🔔 Price Alerts")
        
        # Create new alert
        st.subheader("➕ Create New Alert")
        
        products = self.db.get_all_products()
        if products:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_product = st.selectbox("Select Product", 
                                               options=products,
                                               format_func=lambda x: x.name)
            
            with col2:
                alert_type = st.selectbox("Alert Type", ["price_drop", "back_in_stock"])
            
            with col3:
                threshold = st.number_input("Price Threshold (₹)", min_value=0.0)
            
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", value=st.session_state.get('user_email', ''))
            with col2:
                phone = st.text_input("Phone", value=st.session_state.get('user_phone', ''))
            
            if st.button("🔔 Create Alert"):
                self.create_alert(selected_product.id, alert_type, threshold, email, phone)
        
        # Show existing alerts
        st.subheader("📋 Active Alerts")
        alerts = self.db.get_active_alerts()
        
        if alerts:
            for alert in alerts:
                product = self.db.get_product_by_id(alert.product_id)
                if product:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**{product.name}**")
                            st.write(f"Alert: {alert.alert_type}")
                        
                        with col2:
                            if alert.threshold_price:
                                st.write(f"Threshold: ₹{alert.threshold_price:,.0f}")
                            st.write(f"Contact: {alert.email or alert.phone}")
                        
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_alert_{alert.id}"):
                                self.delete_alert(alert.id)
                        
                        st.divider()
        else:
            st.info("🔕 No active alerts. Create one above!")
    
    def render_analytics_tab(self):
        """Render analytics and insights"""
        st.header("📈 Analytics & Insights")
        
        # Summary metrics
        products = self.db.get_all_products()
        total_products = len(products)
        total_savings = self.calculate_total_savings()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Tracked Products", total_products)
        
        with col2:
            st.metric("💰 Total Savings", f"₹{total_savings:,.0f}")
        
        with col3:
            alerts_count = len(self.db.get_active_alerts())
            st.metric("🔔 Active Alerts", alerts_count)
        
        with col4:
            avg_price = self.calculate_average_price()
            st.metric("📊 Avg Product Price", f"₹{avg_price:,.0f}")
        
        # Charts
        self.render_analytics_charts()
    
    def render_analytics_charts(self):
        """Render analytics charts"""
        products = self.db.get_all_products()
        
        if not products:
            st.info("📊 Analytics will appear when you start tracking products")
            return
        
        # Site distribution
        site_data = {}
        for product in products:
            site_data[product.site] = site_data.get(product.site, 0) + 1
        
        if site_data:
            st.subheader("🌐 Products by Site")
            fig = px.pie(values=list(site_data.values()), 
                        names=list(site_data.keys()),
                        title="Distribution of Tracked Products by Site")
            st.plotly_chart(fig, use_container_width=True)
        
        # Price range distribution
        prices = [p.current_price for p in products if p.current_price]
        if prices:
            st.subheader("💰 Price Distribution")
            fig = px.histogram(x=prices, nbins=10, title="Product Price Distribution")
            fig.update_layout(
                xaxis_title="Price (₹)",
                yaxis_title="Number of Products"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Helper methods
    def refresh_all_prices(self):
        """Refresh prices for all tracked products"""
        # Implementation for price refresh
        pass
    
    def test_notifications(self):
        """Test notification system"""
        try:
            # Use the correct attribute name and method
            if hasattr(self, 'notification_service'):
                # Test in-app notification
                in_app_success = self.notification_service.save_in_app_notification(
                    "Test Notification", 
                    "This is a test notification to verify the system is working.",
                    "info"
                )
                
                # Test email notification if user email is configured
                user_email = st.session_state.get('user_email', '')
                if user_email and '@' in user_email:
                    email_success = self.notification_service.send_test_email(user_email)
                    if email_success:
                        st.success(f"✅ Test email sent successfully to {user_email}!")
                    else:
                        st.warning("⚠️ Email test failed - check your email configuration")
                else:
                    st.info("ℹ️ Enter your email in sidebar to test email notifications")
                
                if in_app_success:
                    st.success("✅ In-app notification system test successful!")
                else:
                    st.error("❌ In-app notification system test failed")
            else:
                st.error("Notification service not available")
        except Exception as e:
            st.error(f"Notification test failed: {e}")
    
    def export_data_csv(self):
        """Export tracking data to CSV"""
        # Implementation for CSV export
        pass
    
    def export_report(self):
        """Export detailed report"""
        # Implementation for report export
        pass
    
    def show_recent_searches(self):
        """Show recent search queries"""
        # Implementation for recent searches
        pass
    
    def set_target_price(self, product_id: int, target_price: float):
        """Set target price for product"""
        try:
            # Update target price in database
            success = self.db.update_product_target_price(product_id, target_price)
            if success:
                st.success(f"🎯 Target price set to ₹{target_price:,.0f}")
                
                # Check if current price is already at or below target
                product = self.db.get_product_by_id(product_id)
                if product and product.current_price and product.current_price <= target_price:
                    st.balloons()  # Celebration effect
                    st.success("🎉 Target price already reached!")
                    
                    # Send email notification if configured
                    if (st.session_state.get('user_email') and 
                        st.session_state.notification_preferences.get('email_alerts', True)):
                        
                        email_success = self.notification_service.send_price_alert_email(
                            product.name, product.current_price, target_price, product.url,
                            st.session_state.user_email
                        )
                        
                        if email_success:
                            st.success("📧 Email notification sent!")
                        else:
                            st.warning("📧 Email notification failed")
                
                st.rerun()  # Refresh to show updated target price
            else:
                st.error("❌ Failed to set target price")
        except Exception as e:
            st.error(f"❌ Error setting target price: {e}")
    
    def remove_product_tracking(self, product_id: int):
        """Remove product from tracking"""
        if self.db.delete_product(product_id):
            st.success("Product removed from tracking!")
            
            # Clear comprehensive session state to force refresh
            cache_keys_to_clear = [
                'tracked_products',
                'tracking_page_data', 
                'product_cache',
                'products_list',
                'dashboard_products',
                'tracking_products'
            ]
            for key in cache_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Force immediate rerun
            st.rerun()
        else:
            st.error("Failed to remove product")
    
    def update_single_price(self, product_id: int):
        """Update price for single product"""
        try:
            product = self.db.get_product_by_id(product_id)
            if not product:
                st.error("Product not found")
                return
            
            # Get current price from website using workflow system
            with st.spinner(f"Updating price for {product.name}..."):
                if self.workflow_manager:
                    try:
                        # Use workflow to get updated price
                        state = WorkflowState(
                            query=f"Update price for {product.name}",
                            search_sites=[product.site],
                            target_url=product.url
                        )
                        # Run workflow asynchronously
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(self.workflow_manager.run_workflow(state))
                        loop.close()
                        
                        # Extract updated price from workflow result
                        if result and 'sites' in result and product.site in result['sites']:
                            site_products = result['sites'][product.site]
                            if site_products:
                                updated_price = site_products[0].get('price')
                            else:
                                updated_price = None
                        else:
                            updated_price = None
                    except Exception as e:
                        st.warning(f"⚠️ Workflow price update failed: {e}")
                        updated_price = None
                else:
                    # Fallback mode
                    updated_price = None
                
                if updated_price is None:
                    st.warning(f"Could not update price: {result['error']}")
                    return
                
                # Extract new price
                new_price_str = result.get('current_price', 'N/A')
                if new_price_str and new_price_str != 'N/A':
                    # Extract numeric value
                    import re
                    price_numbers = re.findall(r'\d+', str(new_price_str).replace(',', ''))
                    if price_numbers:
                        new_price = float(''.join(price_numbers))
                        self.update_single_price_with_notifications(product_id, new_price)
                    else:
                        st.warning("Could not parse price from website")
                else:
                    st.warning("Price not available on website")
                    
        except Exception as e:
            st.error(f"Failed to update price: {e}")
    
    def update_single_price_with_notifications(self, product_id: int, new_price: float = None):
        """Update price with notification support"""
        try:
            product = self.db.get_product_by_id(product_id)
            if not product:
                return
            
            old_price = product.current_price
            
            # If new_price not provided, fetch from website using workflow
            if new_price is None:
                if self.workflow_manager:
                    try:
                        # Use workflow to get updated price
                        state = WorkflowState(
                            query=f"Update price for {product.name}",
                            search_sites=[product.site],
                            target_url=product.url
                        )
                        # Run workflow asynchronously
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(self.workflow_manager.run_workflow(state))
                        loop.close()
                        
                        # Extract updated price from workflow result
                        if result and 'sites' in result and product.site in result['sites']:
                            site_products = result['sites'][product.site]
                            if site_products:
                                new_price_str = site_products[0].get('price')
                                if new_price_str and new_price_str != 'N/A':
                                    import re
                                    price_numbers = re.findall(r'\d+', str(new_price_str).replace(',', ''))
                                    if price_numbers:
                                        new_price = float(''.join(price_numbers))
                    except Exception as e:
                        print(f"⚠️ Workflow price update failed: {e}")
                        new_price = None
            
            if new_price is None or new_price <= 0:
                return
            
            # Update price in database
            self.db.update_product_price(product_id, new_price)
            
            # Check if price dropped significantly
            if old_price and new_price < old_price:
                price_drop_percent = ((old_price - new_price) / old_price) * 100
                threshold = st.session_state.notification_preferences['price_drop_threshold']
                
                # Send email notification if price drop is significant
                if price_drop_percent >= threshold:
                    # Only send email notification
                    if (st.session_state.get('user_email') and 
                        st.session_state.notification_preferences.get('email_alerts', True)):
                        
                        email_success = self.notification_service.send_price_alert_email(
                            product.name, new_price, old_price, product.url,
                            st.session_state.user_email
                        )
                        
                        if email_success:
                            st.success(f"💰 Price dropped for {product.name}! Email alert sent!")
                        else:
                            st.success(f"💰 Price dropped for {product.name}! Saved ₹{old_price - new_price:,.0f}")
                            st.warning("📧 Email alert failed to send")
                    else:
                        st.success(f"� Price dropped for {product.name}! Saved ₹{old_price - new_price:,.0f}")
            
            # Check if target price reached
            elif product.target_price and new_price <= product.target_price:
                # Send email for target price achievement
                if (st.session_state.get('user_email') and 
                    st.session_state.notification_preferences.get('email_alerts', True)):
                    
                    email_success = self.notification_service.send_price_alert_email(
                        product.name, new_price, product.target_price, product.url,
                        st.session_state.user_email
                    )
                    
                    if email_success:
                        st.balloons()  # Celebration effect
                        st.success(f"🎉 Target price reached for {product.name}! Email sent!")
                    else:
                        st.balloons()  # Celebration effect
                        st.success(f"🎉 Target price reached for {product.name}!")
                        st.warning("📧 Email alert failed to send")
                else:
                    st.balloons()  # Celebration effect
                    st.success(f"🎉 Target price reached for {product.name}!")
                
        except Exception as e:
            print(f"Error in update_single_price_with_notifications: {e}")
    
    def create_alert(self, product_id: int, alert_type: str, threshold: float, email: str, phone: str):
        """Create new price alert"""
        try:
            self.db.add_alert(product_id, alert_type, threshold, email, phone)
            st.success("Alert created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to create alert: {e}")
    
    def delete_alert(self, alert_id: int):
        """Delete price alert"""
        # Implementation for deleting alert
        pass
    
    def calculate_total_savings(self) -> float:
        """Calculate total savings from price tracking"""
        # Implementation for calculating savings
        return 0.0
    
    def calculate_average_price(self) -> float:
        """Calculate average price of tracked products"""
        products = self.db.get_all_products()
        prices = [p.current_price for p in products if p.current_price]
        return sum(prices) / len(prices) if prices else 0.0
    
    def get_price_days_ago(self, product_id: int, days: int) -> float:
        """Get price from specified days ago"""
        try:
            target_date = datetime.now() - timedelta(days=days)
            history = self.db.get_price_history(product_id, days=days + 1)
            
            # Find the closest price to the target date
            if history:
                closest_entry = min(history, key=lambda x: abs((x.timestamp - target_date).total_seconds()))
                return closest_entry.price
            
            return None
        except Exception as e:
            print(f"Error getting historical price: {e}")
            return None
