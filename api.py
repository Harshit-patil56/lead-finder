import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import urllib3

# Silence insecure request warnings from verify=False requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# On Windows, SelectorEventLoop does not support subprocesses (which Playwright relies on).
# We force the WindowsProactorEventLoopPolicy globally.
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception as e:
        print(f"[API] Warning: Failed to set WindowsProactorEventLoopPolicy: {e}")

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from osm_fetch import fetch_leads_from_osm
from site_checker import check_website
from main import merge_and_deduplicate_leads

app = FastAPI(title="Lead Finder API", description="API wrapper for local business lead audits")

# Enable CORS for the Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/leads")
def get_leads(
    category: str = Query(..., description="Business category (e.g. dentist, bakery)"),
    city: str = Query(..., description="City or region name"),
    include_maps_scrape: bool = Query(False, description="Enable Playwright Google Maps scraper fallback"),
    max_results: int = Query(30, description="Max results from Google Maps fallback")
):
    print(f"[*] API request received: category='{category}', city='{city}', maps_scrape={include_maps_scrape}")
    
    if not category.strip() or not city.strip():
        raise HTTPException(status_code=400, detail="Category and City must not be empty.")
        
    try:
        # 1. Fetch from OSM
        osm_leads = fetch_leads_from_osm(category, city)
        
        # 2. Fetch from Google Maps Scraper (optional)
        maps_leads = []
        if include_maps_scrape:
            try:
                from maps_scrape import scrape_leads_from_maps
                maps_leads = scrape_leads_from_maps(category, city, max_results)
            except Exception as e:
                print(f"[!] Google Maps scraper failed in API context: {e}")
                # Continue with OSM data
                
        # 3. Merge & Deduplicate
        leads = merge_and_deduplicate_leads(osm_leads, maps_leads)
        total_found = len(leads)
        print(f"[*] Total unique businesses found: {total_found}")
        
        # 4. Website Quality Audits (Run in parallel to prevent UI timeouts)
        print(f"[*] Starting parallel audits of {total_found} websites...")
        
        def audit_lead(lead):
            website = lead.get("website", "NONE")
            lead_result = dict(lead)
            lead_result["business_name"] = lead.get("name", "Unknown Name")
            
            if website == "NONE":
                lead_result["status"] = "no_website"
                lead_result["reason_flagged"] = "N/A"
            else:
                try:
                    status, reason = check_website(website)
                    lead_result["status"] = status
                    lead_result["reason_flagged"] = reason
                except Exception as e:
                    lead_result["status"] = "unchecked"
                    lead_result["reason_flagged"] = f"Check failed ({str(e)})"
            
            lead_result["latitude"] = lead.get("lat")
            lead_result["longitude"] = lead.get("lon")
            return lead_result

        with ThreadPoolExecutor(max_workers=30) as executor:
            processed_leads = list(executor.map(audit_lead, leads))
            
        print("[*] Completed parallel audits.")
            
        # 5. Sort: no_website first, then outdated, then others
        STATUS_ORDER = {
            "no_website": 0,
            "outdated": 1,
            "ok": 2,
            "unchecked": 3
        }
        processed_leads.sort(key=lambda x: STATUS_ORDER.get(x["status"], 4))
        
        return {
            "leads": processed_leads,
            "summary": {
                "total": len(processed_leads),
                "no_website": sum(1 for l in processed_leads if l["status"] == "no_website"),
                "outdated": sum(1 for l in processed_leads if l["status"] == "outdated"),
                "ok": sum(1 for l in processed_leads if l["status"] == "ok"),
                "unchecked": sum(1 for l in processed_leads if l["status"] == "unchecked")
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lead search failed: {str(e)}")
