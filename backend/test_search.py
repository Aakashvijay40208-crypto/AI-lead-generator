import time
import requests
import json

base_url = "http://127.0.0.1:5000/api"

print("--- Testing Search ---")
payload = {
    "category": "dentist",
    "city": "chennai",
    "area": "virugambakkam",
    "limit": 5
}
r = requests.post(f"{base_url}/search", json=payload)
data = r.json()
print("Search Response:", data)
search_id = data.get("search_id")

if search_id:
    print(f"Waiting for search {search_id} to complete...")
    for _ in range(30):
        time.sleep(5)
        try:
            r = requests.get(f"{base_url}/search/status/{search_id}")
            status = r.json()
            print(f"Status: {status['status']}, Lead: {status.get('current_lead')}")
            if status['status'] in ['completed', 'failed']:
                break
        except Exception as e:
            print(f"Error querying status: {e}")

print("\n--- Testing Leads ---")
r = requests.get(f"{base_url}/leads")
leads = r.json()
print(f"Found {len(leads)} leads.")
if leads:
    for i, lead in enumerate(leads[:5]):
        print(f"{i+1}. Name: {lead.get('name')} | Score: {lead.get('lead_scores', {}).get('score')}")
