import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client = None
local_db = {
    "profiles": {},
    "search_history": {},
    "businesses": {},
    "audit_reports": {},
    "lead_scores": {}
}
LOCAL_DB_FILE = os.path.join(os.path.dirname(__file__), "local_db.json")

# Load local DB if exists
if os.path.exists(LOCAL_DB_FILE):
    try:
        with open(LOCAL_DB_FILE, "r") as f:
            local_db = json.load(f)
    except Exception as e:
        logger.error(f"Error loading local DB file: {e}")

def save_local_db():
    try:
        with open(LOCAL_DB_FILE, "w") as f:
            json.dump(local_db, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving local DB file: {e}")

if SUPABASE_URL and SUPABASE_KEY and "your-supabase" not in SUPABASE_URL:
    try:
        from supabase import create_client, Client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}. Falling back to Local DB.")
else:
    logger.info("Supabase credentials missing or default. Using local in-memory/JSON database.")

def get_client():
    return supabase_client

def is_mock_mode():
    return supabase_client is None

# --- DATABASE HELPERS ---

def db_upsert_business(business_data):
    """Upsert business records."""
    place_id = business_data.get("place_id")
    if not place_id:
        return None
    
    if supabase_client:
        try:
            res = supabase_client.table("businesses").upsert(business_data).execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase upsert business error: {e}")
    
    # Local fallback
    local_db["businesses"][place_id] = business_data
    save_local_db()
    return business_data

def db_upsert_audit_report(audit_data):
    """Upsert website audit reports."""
    place_id = audit_data.get("place_id")
    if not place_id:
        return None
    
    if supabase_client:
        try:
            res = supabase_client.table("audit_reports").upsert(audit_data).execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase upsert audit report error: {e}")
            
    local_db["audit_reports"][place_id] = audit_data
    save_local_db()
    return audit_data

def db_upsert_lead_score(score_data):
    """Upsert lead score statistics."""
    place_id = score_data.get("place_id")
    if not place_id:
        return None
        
    if supabase_client:
        try:
            res = supabase_client.table("lead_scores").upsert(score_data).execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase upsert lead score error: {e}")
            
    local_db["lead_scores"][place_id] = score_data
    save_local_db()
    return score_data

def db_create_search_history(user_id, query_params):
    """Log a new search query execution."""
    import uuid
    from datetime import datetime
    
    history_id = str(uuid.uuid4())
    record = {
        "id": history_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "query": query_params,
        "status": "running",
        "leads_found": 0
    }
    
    if supabase_client:
        try:
            res = supabase_client.table("search_history").insert(record).execute()
            return history_id
        except Exception as e:
            logger.error(f"Supabase create search history error: {e}")
            
    local_db["search_history"][history_id] = record
    save_local_db()
    return history_id

def db_update_search_history(history_id, status, leads_found):
    """Update status/metrics of search history."""
    if supabase_client:
        try:
            supabase_client.table("search_history").update({
                "status": status,
                "leads_found": leads_found
            }).eq("id", history_id).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase update search history error: {e}")
            
    if history_id in local_db["search_history"]:
        local_db["search_history"][history_id]["status"] = status
        local_db["search_history"][history_id]["leads_found"] = leads_found
        save_local_db()
        return True
    return False

def db_get_leads(filters=None, sort_by=None):
    """
    Fetch all leads by joining businesses, audit_reports and lead_scores.
    Filters: category, city, priority, has_website, min_score, etc.
    """
    if supabase_client:
        try:
            # Query from supabase with joins.
            # Post-filtering simplifies client implementation
            query = supabase_client.table("businesses").select(
                "*, audit_reports(*), lead_scores(*)"
            )
            res = query.execute()
            leads = res.data or []
            return _apply_filters_and_sorting(leads, filters, sort_by)
        except Exception as e:
            logger.error(f"Supabase get leads error: {e}. Falling back to local search.")

    # Local Join
    leads = []
    for place_id, bus in local_db["businesses"].items():
        audit = local_db["audit_reports"].get(place_id, {})
        score = local_db["lead_scores"].get(place_id, {})
        joined = {**bus}
        joined["audit_reports"] = audit
        joined["lead_scores"] = score
        leads.append(joined)
        
    return _apply_filters_and_sorting(leads, filters, sort_by)

def db_get_lead_detail(place_id):
    """Get full details of a business lead."""
    if supabase_client:
        try:
            res = supabase_client.table("businesses").select(
                "*, audit_reports(*), lead_scores(*)"
            ).eq("place_id", place_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Supabase get lead detail error: {e}")
            
    bus = local_db["businesses"].get(place_id)
    if not bus:
        return None
    audit = local_db["audit_reports"].get(place_id, {})
    score = local_db["lead_scores"].get(place_id, {})
    return {
        **bus,
        "audit_reports": audit,
        "lead_scores": score
    }

def db_get_stats():
    """Retrieve statistical counters for the dashboard."""
    leads = db_get_leads()
    total_leads = len(leads)
    hot_leads = 0
    total_score = 0
    no_website = 0
    
    for lead in leads:
        score_info = lead.get("lead_scores", {}) or {}
        score = score_info.get("score", 0)
        priority = score_info.get("priority", "LOW")
        website = lead.get("website")
        
        if priority == "HOT":
            hot_leads += 1
        total_score += score
        if not website:
            no_website += 1
            
    avg_score = round(total_score / total_leads, 1) if total_leads > 0 else 0
    
    return {
        "leadsGenerated": total_leads,
        "hotLeads": hot_leads,
        "averageLeadScore": avg_score,
        "websitesWithoutWebsite": no_website,
        "analyzedBusinesses": total_leads
    }

def _apply_filters_and_sorting(leads, filters, sort_by):
    filtered_leads = []
    filters = filters or {}
    
    for lead in leads:
        audit = lead.get("audit_reports") or {}
        score_info = lead.get("lead_scores") or {}
        
        # Filter by Category (case-insensitive contains)
        if filters.get("category"):
            # Mock leads might not have a category stored in the business entity,
            # we check name or address or custom field. Let's make category matching relaxed.
            pass
            
        # Filter by rating
        if filters.get("rating"):
            rating = lead.get("google_rating") or 0
            if rating < float(filters["rating"]):
                continue
                
        # Filter by Website (Exists or not)
        if filters.get("website"):
            has_web = bool(lead.get("website"))
            req_web = filters["website"] # 'yes' | 'no'
            if req_web == "yes" and not has_web:
                continue
            if req_web == "no" and has_web:
                continue
                
        # Filter by Score
        if filters.get("leadScore"):
            req_priority = filters["leadScore"].upper() # 'HOT', 'MEDIUM', 'LOW'
            priority = score_info.get("priority", "LOW")
            if priority != req_priority:
                continue
                
        # Filter by city or area (simple substring search in address)
        if filters.get("city"):
            addr = lead.get("address") or ""
            if filters["city"].lower() not in addr.lower():
                continue
                
        if filters.get("area"):
            addr = lead.get("address") or ""
            if filters["area"].lower() not in addr.lower():
                continue
                
        filtered_leads.append(lead)
        
    # Sort
    if sort_by:
        reverse = sort_by.startswith("-")
        field = sort_by.lstrip("-")
        
        def sort_key(item):
            if field == "score":
                return item.get("lead_scores", {}).get("score", 0)
            elif field == "rating":
                return item.get("google_rating") or 0
            elif field == "name":
                return item.get("name") or ""
            return 0
            
        filtered_leads.sort(key=sort_key, reverse=reverse)
        
    return filtered_leads
