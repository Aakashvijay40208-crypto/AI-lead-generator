import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

def calculate_lead_score(business, audit=None):
    """
    Compute a deterministic lead score from 0 to 100 based on website presence & Playwright technical audit.
    Extensible rule-based scoring:
    - No Website: Score 100, Priority HOT, Website Status "No Website"
    - Website Available: Base Score 30, Priority LOW, Website Status "Website Available"
      Additional Playwright Technical Audit Penalties (if audit data present):
      - Insecure (No SSL/HTTPS): +15 points
      - Missing SEO (Title or Meta description): +15 points
      - Not Mobile Friendly: +15 points
      - Slow Performance (Response time > 3s): +10 points
      - Missing WhatsApp / Booking integration: +10 points
    """
    score = 0
    failed_checks = []
    recommended_services = []
    audit = audit or {}
    
    website = business.get("website") or ""
    
    if not website:
        website_status = "No Website"
        score = 100
        failed_checks.append("No Website")
        recommended_services.append("Website Development & Redesign")
    else:
        website_status = "Website Available"
        score = 30 # Base score for having a website
        
        # Playwright Technical Audit Checks (if available)
        # 1. SSL check (15 pts)
        is_https = audit.get("is_https", True)
        if not is_https:
            score += 15
            failed_checks.append("No SSL (Not HTTPS)")
            recommended_services.append("SSL/HTTPS Security Configuration")
            
        # 2. SEO Check (15 pts)
        seo_info = audit.get("seo") or {}
        has_title = bool(seo_info.get("title"))
        has_desc = bool(seo_info.get("description"))
        if not has_title or not has_desc:
            score += 15
            failed_checks.append("Missing SEO Title or Description")
            recommended_services.append("Search Engine Optimization (SEO)")
            
        # 3. Mobile Friendly check (15 pts)
        ux_info = audit.get("ux") or {}
        is_mobile = ux_info.get("isMobileFriendly", True)
        if not is_mobile:
            score += 15
            failed_checks.append("Not Mobile Friendly")
            recommended_services.append("Mobile-responsive Design")
            
        # 4. Performance check (10 pts)
        resp_time = audit.get("response_time_ms", 0)
        if resp_time > 3000:
            score += 10
            failed_checks.append("Slow Load Time (> 3s)")
            recommended_services.append("Performance Optimization")

    # Cap score at 100
    score = min(score, 100)
    
    # Priority Levels: Hot >= 80, Medium >= 50, Low >= 0
    if score >= 80:
        priority = "HOT"
    elif score >= 50:
        priority = "MEDIUM"
    else:
        priority = "LOW"
        
    return {
        "place_id": business["place_id"],
        "score": score,
        "priority": priority,
        "website_status": website_status,
        "failed_checks": failed_checks,
        "recommended_services": list(set(recommended_services)),
        "last_calculated": datetime.utcnow().isoformat() + "Z"
    }

