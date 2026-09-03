import time
import requests
import json

base_url = "http://127.0.0.1:5000/api"

print("--- Testing API Status ---")
r = requests.get(f"{base_url}/api-status")
print(r.json())

print("\n--- Testing Search ---")
payload = {
    "category": "dentist",
    "city": "austin",
    "limit": 1
}
r = requests.post(f"{base_url}/search", json=payload)
data = r.json()
print("Search Response:", data)
search_id = data.get("search_id")

if search_id:
    print(f"Waiting for search {search_id} to complete...")
    for _ in range(20):
        time.sleep(3)
        r = requests.get(f"{base_url}/search/status/{search_id}")
        status = r.json()
        print(f"Status: {status['status']}, Lead: {status.get('current_lead')}")
        if status['status'] in ['completed', 'failed']:
            break

print("\n--- Testing Leads ---")
r = requests.get(f"{base_url}/leads")
leads = r.json()
print(f"Found {len(leads)} leads.")
if leads:
    lead = leads[0]
    print(f"Name: {lead.get('name')}")
    print(f"AI Problems: {lead.get('lead_scores', {}).get('failed_checks')}")
    print(f"AI Recommended: {lead.get('lead_scores', {}).get('recommended_services')}")
    print(f"AI Score: {lead.get('lead_scores', {}).get('score')}")
    print(f"AI Priority: {lead.get('lead_scores', {}).get('priority')}")
