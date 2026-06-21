import random
import time
import urllib.parse
import re
from playwright.sync_api import sync_playwright

import sys

# List of realistic user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def clean_pua_chars(s):
    """
    Strips Private Use Area (PUA) unicode characters (e.g. material icon font glyphs)
    which may be extracted from the DOM and can crash console prints on Windows.
    """
    if not s:
        return ""
    return "".join(c for c in s if not (
        (0xE000 <= ord(c) <= 0xF8FF) or
        (0xF0000 <= ord(c) <= 0xFFFFD) or
        (0x100000 <= ord(c) <= 0x10FFFD)
    )).strip()

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

def clean_website_url(url):
    """
    Cleans Google redirect URLs if present, extracting the actual target website.
    """
    if not url or url == "NONE":
        return "NONE"
    
    url = clean_pua_chars(url)
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc == "www.google.com" and parsed.path == "/url":
        qs = urllib.parse.parse_qs(parsed.query)
        if "q" in qs:
            return qs["q"][0]
            
    return url

def scrape_leads_from_maps(category, city_name, max_results=30):
    """
    Scrapes business leads from Google Maps using Playwright.
    """
    print("\n" + "="*80)
    print("WARNING: Using the Google Maps scraper may violate Google's Terms of Service.")
    print("Please use this feature sparingly and respect Google's rate limits.")
    print("="*80 + "\n")

    results = []
    
    with sync_playwright() as p:
        user_agent = random.choice(USER_AGENTS)
        print(f"[Maps Scraper] Launching headless browser with User-Agent: {user_agent}")
        
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Create a stealthy browser context
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        
        page = context.new_page()
        
        # Direct search query
        search_query = f"{category} in {city_name}"
        encoded_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        
        print(f"[Maps Scraper] Navigating to Google Maps search page...")
        page.goto(search_url)
        
        # Handle Cookie Consent/Agreement popups if they appear
        try:
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("Agree")',
                'button:has-text("I agree")',
                'button:has-text("Accept")',
                'button[aria-label="Accept all"]'
            ]
            for selector in consent_selectors:
                btn = page.locator(selector)
                if btn.count() > 0:
                    btn.first.click()
                    print("[Maps Scraper] Dismissed cookie consent dialog.")
                    time.sleep(2.0)
                    break
        except Exception:
            pass

        # Wait for either results list or single place view to load
        try:
            page.wait_for_selector('a[href*="/maps/place/"], h1', timeout=15000)
        except Exception:
            print("[Maps Scraper] Timeout waiting for initial page load. No results found or page blocked.")
            browser.close()
            return []

        # If it's a single search result, Google Maps redirects directly to the place page
        # In this case, we have a single result
        if page.locator('h1').count() > 0 and page.locator('a[href*="/maps/place/"]').count() == 0:
            print("[Maps Scraper] Single matching result detected.")
            # Extract details directly
            name = clean_pua_chars(page.locator('h1').first.inner_text().strip())
            
            address = "N/A"
            address_btn = page.locator('button[data-item-id="address"]')
            if address_btn.count() > 0:
                address = clean_pua_chars(address_btn.first.inner_text().strip())
                
            phone = "N/A"
            phone_btn = page.locator('button[data-item-id^="phone:tel:"]')
            if phone_btn.count() > 0:
                phone = clean_pua_chars(phone_btn.first.inner_text().strip())
                
            website = "NONE"
            website_link = page.locator('a[data-item-id="authority"]')
            if website_link.count() > 0:
                website = website_link.first.get_attribute("href") or "NONE"
                website = clean_website_url(website)
                
            # Extract lat/lon from page url
            lat, lon = None, None
            url = page.url
            coords_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
            if coords_match:
                lat = float(coords_match.group(1))
                lon = float(coords_match.group(2))
            else:
                coords_match2 = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
                if coords_match2:
                    lat = float(coords_match2.group(1))
                    lon = float(coords_match2.group(2))

            browser.close()
            return [{
                "name": name,
                "phone": phone,
                "address": address,
                "website": website,
                "lat": lat,
                "lon": lon,
                "source": "google_maps"
            }]

        # Scroll the feed container to load more items
        print("[Maps Scraper] Scrolling results feed...")
        feed_selector = 'div[role="feed"]'
        
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 15
        
        while scroll_attempts < max_scroll_attempts:
            count = page.locator('a[href*="/maps/place/"]').count()
            print(f"[Maps Scraper] Found {count} items in list...")
            if count >= max_results:
                break
                
            # Perform scroll
            feed = page.locator(feed_selector)
            if feed.count() > 0:
                feed.first.evaluate("element => element.scrollBy(0, element.scrollHeight)")
            else:
                # Fallback scroll window
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                
            # Random delay during scroll to mimic user behavior
            time.sleep(random.uniform(2.0, 4.0))
            
            new_count = page.locator('a[href*="/maps/place/"]').count()
            if new_count == last_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                last_count = new_count
                
        # Gather matching place hrefs
        place_links = page.locator('a[href*="/maps/place/"]')
        links_count = min(place_links.count(), max_results)
        
        hrefs = []
        for i in range(links_count):
            href = place_links.nth(i).get_attribute("href")
            if href:
                hrefs.append(href)
                
        print(f"[Maps Scraper] Scoped {len(hrefs)} listing links. Fetching details sequentially...")
        
        for idx, href in enumerate(hrefs):
            print(f"[Maps Scraper] ({idx + 1}/{len(hrefs)}) Opening listing details...")
            
            try:
                # Realistic navigation
                page.goto(href)
                page.wait_for_selector('h1', timeout=10000)
                
                # Dynamic delay to evade rate limits / bot checks
                delay = random.uniform(3.0, 8.0)
                print(f"[Maps Scraper] Sleeping for {delay:.2f}s...")
                time.sleep(delay)
                
                # Scraping attributes
                name_el = page.locator('h1').first
                name = clean_pua_chars(name_el.inner_text().strip()) if name_el.count() > 0 else "Unknown Name"
                
                address = "N/A"
                address_btn = page.locator('button[data-item-id="address"]')
                if address_btn.count() > 0:
                    address = clean_pua_chars(address_btn.first.inner_text().strip())
                    
                phone = "N/A"
                phone_btn = page.locator('button[data-item-id^="phone:tel:"]')
                if phone_btn.count() > 0:
                    phone = clean_pua_chars(phone_btn.first.inner_text().strip())
                    
                website = "NONE"
                website_link = page.locator('a[data-item-id="authority"]')
                if website_link.count() > 0:
                    website = website_link.first.get_attribute("href") or "NONE"
                    website = clean_website_url(website)
                    
                # Extract lat/lon from detail URL (href)
                lat, lon = None, None
                coords_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', href)
                if coords_match:
                    lat = float(coords_match.group(1))
                    lon = float(coords_match.group(2))
                else:
                    coords_match2 = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', href)
                    if coords_match2:
                        lat = float(coords_match2.group(1))
                        lon = float(coords_match2.group(2))

                safe_print(f"[Maps Scraper] Scraped: {name} | Website: {website} | Phone: {phone}")
                
                results.append({
                    "name": name,
                    "phone": phone,
                    "address": address,
                    "website": website,
                    "lat": lat,
                    "lon": lon,
                    "source": "google_maps"
                })
                
            except Exception as e:
                print(f"[Maps Scraper] Error scraping details for {href}: {e}")
                continue
                
        browser.close()
        
    return results
