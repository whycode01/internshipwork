import streamlit as st
import asyncio
from dotenv import load_dotenv
import os
from ui.dashboard import SmartShoppingDashboard
from database.database import Database
from utils.price_tracker import PriceTracker

load_dotenv()

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Smart Shopping Assistant",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    db = Database()
    
    # Initialize price tracker
    price_tracker = PriceTracker(db)
    
    # Initialize dashboard
    dashboard = SmartShoppingDashboard(db, price_tracker)
    
    # Run dashboard
    dashboard.render()

if __name__ == "__main__":
    main()
