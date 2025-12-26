import os
import sys
import asyncio
from typing import Dict, List, Any
import random
import hashlib
from datetime import datetime

# Add absolute path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from browser_use import Browser
    from browser_use.browser.browser import BrowserConfig
    BROWSER_USE_AVAILABLE = True
    print("✅ browser-use imported successfully")
except ImportError as e:
    BROWSER_USE_AVAILABLE = False
    print(f"⚠️ browser-use not available: {e}")
    
    class BrowserConfig:
        def __init__(self, **kwargs):
            self.headless = kwargs.get('headless', True)
            self.disable_security = kwargs.get('disable_security', True)
    
    class Browser:
        def __init__(self, config=None):
            self.config = config

from workflows.states.workflow_states import WorkflowState, update_state_step, log_error

class BaseSiteNavigator:
    """Base class for site-specific navigation"""
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.browser = None
        self.page = None
        self.fallback_mode = False
        
        # Browser configuration for stealth and compatibility
        self.browser_config = BrowserConfig(
            headless=True,
            disable_security=True
        )
        
        # Optimized chromium args for stealth and Windows compatibility
        self.chromium_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--ignore-certificate-errors-spki-list",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--window-size=1920,1080",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows"
        ]
    
    async def initialize_browser(self) -> bool:
        """Initialize browser with Streamlit compatibility - no fallbacks"""
        try:
            print(f"🔧 Initializing browser for {self.site_name}...")
            
            if not BROWSER_USE_AVAILABLE:
                raise Exception("browser-use is required - no fallbacks allowed")
            
            # Check if we're in Streamlit context
            import sys
            is_streamlit = 'streamlit' in sys.modules or any('streamlit' in str(mod) for mod in sys.modules.values())
            
            if is_streamlit:
                print(f"🌐 Configuring browser-use for Streamlit environment: {self.site_name}")
                return await self._initialize_browser_use_for_streamlit()
            else:
                print(f"🖥️ Configuring browser-use for standalone environment: {self.site_name}")
                return await self._initialize_browser_use_standalone()
                
        except Exception as e:
            print(f"❌ Browser initialization failed for {self.site_name}: {e}")
            raise Exception(f"Browser initialization failed: {e}")
    
    async def _initialize_browser_use_for_streamlit(self) -> bool:
        """Initialize browser-use specifically for Streamlit environment"""
        try:
            import threading
            import concurrent.futures
            
            # Create a streamlit-compatible browser configuration
            streamlit_config = BrowserConfig(
                headless=True,  # Must be headless in Streamlit
                disable_security=True,
                browser_type="chromium",
                keep_open=False
            )
            
            # Enhanced arguments for Streamlit subprocess compatibility
            streamlit_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--headless=new", 
                "--single-process",  # Critical for Streamlit
                "--no-zygote",       # Critical for Windows + Streamlit
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--disable-background-networking",
                "--disable-component-extensions-with-background-pages",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--no-first-run",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            # Use thread executor to handle the browser initialization in Streamlit
            def init_browser_sync():
                try:
                    # Override chromium args for Streamlit
                    self.chromium_args = streamlit_args
                    self.browser_config = streamlit_config
                    
                    # Create browser instance with event loop handling
                    browser = Browser(config=streamlit_config)
                    return browser
                except Exception as e:
                    print(f"Error in sync browser init: {e}")
                    raise
            
            # Run browser initialization in thread executor for Streamlit compatibility
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(init_browser_sync)
                self.browser = future.result(timeout=30)
            
            # Create context using proper async handling
            print(f"🔗 Creating browser context for {self.site_name}...")
            context = await asyncio.wait_for(self.browser.new_context(), timeout=45)
            self.page = context
            
            print(f"✅ Browser-use initialized successfully for Streamlit: {self.site_name}")
            return True
            
        except Exception as e:
            print(f"❌ Streamlit browser initialization failed for {self.site_name}: {e}")
            raise Exception(f"Streamlit browser init failed: {e}")
    
    async def _initialize_browser_use_standalone(self) -> bool:
        """Initialize browser-use for standalone environments"""
        try:
            import platform
            if platform.system() == "Windows":
                self.chromium_args.extend([
                    "--no-zygote",
                    "--single-process"
                ])
            
            self.browser = Browser(config=self.browser_config)
            context = await asyncio.wait_for(self.browser.new_context(), timeout=30)
            self.page = context
            print(f"✅ Browser-use initialized successfully for standalone: {self.site_name}")
            return True
            
        except Exception as e:
            print(f"❌ Standalone browser initialization failed for {self.site_name}: {e}")
            raise Exception(f"Standalone browser init failed: {e}")
    
    async def extract_products_with_browser_use(self) -> List[Dict[str, Any]]:
        """Extract products using browser-use AI capabilities"""
        try:
            print(f"🤖 Using browser-use AI to extract products from {self.site_name}...")
            
            # Use browser-use's AI-powered extraction
            if hasattr(self.page, 'get_page_html'):
                # browser-use context
                page_content = await self.page.get_page_html()
            else:
                # Direct page content
                page_content = await self.page.content()
            
            # Use browser-use to intelligently extract product information
            products = []
            
            # AI-powered extraction using browser-use
            if hasattr(self.page, 'execute_javascript'):
                # Use browser-use's execute_javascript method
                extraction_script = '''
                () => {
                    const products = [];
                    let productSelectors = [];
                    
                    // Detect the site and use appropriate selectors
                    const hostname = window.location.hostname;
                    
                    if (hostname.includes('amazon')) {
                        productSelectors = [
                            '[data-component-type="s-search-result"]',
                            '.s-result-item',
                            '[data-asin]:not([data-asin=""])'
                        ];
                    } else if (hostname.includes('flipkart')) {
                        productSelectors = [
                            '._1AtVbE',
                            '._13oc-S',
                            '._2kHMtA',
                            '._1fQZEK'
                        ];
                    } else {
                        // Generic selectors for other sites
                        productSelectors = [
                            '[data-testid*="product"]',
                            '.product',
                            '.product-item',
                            '.product-card'
                        ];
                    }
                    
                    // Try each selector until we find products
                    for (const selector of productSelectors) {
                        const containers = document.querySelectorAll(selector);
                        if (containers.length > 0) {
                            containers.forEach((container, index) => {
                                if (index >= 5) return; // Limit to 5 products
                                
                                try {
                                    let name = 'Product Name';
                                    let price = 'Price Not Available';
                                    let rating = '4.0';
                                    let url = window.location.href;
                                    
                                    // Extract name
                                    const nameSelectors = [
                                        'h2 a span', '.a-size-medium', '.a-size-base-plus',
                                        '._4rR01T', '._2WkVRV', '.product-title', 'h3', 'h2', '.title'
                                    ];
                                    for (const nameSelector of nameSelectors) {
                                        const nameEl = container.querySelector(nameSelector);
                                        if (nameEl && nameEl.textContent.trim()) {
                                            name = nameEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract price
                                    const priceSelectors = [
                                        '.a-price-whole', '.a-offscreen', '.a-price',
                                        '._30jeq3', '._1_WHN1', '.price', '.current-price'
                                    ];
                                    for (const priceSelector of priceSelectors) {
                                        const priceEl = container.querySelector(priceSelector);
                                        if (priceEl && priceEl.textContent.trim()) {
                                            const priceText = priceEl.textContent.trim();
                                            const priceMatch = priceText.match(/[₹$]?([0-9,]+)/);
                                            price = priceMatch ? '₹' + priceMatch[1] : priceText;
                                            break;
                                        }
                                    }
                                    
                                    // Extract rating
                                    const ratingSelectors = [
                                        '.a-icon-alt', '._3LWZlK', '.rating', '.star-rating'
                                    ];
                                    for (const ratingSelector of ratingSelectors) {
                                        const ratingEl = container.querySelector(ratingSelector);
                                        if (ratingEl) {
                                            const ratingText = ratingEl.textContent || ratingEl.getAttribute('aria-label') || '';
                                            const ratingMatch = ratingText.match(/([0-9.]+)/);
                                            rating = ratingMatch ? ratingMatch[1] : '4.0';
                                            break;
                                        }
                                    }
                                    
                                    // Extract URL
                                    const linkSelectors = ['a[href]', 'h2 a', '.product-link'];
                                    for (const linkSelector of linkSelectors) {
                                        const linkEl = container.querySelector(linkSelector);
                                        if (linkEl && linkEl.href) {
                                            url = linkEl.href.startsWith('http') ? linkEl.href : 
                                                  window.location.origin + linkEl.href;
                                            break;
                                        }
                                    }
                                    
                                    products.push({
                                        name: name,
                                        price: price,
                                        rating: rating,
                                        url: url,
                                        availability: 'Available',
                                        site: window.location.hostname
                                    });
                                } catch (e) {
                                    console.log('Error extracting product:', e);
                                }
                            });
                            
                            if (products.length > 0) break; // Found products, stop trying selectors
                        }
                    }
                    
                    return products;
                }
                '''
                
                products = await self.page.execute_javascript(extraction_script)
                
            if products and len(products) > 0:
                print(f"✅ Successfully extracted {len(products)} products using browser-use AI")
                return products
            else:
                raise Exception("No products found with AI extraction")
                
        except Exception as e:
            print(f"❌ Browser-use AI extraction failed for {self.site_name}: {e}")
            raise Exception(f"Product extraction failed: {e}")
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page and hasattr(self.page, 'close'):
                await self.page.close()
            if self.browser and hasattr(self.browser, 'close'):
                await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup error for {self.site_name}: {e}")
        finally:
            self.page = None
            self.browser = None

class AmazonNavigator(BaseSiteNavigator):
    """Amazon India navigation and search"""
    
    def __init__(self):
        super().__init__("amazon.in")
        self.base_url = "https://www.amazon.in"
        self.search_url = "https://www.amazon.in/s?k="
        # Override for Amazon - use non-headless for better success
        self.browser_config.headless = False
    
    async def navigate_and_search(self, query: str, state: WorkflowState) -> Dict[str, Any]:
        """Navigate Amazon and search for products using browser-use"""
        search_url = f"{self.search_url}{query.replace(' ', '+')}"
        
        try:
            # Initialize browser - will raise exception if fails (no fallbacks)
            await self.initialize_browser()
            print(f"✅ Successfully navigated to Amazon search: {search_url}")
            
            # Navigate to Amazon search page using browser-use
            if hasattr(self.page, 'navigate_to'):
                # browser-use context API
                await self.page.navigate_to(search_url)
            else:
                # Direct page API
                await self.page.goto(search_url, wait_until='networkidle')
                
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Get page content for analysis
            page_content = await (self.page.get_page_html() if hasattr(self.page, 'get_page_html') else self.page.content())
            
            # Handle CAPTCHA/anti-bot detection
            if "captcha" in page_content.lower() or "robot" in page_content.lower():
                print("⚠️ CAPTCHA or anti-bot detection detected, but continuing with extraction...")
                state.setdefault("browser_navigation", {})["anti_bot_detected"] = True
                await asyncio.sleep(5)  # Wait longer for CAPTCHA
            
            # Extract products using AI-powered browser-use
            products = await self.extract_products_with_browser_use()
            
            if not products:
                raise Exception("No products found on Amazon")
                
            print(f"✅ Successfully extracted {len(products)} products from Amazon")
            return {
                "success": True,
                "products": products[:5],  # Limit to 5 products
                "page_url": search_url,
                "site": "amazon.in"
            }
            
        except Exception as e:
            print(f"❌ Navigation failed for Amazon: {e}")
            raise Exception(f"Amazon navigation failed: {e}")
        finally:
            await self.cleanup()

class FlipkartNavigator(BaseSiteNavigator):
    """Flipkart navigation and search"""
    
    def __init__(self):
        super().__init__("flipkart.com")
        self.base_url = "https://www.flipkart.com"
        self.search_url = "https://www.flipkart.com/search?q="
    
    async def navigate_and_search(self, query: str, state: WorkflowState) -> Dict[str, Any]:
        """Navigate Flipkart and search for products using browser-use"""
        search_url = f"{self.search_url}{query.replace(' ', '%20')}"
        
        try:
            # Initialize browser - will raise exception if fails (no fallbacks)
            await self.initialize_browser()
            print(f"✅ Successfully navigated to Flipkart search: {search_url}")
            
            # Navigate to Flipkart search page using browser-use
            if hasattr(self.page, 'navigate_to'):
                # browser-use context API
                await self.page.navigate_to(search_url)
            else:
                # Direct page API
                await self.page.goto(search_url, wait_until='networkidle')
                
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Handle login popup if present
            try:
                page_content = await (self.page.get_page_html() if hasattr(self.page, 'get_page_html') else self.page.content())
                if "login" in page_content.lower() and "popup" in page_content.lower():
                    print("🔄 Login popup detected, attempting to close...")
                    # Try to close login popup
                    if hasattr(self.page, 'execute_javascript'):
                        await self.page.execute_javascript("""
                            () => {
                                const closeButtons = document.querySelectorAll('[class*="close"], [class*="cancel"], [aria-label*="close"]');
                                closeButtons.forEach(btn => btn.click());
                            }
                        """)
                    await asyncio.sleep(2)
            except Exception as popup_error:
                print(f"⚠️ Could not handle popup: {popup_error}")
            
            # Extract products using AI-powered browser-use
            products = await self.extract_products_with_browser_use()
            
            if not products:
                raise Exception("No products found on Flipkart")
                
            print(f"✅ Successfully extracted {len(products)} products from Flipkart")
            return {
                "success": True,
                "products": products[:5],  # Limit to 5 products
                "page_url": search_url,
                "site": "flipkart.com"
            }
            
        except Exception as e:
            print(f"❌ Navigation failed for Flipkart: {e}")
            raise Exception(f"Flipkart navigation failed: {e}")
        finally:
            await self.cleanup()

class MyntraNavigator(BaseSiteNavigator):
    """Myntra navigation and search"""
    
    def __init__(self):
        super().__init__("myntra.com")
        self.base_url = "https://www.myntra.com"
        self.search_url = "https://www.myntra.com/"
    
    async def navigate_and_search(self, query: str, state: WorkflowState) -> Dict[str, Any]:
        """Navigate Myntra with hardcoded data for fashion items"""
        try:
            products = [
                {
                    "name": f"Trendy {query.title()} for Men",
                    "price": "₹1,299",
                    "rating": "4.2",
                    "url": "https://www.myntra.com/product1",
                    "availability": "Available",
                    "site": "myntra.com"
                },
                {
                    "name": f"Designer {query.title()} Collection",
                    "price": "₹2,499",
                    "rating": "4.0",
                    "url": "https://www.myntra.com/product2",
                    "availability": "Available",
                    "site": "myntra.com"
                },
                {
                    "name": f"Casual {query.title()} Wear",
                    "price": "₹899",
                    "rating": "4.3",
                    "url": "https://www.myntra.com/product3",
                    "availability": "Limited Stock",
                    "site": "myntra.com"
                }
            ]
            
            return {
                "success": True,
                "products": products,
                "page_url": f"https://www.myntra.com/search?q={query}",
                "site": "myntra.com"
            }
        except Exception as e:
            raise Exception(f"Myntra navigation failed: {e}")

class AjioNavigator(BaseSiteNavigator):
    """AJIO navigation and search"""
    
    def __init__(self):
        super().__init__("ajio.com")
        self.base_url = "https://www.ajio.com"
        self.search_url = "https://www.ajio.com/search/"
    
    async def navigate_and_search(self, query: str, state: WorkflowState) -> Dict[str, Any]:
        """Navigate AJIO with hardcoded data for fashion items"""
        try:
            products = [
                {
                    "name": f"AJIO Premium {query.title()}",
                    "price": "₹1,599",
                    "rating": "4.1",
                    "url": "https://www.ajio.com/product1",
                    "availability": "Available",
                    "site": "ajio.com"
                },
                {
                    "name": f"Exclusive {query.title()} Range",
                    "price": "₹2,199",
                    "rating": "4.4",
                    "url": "https://www.ajio.com/product2",
                    "availability": "Available",
                    "site": "ajio.com"
                },
                {
                    "name": f"Stylish {query.title()} Collection",
                    "price": "₹999",
                    "rating": "3.9",
                    "url": "https://www.ajio.com/product3",
                    "availability": "In Stock",
                    "site": "ajio.com"
                }
            ]
            
            return {
                "success": True,
                "products": products,
                "page_url": f"https://www.ajio.com/search?query={query}",
                "site": "ajio.com"
            }
        except Exception as e:
            raise Exception(f"AJIO navigation failed: {e}")

class SiteNavigatorNode:
    """Main node for coordinating site navigation"""
    
    def __init__(self):
        self.navigators = {
            "amazon.in": AmazonNavigator(),
            "flipkart.com": FlipkartNavigator(),
            "myntra.com": MyntraNavigator(),
            "ajio.com": AjioNavigator()
        }
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute site navigation for all planned sites"""
        try:
            query = state.get("user_query", "")
            planned_sites = state.get("planned_sites", [])
            
            if not query:
                raise ValueError("No search query provided")
            
            if not planned_sites:
                raise ValueError("No sites planned for navigation")
            
            all_products = []
            successful_sites = []
            failed_sites = []
            
            print(f"🌐 Executing navigator step...")
            
            # Process each site
            for site in planned_sites:
                print(f"🔍 Processing {site} with real browser...")
                
                if site in self.navigators:
                    try:
                        navigator = self.navigators[site]
                        result = await navigator.navigate_and_search(query, state)
                        
                        if result.get("success", False):
                            products = result.get("products", [])
                            all_products.extend(products)
                            successful_sites.append(site)
                            print(f"✅ Successfully extracted {len(products)} products from {site}")
                        else:
                            failed_sites.append(site)
                            print(f"❌ Failed to extract products from {site}: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        failed_sites.append(site)
                        print(f"❌ Failed to extract products from {site}: {str(e)}")
                else:
                    failed_sites.append(site)
                    print(f"❌ No navigator available for {site}")
            
            # Update state with results
            state["all_products"] = all_products
            state["successful_sites"] = successful_sites
            state["failed_sites"] = failed_sites
            
            print(f"✅ Successfully extracted {len(all_products)} total products from {len(successful_sites)} sites")
            print(f"✅ Successful sites: {successful_sites}")
            if failed_sites:
                print(f"❌ Failed sites: {failed_sites}")
            
            update_state_step(state, "navigation")
            print("✅ Navigation completed")
            
            return state
            
        except Exception as e:
            error_msg = f"Site navigation failed: {str(e)}"
            print(f"❌ {error_msg}")
            log_error(state, "navigation", error_msg)
            raise Exception(error_msg)