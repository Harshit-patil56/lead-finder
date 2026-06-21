import argparse
import csv
import sys
import os

# Local imports
from osm_fetch import fetch_leads_from_osm
from site_checker import check_website

def safe_print(msg, end="\n", flush=False):
    """
    Prints a message safely, replacing characters that cannot be encoded by the terminal.
    """
    try:
        print(msg, end=end, flush=flush)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        clean_msg = msg.encode(encoding, errors='replace').decode(encoding)
        print(clean_msg, end=end, flush=flush)

def clean_string(s):
    if not s:
        return ""
    return "".join(c for c in s.lower() if c.isalnum())

def merge_and_deduplicate_leads(osm_leads, maps_leads):
    """
    Merges leads from OSM and Google Maps, deduplicating by business name
    and phone/address, preserving the most complete record.
    """
    unique_leads = {}
    
    for lead in osm_leads + maps_leads:
        name_key = clean_string(lead.get("name", ""))
        phone_key = clean_string(lead.get("phone", ""))
        addr_key = clean_string(lead.get("address", ""))
        
        # Determine a composite key to safely group identical businesses
        if phone_key and phone_key != "na":
            key = f"{name_key}_{phone_key}"
        elif addr_key and addr_key != "na":
            key = f"{name_key}_{addr_key[:20]}"
        else:
            key = name_key
            
        if not key:
            continue
            
        if key in unique_leads:
            existing = unique_leads[key]
            # Merge fields if the incoming lead has better info
            if existing["phone"] in ["N/A", ""] and lead["phone"] not in ["N/A", ""]:
                existing["phone"] = lead["phone"]
            if existing["website"] in ["NONE", ""] and lead["website"] not in ["NONE", ""]:
                existing["website"] = lead["website"]
            if existing["address"] in ["N/A", ""] and lead["address"] not in ["N/A", ""]:
                existing["address"] = lead["address"]
            if existing.get("lat") is None and lead.get("lat") is not None:
                existing["lat"] = lead["lat"]
            if existing.get("lon") is None and lead.get("lon") is not None:
                existing["lon"] = lead["lon"]
        else:
            unique_leads[key] = lead
            
    return list(unique_leads.values())

def main():
    parser = argparse.ArgumentParser(
        description="Lead Finder: Discover local businesses without websites or with outdated websites."
    )
    parser.add_argument(
        "-c", "--city",
        required=True,
        help="City or region name to search (e.g., 'Palo Alto', 'Austin, TX')"
    )
    parser.add_argument(
        "-g", "--category",
        required=True,
        help="Business category (e.g., 'dentist', 'bakery', 'restaurant')"
    )
    parser.add_argument(
        "-o", "--output",
        default="leads.csv",
        help="Output CSV filepath (default: leads.csv)"
    )
    parser.add_argument(
        "--include-maps-scrape",
        action="store_true",
        help="Enable optional rate-limited Google Maps fallback scraper (may violate Google's ToS)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=30,
        help="Maximum results to scrap from Google Maps scraper (default: 30)"
    )

    args = parser.parse_args()

    print(f"[*] Starting search for '{args.category}' in '{args.city}'...")
    
    # 1. Fetch from OSM (Primary Source)
    osm_leads = fetch_leads_from_osm(args.category, args.city)
    
    # 2. Fetch from Google Maps Scraper (Secondary Source)
    maps_leads = []
    if args.include_maps_scrape:
        try:
            from maps_scrape import scrape_leads_from_maps
            maps_leads = scrape_leads_from_maps(args.category, args.city, args.max_results)
        except ImportError as e:
            print(f"[!] Error importing maps scraper: {e}. Make sure playwright is installed.")
            print("[!] Continuing with OSM results only.")
        except Exception as e:
            print(f"[!] Google Maps scraper failed: {e}")
            print("[!] Continuing with OSM results only.")
            
    # 3. Merge & Deduplicate
    leads = merge_and_deduplicate_leads(osm_leads, maps_leads)
    total_found = len(leads)
    print(f"[*] Total unique businesses found: {total_found}")
    
    # 4. Website Quality Checking
    print("[*] Performing website quality audits...")
    processed_leads = []
    
    for idx, lead in enumerate(leads):
        name = lead["name"]
        website = lead["website"]
        
        safe_print(f"    ({idx + 1}/{total_found}) Auditing '{name}'...", end="", flush=True)
        
        if website == "NONE":
            lead["status"] = "no_website"
            lead["reason_flagged"] = "N/A"
            safe_print(" NO WEBSITE")
        else:
            try:
                status, reason = check_website(website)
                lead["status"] = status
                lead["reason_flagged"] = reason
                safe_print(f" {status.upper()} ({reason})")
            except Exception as e:
                # Fallback to unchecked if unexpected failure
                lead["status"] = "unchecked"
                lead["reason_flagged"] = f"Check failed ({str(e)})"
                safe_print(" UNCHECKED (error during check)")
                
        processed_leads.append(lead)

    # 5. Sort CSV: "no_website" leads first, then "outdated", then others ("ok", "unchecked")
    STATUS_ORDER = {
        "no_website": 0,
        "outdated": 1,
        "ok": 2,
        "unchecked": 3
    }
    processed_leads.sort(key=lambda x: STATUS_ORDER.get(x["status"], 4))
    
    # 6. Save to CSV
    output_fields = ["business_name", "phone", "address", "website", "status", "reason_flagged", "latitude", "longitude"]
    
    try:
        # Resolve output file path
        output_path = os.path.abspath(args.output)
        
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=output_fields)
            # Write Header
            writer.writerow({
                "business_name": "business_name",
                "phone": "phone",
                "address": "address",
                "website": "website",
                "status": "status",
                "reason_flagged": "reason_flagged",
                "latitude": "latitude",
                "longitude": "longitude"
            })
            
            for lead in processed_leads:
                writer.writerow({
                    "business_name": lead["name"],
                    "phone": lead["phone"],
                    "address": lead["address"],
                    "website": lead["website"],
                    "status": lead["status"],
                    "reason_flagged": lead["reason_flagged"],
                    "latitude": lead.get("lat"),
                    "longitude": lead.get("lon")
                })
                
        print(f"\n[*] Results successfully saved to: {output_path}")
        
    except Exception as e:
        print(f"\n[!] Error writing CSV file: {e}", file=sys.stderr)
        
    # 7. Print Summary Count to Terminal
    no_web_count = sum(1 for l in processed_leads if l["status"] == "no_website")
    outdated_count = sum(1 for l in processed_leads if l["status"] == "outdated")
    ok_count = sum(1 for l in processed_leads if l["status"] == "ok")
    unchecked_count = sum(1 for l in processed_leads if l["status"] == "unchecked")
    
    print("\n" + "="*40)
    print("           LEAD FINDER SUMMARY")
    print("="*40)
    print(f" {no_web_count} no-website leads")
    print(f" {outdated_count} outdated website leads")
    print(f" {ok_count} fine (ok) websites")
    if unchecked_count > 0:
        print(f" {unchecked_count} unchecked leads")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
