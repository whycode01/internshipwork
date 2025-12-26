from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    """Product model for storing tracked products"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    site = Column(String(100), nullable=False)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    availability = Column(Boolean, default=True)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship with price history
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(name='{self.name}', current_price={self.current_price})>"

class PriceHistory(Base):
    """Price history model for tracking price changes"""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    availability = Column(Boolean, default=True)
    source = Column(String(100), nullable=True)
    
    # Relationship with product
    product = relationship("Product", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, timestamp={self.timestamp})>"

class UserAlert(Base):
    """User alerts model for price notifications"""
    __tablename__ = 'user_alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price_drop, back_in_stock, etc.
    threshold_price = Column(Float, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with product
    product = relationship("Product")
    
    def __repr__(self):
        return f"<UserAlert(product_id={self.product_id}, alert_type='{self.alert_type}')>"

class SearchQuery(Base):
    """Search queries model for tracking user searches"""
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SearchQuery(query='{self.query}', results_count={self.results_count})>"
