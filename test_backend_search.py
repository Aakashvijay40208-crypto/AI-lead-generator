import requests
import time

url = "http://127.0.0.1:5000/api"
payload = {
    "category": "dentist",
    "city": "chennai",
    "area": "virugambakkam",
    "limit": 5
}
print("Sending POST request to /api/search...")
res = requests.post(f"{url}/search", json=payload)
data = res.json()
print("POST response:", data)

search_id = data.get("search_id")
if search_id:
    print(f"Polling status for {search_id}...")
    for i in range(5):
        status_res = requests.get(f"{url}/search/status/{search_id}")
        if status_res.status_code == 200:
            print("Status:", status_res.json())
        else:
            print("Status code:", status_res.status_code, status_res.text)
        time.sleep(1)
