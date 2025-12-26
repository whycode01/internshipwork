import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class ProductCard:
    """Reusable product card component"""
    
    @staticmethod
    def render(product_data: Dict, show_tracking_button: bool = True, key_prefix: str = ""):
        """Render a product card with all product information"""
        with st.container():
            # Create border around the card
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                # Product name and basic info
                st.markdown(f"**{product_data.get('name', 'Unknown Product')}**")
                
                # Site badge
                site = product_data.get('site', 'unknown')
                st.markdown(f"🏪 **{site.title()}**")
                
                # Rating if available
                if product_data.get('rating'):
                    rating = float(product_data['rating'])
                    stars = "⭐" * int(rating)
                    st.markdown(f"{stars} {rating}/5")
                
                # Availability status
                availability = product_data.get('availability', True)
                if availability:
                    st.markdown("✅ **In Stock**")
                else:
                    st.markdown("❌ **Out of Stock**")
            
            with col2:
                # Price information
                price = product_data.get('price', product_data.get('current_price'))
                if price:
                    try:
                        price_num = float(str(price).replace('₹', '').replace(',', ''))
                        st.metric("💰 Price", f"₹{price_num:,.0f}")
                    except:
                        st.markdown(f"💰 **Price:** {price}")
                else:
                    st.markdown("💰 **Price:** Not available")
                
                # Target price if available
                target_price = product_data.get('target_price')
                if target_price:
                    st.metric("🎯 Target", f"₹{target_price:,.0f}")
            
            with col3:
                # Additional metrics
                if product_data.get('savings'):
                    savings = product_data['savings']
                    st.metric("💸 Savings", f"₹{savings:,.0f}", delta=f"{savings:,.0f}")
                
                # Date information
                if product_data.get('created_at'):
                    created = product_data['created_at']
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    st.markdown(f"📅 Added: {created.strftime('%Y-%m-%d')}")
                
                if product_data.get('updated_at'):
                    updated = product_data['updated_at']
                    if isinstance(updated, str):
                        updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    st.markdown(f"🔄 Updated: {updated.strftime('%Y-%m-%d')}")
            
            with col4:
                # Action buttons
                if show_tracking_button:
                    if st.button("➕ Track", key=f"{key_prefix}_track_{product_data.get('id', '')}"):
                        return "track"
                
                # View product button
                if product_data.get('url'):
                    st.link_button("🔗 View", product_data['url'], use_container_width=True)
                
                # Update price button (for tracked products)
                if product_data.get('id') and not show_tracking_button:
                    if st.button("🔄 Update", key=f"{key_prefix}_update_{product_data['id']}"):
                        return "update"
                    
                    if st.button("🗑️ Remove", key=f"{key_prefix}_remove_{product_data['id']}"):
                        return "remove"
        
        return None

class PriceChart:
    """Price history chart component"""
    
    @staticmethod
    def render(price_history: List[Dict], product_name: str, target_price: Optional[float] = None):
        """Render price history chart"""
        if not price_history or len(price_history) < 2:
            st.info("📈 Price history will appear after multiple price updates")
            return
        
        # Prepare data
        df = pd.DataFrame(price_history)
        
        # Ensure we have the right column names
        if 'timestamp' in df.columns:
            df['Date'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['Date'] = pd.to_datetime(df['date'])
        else:
            df['Date'] = pd.date_range(start='2024-01-01', periods=len(df))
        
        if 'price' not in df.columns and 'Price' in df.columns:
            df['price'] = df['Price']
        
        # Create the chart
        fig = px.line(df, x='Date', y='price', 
                     title=f"📈 Price History - {product_name}",
                     markers=True,
                     line_shape='spline')
        
        # Customize the chart
        fig.update_traces(
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8, color='#1f77b4')
        )
        
        # Add target price line if provided
        if target_price:
            fig.add_hline(
                y=target_price, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Target: ₹{target_price:,.0f}",
                annotation_position="top right"
            )
        
        # Update layout
        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            hovermode='x unified',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        # Format y-axis to show currency
        fig.update_yaxis(tickformat='₹,.0f')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price statistics
        if len(price_history) > 1:
            prices = [p['price'] for p in price_history]
            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📉 Lowest", f"₹{min_price:,.0f}")
            
            with col2:
                st.metric("📈 Highest", f"₹{max_price:,.0f}")
            
            with col3:
                savings = max_price - current_price
                st.metric("💰 Max Savings", f"₹{savings:,.0f}")
            
            with col4:
                change_percent = ((current_price - prices[0]) / prices[0]) * 100
                st.metric("📊 Total Change", f"{change_percent:+.1f}%")

class AlertCard:
    """Alert management component"""
    
    @staticmethod
    def render(alert_data: Dict, product_name: str, key_prefix: str = ""):
        """Render alert card"""
        with st.container():
            st.markdown("---")
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**🔔 {product_name}**")
                st.markdown(f"Alert Type: **{alert_data.get('alert_type', '').replace('_', ' ').title()}**")
                
                if alert_data.get('threshold_price'):
                    st.markdown(f"🎯 Threshold: **₹{alert_data['threshold_price']:,.0f}**")
            
            with col2:
                # Contact information
                if alert_data.get('email'):
                    st.markdown(f"📧 {alert_data['email']}")
                
                if alert_data.get('phone'):
                    st.markdown(f"📱 {alert_data['phone']}")
                
                # Status
                status = "🟢 Active" if alert_data.get('is_active', True) else "🔴 Inactive"
                st.markdown(f"Status: {status}")
            
            with col3:
                if st.button("🗑️ Delete", key=f"{key_prefix}_delete_{alert_data.get('id', '')}"):
                    return "delete"
                
                if st.button("⏸️ Pause" if alert_data.get('is_active', True) else "▶️ Resume", 
                           key=f"{key_prefix}_toggle_{alert_data.get('id', '')}"):
                    return "toggle"
        
        return None

class SearchSuggestions:
    """Search suggestions component"""
    
    @staticmethod
    def render(suggestions: List[str], current_query: str = ""):
        """Render search suggestions"""
        if not suggestions:
            return None
        
        st.markdown("💡 **Search Suggestions:**")
        
        # Create columns for suggestions
        cols = st.columns(min(len(suggestions), 4))
        
        selected_suggestion = None
        
        for i, suggestion in enumerate(suggestions[:4]):
            with cols[i]:
                if st.button(f"🎯 {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                    selected_suggestion = suggestion
        
        return selected_suggestion

class MetricsGrid:
    """Grid of metrics component"""
    
    @staticmethod
    def render(metrics: Dict[str, any], columns: int = 4):
        """Render metrics in a grid layout"""
        cols = st.columns(columns)
        
        metric_items = list(metrics.items())
        for i, (label, value) in enumerate(metric_items):
            with cols[i % columns]:
                if isinstance(value, dict):
                    # If value is a dict, it should contain 'value' and optionally 'delta'
                    metric_value = value.get('value', 0)
                    delta = value.get('delta', None)
                    delta_color = value.get('delta_color', None)
                    
                    st.metric(label, metric_value, delta=delta, delta_color=delta_color)
                else:
                    st.metric(label, value)

class DataTable:
    """Enhanced data table component"""
    
    @staticmethod
    def render(data: List[Dict], title: str = "", searchable: bool = True, 
               sortable: bool = True, paginated: bool = True, page_size: int = 10):
        """Render enhanced data table"""
        if not data:
            st.info(f"No data available for {title}")
            return
        
        df = pd.DataFrame(data)
        
        if title:
            st.subheader(title)
        
        # Search functionality
        if searchable and len(df) > 0:
            search_term = st.text_input("🔍 Search in table", key=f"search_{title}")
            if search_term:
                # Search across all string columns
                string_columns = df.select_dtypes(include=['object']).columns
                mask = df[string_columns].astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                df = df[mask]
        
        # Sorting
        if sortable and len(df) > 0:
            col1, col2 = st.columns(2)
            with col1:
                sort_column = st.selectbox("Sort by", options=df.columns, key=f"sort_col_{title}")
            with col2:
                sort_order = st.selectbox("Order", options=["Ascending", "Descending"], key=f"sort_order_{title}")
            
            ascending = sort_order == "Ascending"
            df = df.sort_values(by=sort_column, ascending=ascending)
        
        # Pagination
        if paginated and len(df) > page_size:
            total_pages = (len(df) - 1) // page_size + 1
            page = st.number_input(f"Page (1-{total_pages})", min_value=1, max_value=total_pages, value=1, key=f"page_{title}") - 1
            start_idx = page * page_size
            end_idx = start_idx + page_size
            df_display = df.iloc[start_idx:end_idx]
            
            st.info(f"Showing {start_idx + 1}-{min(end_idx, len(df))} of {len(df)} records")
        else:
            df_display = df
        
        # Display table
        st.dataframe(df_display, use_container_width=True)
        
        return df_display

class FilterPanel:
    """Filter panel component"""
    
    @staticmethod
    def render(filter_options: Dict, title: str = "Filters"):
        """Render filter panel"""
        with st.expander(f"🔧 {title}", expanded=False):
            filters = {}
            
            for filter_name, filter_config in filter_options.items():
                filter_type = filter_config.get('type', 'text')
                label = filter_config.get('label', filter_name.title())
                
                if filter_type == 'text':
                    filters[filter_name] = st.text_input(
                        label, 
                        value=filter_config.get('default', ''),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_type == 'number':
                    filters[filter_name] = st.number_input(
                        label,
                        min_value=filter_config.get('min_value', 0),
                        max_value=filter_config.get('max_value', 1000000),
                        value=filter_config.get('default', 0),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_type == 'select':
                    filters[filter_name] = st.selectbox(
                        label,
                        options=filter_config.get('options', []),
                        index=filter_config.get('default_index', 0),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_type == 'multiselect':
                    filters[filter_name] = st.multiselect(
                        label,
                        options=filter_config.get('options', []),
                        default=filter_config.get('default', []),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_type == 'date':
                    filters[filter_name] = st.date_input(
                        label,
                        value=filter_config.get('default', datetime.now().date()),
                        key=f"filter_{filter_name}"
                    )
                
                elif filter_type == 'range':
                    min_val = filter_config.get('min_value', 0)
                    max_val = filter_config.get('max_value', 100)
                    default_range = filter_config.get('default', [min_val, max_val])
                    
                    filters[filter_name] = st.slider(
                        label,
                        min_value=min_val,
                        max_value=max_val,
                        value=default_range,
                        key=f"filter_{filter_name}"
                    )
            
            return filters

class StatusIndicator:
    """Status indicator component"""
    
    @staticmethod
    def render(status: str, message: str = "", show_time: bool = True):
        """Render status indicator"""
        status_configs = {
            'success': {'icon': '✅', 'color': 'green'},
            'error': {'icon': '❌', 'color': 'red'},
            'warning': {'icon': '⚠️', 'color': 'orange'},
            'info': {'icon': 'ℹ️', 'color': 'blue'},
            'loading': {'icon': '⏳', 'color': 'gray'}
        }
        
        config = status_configs.get(status, status_configs['info'])
        
        status_text = f"{config['icon']} {message}"
        
        if show_time:
            current_time = datetime.now().strftime("%H:%M:%S")
            status_text += f" ({current_time})"
        
        if status == 'success':
            st.success(status_text)
        elif status == 'error':
            st.error(status_text)
        elif status == 'warning':
            st.warning(status_text)
        else:
            st.info(status_text)

class ProgressTracker:
    """Progress tracking component"""
    
    @staticmethod
    def render(current: int, total: int, title: str = "Progress", show_percentage: bool = True):
        """Render progress tracker"""
        if total == 0:
            progress = 0
            percentage = 0
        else:
            progress = current / total
            percentage = (current / total) * 100
        
        st.markdown(f"**{title}**")
        
        if show_percentage:
            st.progress(progress, text=f"{current}/{total} ({percentage:.1f}%)")
        else:
            st.progress(progress, text=f"{current}/{total}")

class ExportOptions:
    """Export options component"""
    
    @staticmethod
    def render(data, filename_prefix: str = "export"):
        """Render export options"""
        st.markdown("### 📤 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export CSV", use_container_width=True):
                if isinstance(data, pd.DataFrame):
                    csv = data.to_csv(index=False)
                else:
                    df = pd.DataFrame(data)
                    csv = df.to_csv(index=False)
                
                st.download_button(
                    "💾 Download CSV",
                    csv,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Export JSON", use_container_width=True):
                if isinstance(data, pd.DataFrame):
                    json_data = data.to_json(orient='records', indent=2)
                else:
                    json_data = json.dumps(data, indent=2, default=str)
                
                st.download_button(
                    "💾 Download JSON",
                    json_data,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("📈 Export Report", use_container_width=True):
                # Generate HTML report
                html_report = ExportOptions._generate_html_report(data, filename_prefix)
                
                st.download_button(
                    "💾 Download Report",
                    html_report,
                    file_name=f"{filename_prefix}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )
    
    @staticmethod
    def _generate_html_report(data, title: str) -> str:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title} Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 10px; }}
                .data-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .data-table th {{ background-color: #4CAF50; color: white; }}
                .footer {{ text-align: center; margin-top: 40px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 {title} Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
        """
        
        if isinstance(data, pd.DataFrame):
            html += data.to_html(classes='data-table', escape=False)
        elif isinstance(data, list) and data:
            df = pd.DataFrame(data)
            html += df.to_html(classes='data-table', escape=False)
        else:
            html += f"<pre>{json.dumps(data, indent=2, default=str)}</pre>"
        
        html += """
            </div>
            
            <div class="footer">
                <p>Generated by Smart Shopping Assistant</p>
            </div>
        </body>
        </html>
        """
        
        return html

class NotificationBanner:
    """Notification banner component"""
    
    @staticmethod
    def render():
        """Render notification banner for alerts"""
        # This would typically check for recent alerts
        # For demo purposes, showing static example
        
        if st.session_state.get('show_alert_banner', False):
            alert_type = st.session_state.get('alert_type', 'info')
            alert_message = st.session_state.get('alert_message', 'New notification')
            
            if alert_type == 'price_drop':
                st.success(f"🎉 {alert_message}")
            elif alert_type == 'error':
                st.error(f"❌ {alert_message}")
            elif alert_type == 'warning':
                st.warning(f"⚠️ {alert_message}")
            else:
                st.info(f"ℹ️ {alert_message}")
            
            # Clear the banner after showing
            if st.button("✕", key="close_banner"):
                st.session_state.show_alert_banner = False
                st.rerun()

# Helper function to initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if 'show_alert_banner' not in st.session_state:
        st.session_state.show_alert_banner = False
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ''
    
    if 'user_phone' not in st.session_state:
        st.session_state.user_phone = ''
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'tracked_products' not in st.session_state:
        st.session_state.tracked_products = []
