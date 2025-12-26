import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from .models import Base, Product, PriceHistory, UserAlert, SearchQuery
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """Database manager for Smart Shopping Assistant"""
    
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_url = os.getenv("DATABASE_URL", "sqlite:///data/products.db")
        
        # Create data directory if it doesn't exist
        if "sqlite" in db_url:
            os.makedirs("data", exist_ok=True)
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def add_product(self, product_data: Dict) -> Product:
        """Add new product to database"""
        session = self.get_session()
        try:
            # Check if product already exists (active or inactive)
            existing_product = session.query(Product).filter_by(url=product_data['url']).first()
            if existing_product:
                if existing_product.is_active:
                    logger.info(f"Product already exists and is active: {existing_product.name}")
                    return existing_product
                else:
                    # Reactivate the deleted product and update its data
                    logger.info(f"Reactivating previously deleted product: {existing_product.name}")
                    existing_product.is_active = True
                    existing_product.name = product_data['name']
                    existing_product.site = product_data.get('site', existing_product.site)
                    existing_product.current_price = product_data.get('price', existing_product.current_price)
                    existing_product.rating = product_data.get('rating', existing_product.rating)
                    existing_product.image_url = product_data.get('image_url', existing_product.image_url)
                    existing_product.target_price = product_data.get('target_price', existing_product.target_price)
                    existing_product.updated_at = datetime.utcnow()
                    session.commit()
                    
                    # Add price history for reactivated product
                    if product_data.get('price'):
                        self.add_price_history(existing_product.id, product_data['price'])
                    
                    logger.info(f"Product reactivated: {existing_product.name}")
                    return existing_product
            
            product = Product(
                name=product_data['name'],
                url=product_data['url'],
                site=product_data.get('site', 'unknown'),
                current_price=product_data.get('price'),
                rating=product_data.get('rating'),
                image_url=product_data.get('image_url'),
                target_price=product_data.get('target_price')
            )
            
            session.add(product)
            session.commit()
            
            # Add initial price history
            if product_data.get('price'):
                self.add_price_history(product.id, product_data['price'])
            
            logger.info(f"Product added: {product.name}")
            return product
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding product: {e}")
            raise
        finally:
            session.close()
    
    def get_all_products(self) -> List[Product]:
        """Get all active products"""
        session = self.get_session()
        try:
            products = session.query(Product).filter_by(is_active=True).all()
            return products
        except SQLAlchemyError as e:
            logger.error(f"Error fetching products: {e}")
            return []
        finally:
            session.close()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            return product
        except SQLAlchemyError as e:
            logger.error(f"Error fetching product: {e}")
            return None
        finally:
            session.close()
    
    def find_product_by_url(self, url: str) -> Optional[Product]:
        """Find product by URL"""
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(url=url, is_active=True).first()
            return product
        except SQLAlchemyError as e:
            logger.error(f"Error finding product by URL: {e}")
            return None
        finally:
            session.close()
    
    def update_product_price(self, product_id: int, new_price: float) -> bool:
        """Update product price and add to history"""
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if product:
                product.current_price = new_price
                product.updated_at = datetime.utcnow()
                session.commit()
                
                # Add to price history
                self.add_price_history(product_id, new_price)
                logger.info(f"Price updated for {product.name}: ₹{new_price}")
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating price: {e}")
            return False
        finally:
            session.close()
    
    def add_price_history(self, product_id: int, price: float) -> PriceHistory:
        """Add price history entry"""
        session = self.get_session()
        try:
            history = PriceHistory(
                product_id=product_id,
                price=price,
                timestamp=datetime.utcnow()
            )
            session.add(history)
            session.commit()
            return history
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding price history: {e}")
            raise
        finally:
            session.close()
    
    def get_price_history(self, product_id: int, days: int = 30) -> List[PriceHistory]:
        """Get price history for product"""
        session = self.get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            history = (session.query(PriceHistory)
                      .filter_by(product_id=product_id)
                      .filter(PriceHistory.timestamp >= start_date)
                      .order_by(PriceHistory.timestamp.asc())
                      .all())
            return history
        except SQLAlchemyError as e:
            logger.error(f"Error fetching price history: {e}")
            return []
        finally:
            session.close()
    
    def update_product_target_price(self, product_id: int, target_price: float) -> bool:
        """Update product target price"""
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if product:
                product.target_price = target_price
                product.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Target price updated for {product.name}: ₹{target_price}")
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating target price: {e}")
            return False
        finally:
            session.close()

    def delete_product(self, product_id: int) -> bool:
        """Delete product (soft delete)"""
        session = self.get_session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if product:
                product.is_active = False
                session.commit()
                logger.info(f"Product deleted: {product.name}")
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting product: {e}")
            return False
        finally:
            session.close()
    
    def add_alert(self, product_id: int, alert_type: str, threshold_price: float = None, 
                  email: str = None, phone: str = None) -> UserAlert:
        """Add user alert"""
        session = self.get_session()
        try:
            alert = UserAlert(
                product_id=product_id,
                alert_type=alert_type,
                threshold_price=threshold_price,
                email=email,
                phone=phone
            )
            session.add(alert)
            session.commit()
            logger.info(f"Alert added for product {product_id}")
            return alert
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding alert: {e}")
            raise
        finally:
            session.close()
    
    def get_active_alerts(self) -> List[UserAlert]:
        """Get all active alerts"""
        session = self.get_session()
        try:
            alerts = session.query(UserAlert).filter_by(is_active=True).all()
            return alerts
        except SQLAlchemyError as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
        finally:
            session.close()
    
    def log_search_query(self, query: str, results_count: int = 0):
        """Log search query"""
        session = self.get_session()
        try:
            search = SearchQuery(
                query=query,
                results_count=results_count
            )
            session.add(search)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging search: {e}")
        finally:
            session.close()
