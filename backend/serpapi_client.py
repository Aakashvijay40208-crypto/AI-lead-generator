import logging
import random
import requests
from urllib.parse import urlparse
from api_manager import get_api_key, disable_key

logger = logging.getLogger(__name__)

def search_and_enrich_businesses(category, city, area=None, radius=None, limit=5):
    """
    Search for businesses using SerpAPI (Google Maps), 
    and return structured lists of businesses.
    Falls back to mock mode if keys are missing or api fails.
    """
    api_key = get_api_key("serpapi")
    
    # Construct search query
    query = f"{category}"
    if area:
        query += f" in {area}"
    query += f", {city}"
    
    if not api_key:
        logger.info("SerpAPI key missing. Returning empty results.")
        return []
        
    try:
        logger.info(f"Running SerpAPI Google Maps search for: '{query}', limit: {limit}")
        
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": query,
            "type": "search",
            "api_key": api_key,
            "num": limit  # Some engines support num, but google maps returns up to 20 per page usually
        }
        
        # Adding a timeout for the API call
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 401 or response.status_code == 403:
            logger.error("SerpAPI auth failed (invalid key or quota).")
            disable_key("serpapi", api_key)
            return []
            
        response.raise_for_status()
        data = response.json()
        
        local_results = data.get("local_results", [])
        
        enriched_leads = []
        seen_place_ids = set()
        
        for item in local_results:
            place_id = item.get("place_id") or f"place_{random.randint(100000, 999999)}"
            
            # Duplicate detection
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)
            
            website = item.get("website") or ""
            
            lat = item.get("gps_coordinates", {}).get("latitude")
            lng = item.get("gps_coordinates", {}).get("longitude")
            
            # SerpAPI maps results might have 'type' or 'category'
            item_category = item.get("type", category)
            
            lead = {
                "place_id": place_id,
                "name": item.get("title", "Unknown Business"),
                "address": item.get("address", f"{city}, USA"),
                "phone_number": item.get("phone", ""),
                "website": website,
                "google_rating": float(item.get("rating", 0)) if item.get("rating") else 0.0,
                "review_count": int(item.get("reviews", 0)) if item.get("reviews") else 0,
                "latitude": float(lat) if lat else None,
                "longitude": float(lng) if lng else None,
                "category": item_category,
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
                }
            }
            
            # Note: SerpAPI does not provide native email/social enrichment from the website domain
            # We rely on our playwright_auditor to extract emails and socials when the site is audited.
            # So we just pass the basic lead, and the auditor will merge in the missing contacts.
            
            enriched_leads.append(lead)
            
            if len(enriched_leads) >= limit:
                break
                
        return enriched_leads
        
    except Exception as e:
        logger.error(f"SerpAPI search failed: {e}. Disabling key and returning empty results.")
        disable_key("serpapi", api_key)
        return []

def get_domain_from_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""

