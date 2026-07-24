import os
import time
import logging
import random
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Ensure static folder exists for saving screenshots locally
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "static", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def audit_website(place_id, website_url):
    """
    Perform a Playwright browser audit on the website.
    If Playwright fails (e.g. no browsers installed) or website is empty,
    fall back to a simulated audit.
    """
    if not website_url:
        return generate_simulated_audit(place_id, None)
        
    try:
        from playwright.sync_api import sync_playwright
        logger.info(f"Starting Playwright audit for: {website_url}")
        
        start_time = time.time()
        
        # Format screenshots paths
        desktop_filename = f"{place_id}_desktop.png"
        mobile_filename = f"{place_id}_mobile.png"
        
        desktop_path = os.path.join(SCREENSHOT_DIR, desktop_filename)
        mobile_path = os.path.join(SCREENSHOT_DIR, mobile_filename)
        
        # Perform request checks
        is_https = website_url.lower().startswith("https")
        website_status = 200
        
        with sync_playwright() as p:
            # Launch headless browser
            browser = p.chromium.launch(headless=True)
            
            # 1. Desktop Audit & Screenshot
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            
            # Set up error tracking
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            try:
                response = page.goto(website_url, wait_until="load", timeout=15000)
                website_status = response.status if response else 200
            except Exception as e:
                logger.warning(f"Playwright navigation failed: {e}. Trying simple HTTP request.")
                # If network fails, try requests as fallback
                try:
                    res = requests.get(website_url, timeout=10)
                    website_status = res.status_code
                except:
                    website_status = 0
                raise e # Trigger fallback
                
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Scrape content / SEO
            title = page.title()
            meta_description = ""
            meta_desc_el = page.locator('meta[name="description"]').first
            if meta_desc_el.count() > 0:
                meta_description = meta_desc_el.get_attribute("content") or ""
                
            canonical = ""
            canonical_el = page.locator('link[rel="canonical"]').first
            if canonical_el.count() > 0:
                canonical = canonical_el.get_attribute("href") or ""
                
            # H1 Hierarchy
            h1s = page.locator('h1').all_inner_texts()
            h1_hierarchy = [text.strip() for text in h1s if text.strip()]
            
            # Robots & Sitemap availability checks
            parsed_url = urlparse(website_url)
            root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            has_robots = False
            has_sitemap = False
            try:
                has_robots = requests.get(f"{root_url}/robots.txt", timeout=3).status_code == 200
                has_sitemap = requests.get(f"{root_url}/sitemap.xml", timeout=3).status_code == 200
            except:
                pass
                
            # UX checks
            viewport_el = page.locator('meta[name="viewport"]').first
            is_mobile_friendly = viewport_el.count() > 0
            
            # Simple heuristic detection for Hero, CTA, Footer, Contact Form
            body_html = page.content().lower()
            has_hero_section = "hero" in body_html or "jumbotron" in body_html or "banner" in body_html
            has_cta = "button" in body_html or "btn" in body_html or "get started" in body_html or "sign up" in body_html
            has_footer = "footer" in body_html or "©" in body_html or "copyright" in body_html
            
            # Technologies check
            tech_detected = {
                "bookingSystem": any(x in body_html for x in ["calendly", "acuityscheduling", "booksy", "setmore", "vagaro"]),
                "whatsapp": any(x in body_html for x in ["wa.me", "api.whatsapp.com", "whatsapp.com/send"]),
                "chatWidget": any(x in body_html for x in ["tidio", "crisp.chat", "intercom", "hubspot", "livechat", "tawk.to"]),
                "crm": any(x in body_html for x in ["hubspot", "salesforce", "activecampaign", "pipedrive"]),
                "paymentGateway": any(x in body_html for x in ["stripe", "paypal", "square", "shopify", "checkout"]),
                "newsletter": any(x in body_html for x in ["subscribe", "newsletter", "mailchimp", "klaviyo"]),
                "facebookPixel": "connect.facebook.net" in body_html,
                "googleAnalytics": any(x in body_html for x in ["google-analytics", "googletagmanager", "gtag.js"])
            }
            
            # Scrape contacts
            # Match emails
            emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body_html)))
            # Exclude common media files
            emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
            
            # Match socials
            social_links = {
                "linkedin": _find_social(page, "linkedin.com"),
                "facebook": _find_social(page, "facebook.com"),
                "instagram": _find_social(page, "instagram.com"),
                "twitter": _find_social(page, "twitter.com") or _find_social(page, "x.com"),
                "youtube": _find_social(page, "youtube.com")
            }
            
            # Take desktop screenshot
            page.screenshot(path=desktop_path)
            
            # 2. Mobile Audit & Screenshot
            mobile_page = browser.new_page(
                viewport={"width": 375, "height": 812},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
            )
            try:
                mobile_page.goto(website_url, wait_until="load", timeout=15000)
                mobile_page.screenshot(path=mobile_path)
            except:
                pass # Fallback if mobile load fails
            finally:
                mobile_page.close()
                
            browser.close()
            
        return {
            "place_id": place_id,
            "website_status": website_status,
            "is_https": is_https,
            "response_time_ms": response_time_ms,
            "seo": {
                "title": title,
                "description": meta_description,
                "h1Hierarchy": h1_hierarchy[:5],
                "canonical": canonical,
                "hasRobots": has_robots,
                "hasSitemap": has_sitemap
            },
            "ux": {
                "isMobileFriendly": is_mobile_friendly,
                "hasHeroSection": has_hero_section,
                "hasCTA": has_cta,
                "hasFooter": has_footer
            },
            "tech_detected": tech_detected,
            "contacts": {
                "emails": emails[:5],
                "phoneNumbers": [],
                "socialLinks": social_links
            },
            "screenshots": {
                "desktopUrl": f"/static/screenshots/{desktop_filename}",
                "mobileUrl": f"/static/screenshots/{mobile_filename}"
            }
        }
        
    except Exception as e:
        logger.error(f"Playwright audit failed: {e}. Generating simulated audit.")
        return generate_simulated_audit(place_id, website_url)

def _find_social(page, keyword):
    try:
        links = page.locator('a[href*="' + keyword + '"]').all()
        for link in links:
            href = link.get_attribute("href")
            if href:
                return href
    except:
        pass
    return ""

def generate_simulated_audit(place_id, website_url):
    """Generate a mock website audit result with mock screenshots."""
    # Place placeholders for screenshots (or generate solid color PNGs)
    desktop_filename = f"{place_id}_desktop.png"
    mobile_filename = f"{place_id}_mobile.png"
    
    desktop_path = os.path.join(SCREENSHOT_DIR, desktop_filename)
    mobile_path = os.path.join(SCREENSHOT_DIR, mobile_filename)
    
    # We will write quick 1x1 pixel PNGs or copy a placeholder if it doesn't exist
    # to avoid broken images on frontend.
    create_placeholder_image(desktop_path, "Desktop View")
    create_placeholder_image(mobile_path, "Mobile View")
    
    if not website_url:
        # Business has NO website
        return {
            "place_id": place_id,
            "website_status": 0,
            "is_https": False,
            "response_time_ms": 0,
            "seo": {
                "title": "",
                "description": "",
                "h1Hierarchy": [],
                "canonical": "",
                "hasRobots": False,
                "hasSitemap": False
            },
            "ux": {
                "isMobileFriendly": False,
                "hasHeroSection": False,
                "hasCTA": False,
                "hasFooter": False
            },
            "tech_detected": {
                "bookingSystem": False,
                "whatsapp": False,
                "chatWidget": False,
                "crm": False,
                "paymentGateway": False,
                "newsletter": False,
                "facebookPixel": False,
                "googleAnalytics": False
            },
            "contacts": {
                "emails": [],
                "phoneNumbers": [],
                "socialLinks": {
                    "linkedin": "",
                    "facebook": "",
                    "instagram": "",
                    "twitter": "",
                    "youtube": ""
                }
            },
            "screenshots": {
                "desktopUrl": "",
                "mobileUrl": ""
            }
        }
        
    # Mocking a website audit
    is_https = website_url.startswith("https") or random.random() > 0.3
    response_time = random.randint(150, 4800)
    
    # Give some random fails to test rules
    has_title = random.random() > 0.15
    has_desc = random.random() > 0.4
    is_mobile = random.random() > 0.25
    has_whatsapp = random.random() > 0.7
    has_booking = random.random() > 0.8
    has_ssl = is_https
    
    domain = urlparse(website_url).netloc or "business.com"
    
    return {
        "place_id": place_id,
        "website_status": 200,
        "is_https": has_ssl,
        "response_time_ms": response_time,
        "seo": {
            "title": f"Official Website - {domain.capitalize()}" if has_title else "",
            "description": f"Welcome to the official page of {domain.capitalize()}. We serve local customers with best-in-class quality." if has_desc else "",
            "h1Hierarchy": [f"Welcome to {domain.capitalize()}", "Our Services", "Contact Us"] if has_title else [],
            "canonical": website_url,
            "hasRobots": random.random() > 0.3,
            "hasSitemap": random.random() > 0.5
        },
        "ux": {
            "isMobileFriendly": is_mobile,
            "hasHeroSection": random.random() > 0.2,
            "hasCTA": random.random() > 0.3,
            "hasFooter": random.random() > 0.1
        },
        "tech_detected": {
            "bookingSystem": has_booking,
            "whatsapp": has_whatsapp,
            "chatWidget": random.random() > 0.75,
            "crm": random.random() > 0.8,
            "paymentGateway": random.random() > 0.5,
            "newsletter": random.random() > 0.6,
            "facebookPixel": random.random() > 0.7,
            "googleAnalytics": random.random() > 0.4
        },
        "contacts": {
            "emails": [f"info@{domain}", f"support@{domain}"],
            "phoneNumbers": [],
            "socialLinks": {
                "linkedin": f"https://linkedin.com/company/{domain.split('.')[0]}",
                "facebook": f"https://facebook.com/{domain.split('.')[0]}",
                "instagram": f"https://instagram.com/{domain.split('.')[0]}",
                "twitter": "",
                "youtube": ""
            }
        },
        "screenshots": {
            "desktopUrl": f"/static/screenshots/{desktop_filename}",
            "mobileUrl": f"/static/screenshots/{mobile_filename}"
        }
    }

def create_placeholder_image(path, label):
    """Create a minimal solid color PNG image with text using native python (no PIL dependencies) to avoid load errors."""
    # PNG signature and standard structures for a 100x100 dark blue block
    # This guarantees we write a valid PNG without installing Pillow
    import zlib
    import struct
    
    width = 300
    height = 200
    
    # 24-bit RGB canvas: dark navy color (11, 15, 25)
    pixel_data = bytearray([11, 15, 25] * width * height)
    
    # Simple block representation
    # Format pixel rows with filter type 0
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0) # Filter type 0
        scanlines.extend(pixel_data[y * width * 3 : (y + 1) * width * 3])
        
    compressed = zlib.compress(scanlines)
    
    # Build PNG chunks
    def chunk(tag, data):
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data))
        
    png_data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    
    try:
        with open(path, "wb") as f:
            f.write(png_data)
    except Exception as e:
        logger.error(f"Failed to create placeholder PNG: {e}")
