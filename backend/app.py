import os
import uuid
import logging
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from supabase_client import (
    db_create_search_history,
    db_update_search_history,
    db_upsert_business,
    db_upsert_audit_report,
    db_upsert_lead_score,
    db_get_leads,
    db_get_lead_detail,
    db_get_stats
)
from api_manager import get_provider_status
from serpapi_client import search_and_enrich_businesses
from playwright_auditor import audit_website
from lead_scorer import calculate_lead_score
from ai_analyzer import analyze_business
from export_manager import generate_leads_excel

# Initialize logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")
CORS(app) # Enable CORS for frontend Vite application

# Global registry for tracking background search task progress
active_tasks = {}

def run_background_lead_pipeline(search_id, user_id, category, city, area, radius, limit):
    """
    Background worker thread running search, scraping, website audits, 
    AI analysis, and lead scoring.
    """
    logger.info(f"Background pipeline started for search {search_id}")
    active_tasks[search_id] = {
        "status": "searching",
        "progress": 0,
        "total": 0,
        "current_lead": "Fetching locations from SerpAPI...",
        "leads_found": 0,
        "place_ids": []
    }
    
    try:
        # 1. Fetch businesses from SerpAPI
        businesses = search_and_enrich_businesses(
            category=category,
            city=city,
            area=area,
            radius=radius,
            limit=limit
        )
        
        total_leads = len(businesses)
        active_tasks[search_id]["total"] = total_leads
        active_tasks[search_id]["status"] = "processing"
        
        if total_leads == 0:
            logger.info("No businesses found.")
            db_update_search_history(search_id, "completed", 0)
            active_tasks[search_id]["status"] = "completed"
            active_tasks[search_id]["current_lead"] = "No businesses found."
            return
            
        processed_count = 0
        
        for index, bus in enumerate(businesses):
            place_id = bus["place_id"]
            name = bus["name"]
            website = bus.get("website")
            
            active_tasks[search_id]["current_lead"] = f"Auditing site: {name} ({index+1}/{total_leads})"
            logger.info(f"Auditing business: {name} (Website: {website})")
            
            # Write category back into business
            bus["category"] = category
            
            # Save basic business listing first
            db_upsert_business(bus)
            
            # 2. Run Playwright audit
            audit = audit_website(place_id, website)
            
            # Merge scraper contacts from SerpAPI (if any) if not detected by Playwright
            if bus.get("contacts"):
                for contact_type in ["emails", "phoneNumbers"]:
                    if not audit["contacts"].get(contact_type):
                        audit["contacts"][contact_type] = bus["contacts"].get(contact_type, [])
                for soc, val in bus["contacts"].get("socialLinks", {}).items():
                    if val and not audit["contacts"]["socialLinks"].get(soc):
                        audit["contacts"]["socialLinks"][soc] = val
                        
            # Save audit report
            db_upsert_audit_report(audit)
            
            # 3. AI analysis
            ai_report = analyze_business(bus, audit)
            
            # 4. Lead Score calculation
            lead_score = calculate_lead_score(bus, audit, ai_report)
            
            # Save lead scores
            db_upsert_lead_score(lead_score)
            
            processed_count += 1
            active_tasks[search_id]["progress"] = processed_count
            active_tasks[search_id]["leads_found"] = processed_count
            active_tasks[search_id]["place_ids"].append(place_id)
            
        # Update search history status in Supabase
        db_update_search_history(search_id, "completed", processed_count)
        active_tasks[search_id]["status"] = "completed"
        active_tasks[search_id]["current_lead"] = f"Finished. Analyzed {processed_count} businesses."
        logger.info(f"Background pipeline completed for search {search_id}. Leads found: {processed_count}")
        
    except Exception as e:
        logger.error(f"Error in background pipeline: {e}", exc_info=True)
        db_update_search_history(search_id, "failed", 0)
        active_tasks[search_id]["status"] = "failed"
        active_tasks[search_id]["current_lead"] = f"Error occurred: {str(e)}"

# --- REST ENDPOINTS ---

@app.route("/api/search", methods=["POST"])
def search_leads():
    """Trigger a new search and run lead acquisition pipeline."""
    data = request.json or {}
    category = data.get("category")
    city = data.get("city")
    area = data.get("area")
    radius = data.get("radius", 5)
    limit = int(data.get("limit", 5))
    user_id = data.get("userId", "default-user")
    
    if not category or not city:
        return jsonify({"error": "Category and City are required fields."}), 400
        
    # Log query history in DB
    query_params = {
        "category": category,
        "city": city,
        "area": area,
        "radius": radius,
        "limit": limit
    }
    
    search_id = db_create_search_history(user_id, query_params)
    
    # Run the background scraping and analysis pipeline
    thread = threading.Thread(
        target=run_background_lead_pipeline,
        args=(search_id, user_id, category, city, area, radius, limit)
    )
    thread.start()
    
    return jsonify({
        "search_id": search_id,
        "status": "running",
        "message": "Search initialized successfully."
    })

@app.route("/api/search/status/<search_id>", methods=["GET"])
def get_search_status(search_id):
    """Query current status of background processing thread."""
    task = active_tasks.get(search_id)
    if not task:
        return jsonify({"status": "not_found", "message": "No active search task."}), 404
    return jsonify(task)

@app.route("/api/leads", methods=["GET"])
def get_leads():
    """Fetch collected leads list matching query parameters."""
    filters = {
        "category": request.args.get("category"),
        "city": request.args.get("city"),
        "area": request.args.get("area"),
        "rating": request.args.get("rating"),
        "website": request.args.get("website"), # 'yes' | 'no'
        "leadScore": request.args.get("leadScore") # 'HOT' | 'MEDIUM' | 'LOW'
    }
    sort_by = request.args.get("sort_by", "-score") # default sort by highest score
    
    search_id = request.args.get("search_id")
    place_ids = None
    if search_id:
        task = active_tasks.get(search_id)
        if task:
            place_ids = task.get("place_ids", [])
        else:
            place_ids = []
            
    leads = db_get_leads(filters=filters, sort_by=sort_by)
    
    # Filter memory leads by place_ids if search_id was provided
    if place_ids is not None:
        leads = [lead for lead in leads if lead.get("place_id") in place_ids]
        
    return jsonify(leads)

@app.route("/api/leads/<place_id>", methods=["GET"])
def get_lead_detail_route(place_id):
    """Retrieve all detailed information of a lead."""
    lead = db_get_lead_detail(place_id)
    if not lead:
        return jsonify({"error": "Lead not found."}), 404
    return jsonify(lead)

@app.route("/api/stats", methods=["GET"])
def get_stats_route():
    """Retrieve dashboard metric stats."""
    stats = db_get_stats()
    return jsonify(stats)

@app.route("/api/api-status", methods=["GET"])
def get_api_status_route():
    """Expose API health and rotations."""
    status = get_provider_status()
    return jsonify(status)

@app.route("/api/export", methods=["GET"])
def export_leads_excel_route():
    """Build and download the styled leads Excel sheet."""
    filters = {
        "category": request.args.get("category"),
        "city": request.args.get("city"),
        "area": request.args.get("area"),
        "rating": request.args.get("rating"),
        "website": request.args.get("website"),
        "leadScore": request.args.get("leadScore")
    }
    sort_by = request.args.get("sort_by", "-score")
    
    leads = db_get_leads(filters=filters, sort_by=sort_by)
    
    if not leads:
        return jsonify({"error": "No leads available to export."}), 400
        
    excel_stream = generate_leads_excel(leads)
    
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="oxis_qualified_leads.xlsx"
    )

@app.route("/static/screenshots/<filename>")
def serve_screenshot(filename):
    """Serve audited website page screenshots."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static", "screenshots"), filename)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    logger.info(f"Starting OXIS Lead Generator Backend on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
