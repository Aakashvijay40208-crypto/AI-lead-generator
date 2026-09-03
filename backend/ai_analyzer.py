import os
import json
import logging
import ollama
from api_manager import get_api_key, disable_key

logger = logging.getLogger(__name__)

def analyze_business(business, audit):
    """
    Perform AI-based digital transformation analysis on the business using local Ollama.
    """
    # 1. Check Ollama Status via api_manager (we use a dummy key "local")
    ollama_key = get_api_key("ollama")
    if ollama_key:
        try:
            logger.info("Running Ollama local B2B analysis...")
            prompt = construct_prompt(business, audit)
            
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            model_name = os.getenv("OLLAMA_MODEL", "gemma4:26b")
            
            client = ollama.Client(host=host)
            
            response = client.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}],
                format='json',
                options={'temperature': 0.7}
            )
            
            result_text = response['message']['content']
            result = json.loads(result_text)
            return sanitize_ai_result(result)
            
        except Exception as e:
            logger.error(f"Ollama AI analysis failed: {e}")
            return {
                "ai_status": "error",
                "ai_error": "Ollama is unavailable or AI analysis failed"
            }
            
    logger.error("Ollama AI unavailable. Returning error state.")
    return {
        "ai_status": "error",
        "ai_error": "Ollama is unavailable or AI analysis failed"
    }

def construct_prompt(business, audit):
    """Build the prompt describing business deficiencies."""
    context = {
        "business_name": business.get("name"),
        "website": business.get("website"),
        "address": business.get("address"),
        "phone": business.get("phone_number"),
        "google_rating": business.get("google_rating"),
        "review_count": business.get("review_count"),
        "audit_data": {
            "website_status": audit.get("website_status"),
            "is_https": audit.get("is_https"),
            "response_time_ms": audit.get("response_time_ms"),
            "seo_title": audit.get("seo", {}).get("title"),
            "seo_description": audit.get("seo", {}).get("description"),
            "is_mobile_friendly": audit.get("ux", {}).get("isMobileFriendly"),
            "technologies": audit.get("tech_detected")
        }
    }
    
    prompt = f"""
    You are a professional B2B digital transformation consultant working for OXIS.
    Analyze this business digital footprint:
    {json.dumps(context, indent=2)}
    
    Identify specific digital marketing, tech stack, UX, and SEO problems.
    Recommend digital transformation services.
    Write a highly personalized, compelling B2B cold sales pitch email (addressed from OXIS) that highlights their specific problems, how we can solve them, and requests a quick meeting.
    
    Return a JSON object conforming exactly to this structure:
    {{
        "problems_detected": {{
            "no_website": bool,
            "poor_seo": bool,
            "poor_performance": bool,
            "old_website": bool,
            "missing_ssl": bool,
            "missing_whatsapp": bool,
            "missing_booking": bool,
            "poor_mobile_experience": bool,
            "outdated_design": bool,
            "broken_contact_form": bool
        }},
        "recommended_services": [
            "WebsiteRedesign" or "SEO" or "CRM" or "WhatsAppAutomation" or "AppointmentSystem" or "PerformanceOptimization" or "DigitalTransformation"
        ],
        "analysis_summary": "A 2-3 sentence overview of the digital footprint and core gap.",
        "personalized_pitch": "Write a short (2-3 paragraphs) B2B cold outreach email pitch from OXIS showing how we can transform their business and invite them for a consultation."
    }}
    """
    return prompt

def sanitize_ai_result(result):
    """Ensure return dict has all keys and fits structure."""
    default_problems = {
        "no_website": False,
        "poor_seo": False,
        "poor_performance": False,
        "old_website": False,
        "missing_ssl": False,
        "missing_whatsapp": False,
        "missing_booking": False,
        "poor_mobile_experience": False,
        "outdated_design": False,
        "broken_contact_form": False
    }
    
    sanitized = {
        "problems_detected": default_problems,
        "recommended_services": [],
        "analysis_summary": "",
        "personalized_pitch": ""
    }
    
    if "problems_detected" in result:
        for k in default_problems:
            sanitized["problems_detected"][k] = bool(result["problems_detected"].get(k, False))
            
    if "recommended_services" in result:
        sanitized["recommended_services"] = [str(x) for x in result["recommended_services"]]
        
    sanitized["analysis_summary"] = str(result.get("analysis_summary", "No summary provided."))
    sanitized["personalized_pitch"] = str(result.get("personalized_pitch", "Dear Owner, we can help transform your business."))
    
    return sanitized
