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
        return {
            "place_id": place_id,
            "website_status": "error",
            "audit_status": "failed",
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
            },
            "audit_error": "No website URL provided"
        }
        
    try:
        from playwright.sync_api import sync_playwright
        logger.info(f"Starting Playwright audit for: {website_url}")
        
        start_time = time.time()
        
        # Format screenshots paths
        desktop_filename = f"{place_id}_desktop.png"
        mobile_filename = f"{place_id}_mobile.png"
        
        desktop_path = os.path.join(SCREENSHOT_DIR, desktop_filename)
        mobile_path = os.path.join(SCREENSHOT_DIR, mobile_filename)
        
        is_https = website_url.lower().startswith("https")
        website_status = 200
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            context.set_default_timeout(45000) # 45 seconds hard timeout for operations
            page = context.new_page()
            
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            try:
                response = page.goto(website_url, wait_until="domcontentloaded", timeout=30000)
                website_status = response.status if response else 200
            except Exception as e:
                logger.warning(f"Playwright navigation failed: {e}. Trying simple HTTP request.")
                try:
                    res = requests.get(website_url, timeout=10)
                    website_status = res.status_code
                except:
                    website_status = "timeout"
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            title = ""
            meta_description = ""
            canonical = ""
            h1_hierarchy = []
            has_robots = False
            has_sitemap = False
            is_mobile_friendly = False
            has_hero_section = False
            has_cta = False
            has_footer = False
            tech_detected = {k: False for k in ["bookingSystem", "whatsapp", "chatWidget", "crm", "paymentGateway", "newsletter", "facebookPixel", "googleAnalytics"]}
            emails = []
            social_links = {"linkedin": "", "facebook": "", "instagram": "", "twitter": "", "youtube": ""}
            
            if website_status != "timeout":
                try:
                    title = page.title()
                    meta_desc_el = page.locator('meta[name="description"]').first
                    if meta_desc_el.count() > 0:
                        meta_description = meta_desc_el.get_attribute("content") or ""
                        
                    canonical_el = page.locator('link[rel="canonical"]').first
                    if canonical_el.count() > 0:
                        canonical = canonical_el.get_attribute("href") or ""
                        
                    h1s = page.locator('h1').all_inner_texts()
                    h1_hierarchy = [text.strip() for text in h1s if text.strip()]
                    
                    parsed_url = urlparse(website_url)
                    root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    try:
                        has_robots = requests.get(f"{root_url}/robots.txt", timeout=3).status_code == 200
                        has_sitemap = requests.get(f"{root_url}/sitemap.xml", timeout=3).status_code == 200
                    except:
                        pass
                        
                    viewport_el = page.locator('meta[name="viewport"]').first
                    is_mobile_friendly = viewport_el.count() > 0
                    
                    body_html = page.content().lower()
                    has_hero_section = "hero" in body_html or "jumbotron" in body_html or "banner" in body_html
                    has_cta = "button" in body_html or "btn" in body_html or "get started" in body_html or "sign up" in body_html
                    has_footer = "footer" in body_html or "©" in body_html or "copyright" in body_html
                    
                    tech_detected["bookingSystem"] = any(x in body_html for x in ["calendly", "acuityscheduling", "booksy", "setmore", "vagaro"])
                    tech_detected["whatsapp"] = any(x in body_html for x in ["wa.me", "api.whatsapp.com", "whatsapp.com/send"])
                    tech_detected["chatWidget"] = any(x in body_html for x in ["tidio", "crisp.chat", "intercom", "hubspot", "livechat", "tawk.to"])
                    tech_detected["crm"] = any(x in body_html for x in ["hubspot", "salesforce", "activecampaign", "pipedrive"])
                    tech_detected["paymentGateway"] = any(x in body_html for x in ["stripe", "paypal", "square", "shopify", "checkout"])
                    tech_detected["newsletter"] = any(x in body_html for x in ["subscribe", "newsletter", "mailchimp", "klaviyo"])
                    tech_detected["facebookPixel"] = "connect.facebook.net" in body_html
                    tech_detected["googleAnalytics"] = any(x in body_html for x in ["google-analytics", "googletagmanager", "gtag.js"])
                    
                    import re
                    emails_found = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body_html)))
                    emails = [e for e in emails_found if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
                    
                    social_links = {
                        "linkedin": _find_social(page, "linkedin.com"),
                        "facebook": _find_social(page, "facebook.com"),
                        "instagram": _find_social(page, "instagram.com"),
                        "twitter": _find_social(page, "twitter.com") or _find_social(page, "x.com"),
                        "youtube": _find_social(page, "youtube.com")
                    }
                    
                    try:
                        page.screenshot(path=desktop_path, timeout=10000)
                    except:
                        pass
                except Exception as eval_e:
                    logger.warning(f"Error during page evaluation: {eval_e}")
            
            page.close()
            context.close()
            
            # Mobile Audit
            mobile_context = browser.new_context(
                viewport={"width": 375, "height": 812},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
            )
            mobile_context.set_default_timeout(30000)
            mobile_page = mobile_context.new_page()
            try:
                if website_status != "timeout":
                    mobile_page.goto(website_url, wait_until="domcontentloaded", timeout=20000)
                    mobile_page.screenshot(path=mobile_path, timeout=10000)
            except:
                pass
            finally:
                mobile_page.close()
                mobile_context.close()
                
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
        logger.error(f"Playwright audit failed entirely: {e}")
        # Return a failed audit state instead of simulated data
        return {
            "place_id": place_id,
            "website_status": "timeout",
            "audit_status": "timeout",
            "is_https": False,
            "response_time_ms": 0,
            "audit_error": str(e),
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
