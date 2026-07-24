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
        logger.info("Using simulated SerpAPI mode (No API Key).")
        return generate_mock_leads(category, city, area, limit)
        
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
            return generate_mock_leads(category, city, area, limit)
            
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
        logger.error(f"SerpAPI search failed: {e}. Disabling key and falling back to mock leads.")
        disable_key("serpapi", api_key)
        return generate_mock_leads(category, city, area, limit)

def get_domain_from_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""

def generate_mock_leads(category, city, area=None, limit=5):
    """Generate mock lead data for testing and demonstrations."""
    leads = []
    
    # Pre-defined mock data pools
    first_names = ["Apex", "Zenith", "Quantum", "Summit", "Echo", "Lumina", "Vanguard", "Delta", "Nova", "Stellar"]
    categories_dict = {
        "dentist": ["Dental Care", "Family Dentistry", "Smile Clinic", "Orthodontics"],
        "restaurant": ["Bistro", "Grill & Bar", "Kitchen", "Pizzeria", "Cafe"],
        "gym": ["Fitness Center", "CrossFit", "Athletics", "Yoga Studio", "Iron Gym"],
        "default": ["Consulting", "Solutions", "Services", "Enterprises", "Group"]
    }
    
    key_cat = "default"
    for k in categories_dict:
        if k in category.lower():
            key_cat = k
            break
            
    cat_suffixes = categories_dict[key_cat]
    
    locations = {
        "austin": {"lat": 30.2672, "lng": -97.7431, "zip": "78701"},
        "new york": {"lat": 40.7128, "lng": -74.0060, "zip": "10001"},
        "los angeles": {"lat": 34.0522, "lng": -118.2437, "zip": "90001"},
        "chicago": {"lat": 41.8781, "lng": -87.6298, "zip": "60601"},
        "default": {"lat": 37.7749, "lng": -122.4194, "zip": "94103"}
    }
    
    key_city = "default"
    for k in locations:
        if k in city.lower():
            key_city = k
            break
            
    base_coords = locations[key_city]
    
    for i in range(limit):
        prefix = random.choice(first_names)
        suffix = random.choice(cat_suffixes)
        name = f"{city.capitalize() if key_city == 'default' else prefix} {suffix}"
        
        # Add a random index if name collision is likely
        if i > 0:
            name += f" {i + 1}"
            
        place_id = f"mock_place_{random.randint(10000000, 99999999)}"
        
        # Some mock leads have no website, to test lead scoring +40pts
        has_website = random.random() > 0.35
        domain = f"{name.lower().replace(' ', '').replace('&', 'and')}.com"
        website = f"http://{domain}" if has_website else ""
        
        # Address
        street_num = random.randint(100, 9999)
        street_name = random.choice(["Main St", "Broadway", "Oak Ave", "Pine St", "Maple Dr", "Congress Ave", "Elm St"])
        address = f"{street_num} {street_name}, {city.capitalize()}, TX {base_coords['zip']}"
        
        # Phone
        phone = f"+1 (512) 555-{random.randint(1000, 9999)}"
        
        # Ratings
        rating = round(random.uniform(2.5, 4.9), 1)
        review_count = random.randint(5, 450)
        
        # Coords
        lat = base_coords["lat"] + random.uniform(-0.05, 0.05)
        lng = base_coords["lng"] + random.uniform(-0.05, 0.05)
        
        lead = {
            "place_id": place_id,
            "name": name,
            "address": address,
            "phone_number": phone,
            "website": website,
            "google_rating": rating,
            "review_count": review_count,
            "latitude": lat,
            "longitude": lng,
            "category": key_cat.capitalize(),
            "contacts": {
                "emails": [f"contact@{domain}", f"info@{domain}"] if has_website else [],
                "phoneNumbers": [phone] if has_website else [],
                "socialLinks": {
                    "linkedin": f"https://linkedin.com/company/{name.lower().replace(' ', '-')}" if has_website and random.random() > 0.4 else "",
                    "facebook": f"https://facebook.com/{name.lower().replace(' ', '-')}" if has_website and random.random() > 0.3 else "",
                    "instagram": f"https://instagram.com/{name.lower().replace(' ', '-')}" if has_website and random.random() > 0.4 else "",
                    "twitter": f"https://twitter.com/{name.lower().replace(' ', '-')}" if has_website and random.random() > 0.6 else "",
                    "youtube": ""
                }
            }
        }
        leads.append(lead)
        
    return leads
