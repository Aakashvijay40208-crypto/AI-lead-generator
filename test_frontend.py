from playwright.sync_api import sync_playwright
import time
import subprocess
import os

def run():
    print("Starting backend...")
    backend = subprocess.Popen(["python", "app.py"], cwd=r"c:\Users\Aakash V\OneDrive\Desktop\ai-lead-generator\backend")
    
    print("Starting frontend...")
    frontend = subprocess.Popen(["npm.cmd", "run", "dev"], cwd=r"c:\Users\Aakash V\OneDrive\Desktop\ai-lead-generator\frontend")
    
    time.sleep(10)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.on("console", lambda msg: print(f"Browser console: {msg.type}: {msg.text}"))
            page.on("requestfailed", lambda req: print(f"Request failed: {req.url} - {req.failure}"))
            page.on("response", lambda res: print(f"Response: {res.url} - {res.status}"))
            
            print("Navigating to frontend...")
            page.goto("http://localhost:5173")
            time.sleep(3)
            
            if page.locator("text=Sign In to Platform").count() > 0:
                print("Logging in...")
                page.fill("input[placeholder='admin@oxis.ai']", "test@example.com")
                page.fill("input[placeholder='••••••••']", "password")
                page.click("text=Sign In to Platform")
                time.sleep(3)
            
            print("Filling form...")
            page.fill("input[placeholder='e.g. Dentists, Restaurants']", "dentist")
            page.fill("input[placeholder='e.g. Austin']", "chennai")
            page.fill("input[placeholder='e.g. Downtown']", "virugambakkam")
            
            print("Clicking Launch Prospect Scan...")
            page.click("text=Launch Prospect Scan")
            
            time.sleep(2)
            
            print("Current page HTML after click:")
            html = page.locator(".glass-panel").first.inner_html()
            if "Launch Prospect Scan" in html:
                print("UI reverted to form!")
            elif "Scanning & Auditing" in html:
                print("UI shows progress!")
            else:
                print("UI state unknown.")
            
            time.sleep(5)
            
            browser.close()
    finally:
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    run()
