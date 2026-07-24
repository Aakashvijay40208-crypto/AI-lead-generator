import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

def calculate_lead_score(business, audit, ai_analysis=None):
    """
    Compute a lead score from 0 to 100 based on website and presence deficiencies.
    Capped at 100.
    
    Rules:
    - No Website: +40 points
    - Website Older Than 5 Years: +20 points
    - No SEO (Missing title/desc): +20 points
    - No SSL: +10 points
    - Not Mobile Friendly: +10 points
    - No WhatsApp: +10 points
    - Poor Performance (Response Time > 3s): +10 points
    - No Booking System: +5 points
    - Broken Contact Form: +10 points
    - Outdated Website Design: +15 points
    """
    score = 0
    failed_checks = []
    recommended_services = []
    
    website = business.get("website") or ""
    
    # 1. No Website Check (40 pts)
    if not website:
        score += 40
        failed_checks.append("No Website")
        recommended_services.append("Website Redesign & Development")
        
        # When there is no website, they automatically lack SEO, SSL, Booking, Mobile compatibility, etc.
        # Add those points up but cap the score.
        score += 20  # No SEO
        failed_checks.append("No SEO Setup")
        recommended_services.append("Search Engine Optimization (SEO)")
        
        score += 10  # No SSL
        failed_checks.append("No SSL Certificate")
        recommended_services.append("SSL/HTTPS Security Configuration")
        
        score += 10  # Not Mobile Friendly
        failed_checks.append("Not Mobile Friendly")
        recommended_services.append("Mobile-responsive Design")
        
        score += 10  # No WhatsApp
        failed_checks.append("No WhatsApp Integration")
        recommended_services.append("WhatsApp Business Automation")
        
        score += 5   # No Booking
        failed_checks.append("No Booking System")
        recommended_services.append("Online Appointment Booking Platform")
        
    else:
        # Website exists - audit specific components
        # 2. SSL check (10 pts)
        is_https = audit.get("is_https", True)
        if not is_https:
            score += 10
            failed_checks.append("No SSL (Not HTTPS)")
            recommended_services.append("SSL/HTTPS Security Configuration")
            
        # 3. SEO Check (20 pts)
        seo_info = audit.get("seo") or {}
        has_title = bool(seo_info.get("title"))
        has_desc = bool(seo_info.get("description"))
        if not has_title or not has_desc:
            score += 20
            failed_checks.append("No SEO (Missing Title or Meta Description)")
            recommended_services.append("Search Engine Optimization (SEO)")
            
        # 4. Mobile Friendly check (10 pts)
        ux_info = audit.get("ux") or {}
        is_mobile = ux_info.get("isMobileFriendly", True)
        if not is_mobile:
            score += 10
            failed_checks.append("Not Mobile Friendly")
            recommended_services.append("Mobile-responsive Design")
            
        # 5. WhatsApp check (10 pts)
        tech = audit.get("tech_detected") or {}
        has_whatsapp = tech.get("whatsapp", False)
        if not has_whatsapp:
            score += 10
            failed_checks.append("No WhatsApp Integration")
            recommended_services.append("WhatsApp Business Automation")
            
        # 6. Performance check (10 pts)
        resp_time = audit.get("response_time_ms", 0)
        if resp_time > 3000:
            score += 10
            failed_checks.append("Poor Performance (Page load > 3s)")
            recommended_services.append("Performance Optimization")
            
        # 7. Booking system check (5 pts)
        has_booking = tech.get("bookingSystem", False)
        if not has_booking:
            score += 5
            failed_checks.append("No Booking System")
            recommended_services.append("Online Appointment Booking Platform")
            
        # 8. Broken Contact Form (10 pts)
        # Check if form exists or flagged broken (default to 15% chance if form exists, or from AI analysis)
        is_form_broken = False
        if ai_analysis:
            is_form_broken = ai_analysis.get("problems_detected", {}).get("broken_contact_form", False)
        else:
            # Random heuristic for mock leads
            is_form_broken = (random.random() > 0.85) if website else False
            
        if is_form_broken:
            score += 10
            failed_checks.append("Broken Contact Form")
            recommended_services.append("Contact Form Refactoring")
            
        # 9. Outdated Website Design (15 pts) & 10. Website > 5 Years Old (20 pts)
        # Pull from AI analysis if available, otherwise mock/heauristics
        is_outdated = False
        is_old = False
        
        if ai_analysis:
            is_outdated = ai_analysis.get("problems_detected", {}).get("outdated_design", False)
            is_old = ai_analysis.get("problems_detected", {}).get("old_website", False)
        else:
            is_outdated = random.random() > 0.7
            is_old = random.random() > 0.75
            
        if is_outdated:
            score += 15
            failed_checks.append("Outdated Website Design")
            recommended_services.append("Modern Website Redesign")
            
        if is_old:
            score += 20
            failed_checks.append("Website Older Than 5 Years")
            recommended_services.append("Complete Website Redesign")
            
    # Cap score at 100
    score = min(score, 100)
    
    # Priority Levels
    # Hot >= 80, Medium >= 50, Low >= 0
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
        "failed_checks": failed_checks,
        "recommended_services": list(set(recommended_services)),
        "last_calculated": datetime.utcnow().isoformat() + "Z"
    }
