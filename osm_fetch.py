import requests
import urllib.parse
import time

# User-agent header to comply with OpenStreetMap policy
HEADERS = {
    "User-Agent": "LeadFinderTool/1.0 (contact: contact@leadfinder.local)"
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Common mappings for business categories to OSM tags
CATEGORY_MAPPINGS = {
    "dentist": [("amenity", "dentist")],
    "dentists": [("amenity", "dentist")],
    "restaurant": [("amenity", "restaurant")],
    "restaurants": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "cafes": [("amenity", "cafe")],
    "bar": [("amenity", "bar")],
    "bars": [("amenity", "bar")],
    "bakery": [("shop", "bakery")],
    "bakeries": [("shop", "bakery")],
    "hairdresser": [("shop", "hairdresser")],
    "hair_salon": [("shop", "hairdresser")],
    "hairdresser salon": [("shop", "hairdresser")],
    "hotel": [("tourism", "hotel")],
    "hotels": [("tourism", "hotel")],
    "gym": [("leisure", "fitness_centre")],
    "fitness": [("leisure", "fitness_centre")],
    "plumber": [("craft", "plumber")],
    "plumbers": [("craft", "plumber")],
    "lawyer": [("office", "lawyer")],
    "lawyers": [("office", "lawyer")],
    "doctor": [("amenity", "doctors")],
    "doctors": [("amenity", "doctors")],
    "spa": [("leisure", "spa"), ("amenity", "spa")],
    "real_estate": [("office", "estate_agent"), ("shop", "estate_agent")],
}

def geocode_city_to_area(city_name):
    """
    Geocodes a city/region name to OSM object details using Nominatim API.
    Returns:
        - int: Overpass area ID (osm_id + offset) or
        - dict: {'lat': lat, 'lon': lon} if it's a node/fallback, or
        - None if not found.
    """
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(NOMINATIM_URL, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        
        osm_id = data[0].get("osm_id")
        osm_type = data[0].get("osm_type")
        
        # Convert osm_id to Overpass area ID if applicable
        if osm_type == "relation":
            return osm_id + 3600000000
        elif osm_type == "way":
            return osm_id + 2400000000
        else:
            # Default to coordinates radius search
            lat = data[0].get("lat")
            lon = data[0].get("lon")
            if lat and lon:
                return {"lat": float(lat), "lon": float(lon)}
    except Exception as e:
        print(f"[OSM] Warning: Geocoding via Nominatim failed ({e}). Falling back to name-based area query.")
    return None

def build_overpass_query(category, city_name, area_info=None):
    """
    Constructs the Overpass QL query string.
    """
    # Normalize category
    cat_lower = category.lower().strip()
    tags_to_query = CATEGORY_MAPPINGS.get(cat_lower)
    
    if not tags_to_query:
        # Dynamic fallback: check key-value combinations
        val = cat_lower.replace(" ", "_")
        tags_to_query = [
            ("amenity", val),
            ("shop", val),
            ("office", val),
            ("craft", val),
            ("tourism", val),
            ("leisure", val)
        ]
        
    # Construct tag filter parts
    # Example: node(area.searchArea)[amenity=dentist];
    query_types = ["node", "way", "relation"]
    
    body_statements = []
    
    if isinstance(area_info, int):
        # We have a specific Overpass area ID
        prefix = f"[out:json][timeout:30];\narea({area_info})->.searchArea;\n("
        for q_type in query_types:
            for key, val in tags_to_query:
                body_statements.append(f"  {q_type}(area.searchArea)[{key}={val}];")
        suffix = "\n);\nout center;"
        query = prefix + "\n" + "\n".join(body_statements) + suffix
    elif isinstance(area_info, dict) and "lat" in area_info and "lon" in area_info:
        # Bounding radius fallback (5000 meters around Nominatim coordinates)
        lat, lon = area_info["lat"], area_info["lon"]
        prefix = f"[out:json][timeout:30];\n("
        for q_type in query_types:
            for key, val in tags_to_query:
                body_statements.append(f"  {q_type}(around:5000,{lat},{lon})[{key}={val}];")
        suffix = "\n);\nout center;"
        query = prefix + "\n" + "\n".join(body_statements) + suffix
    else:
        # Traditional name search fallback (may match multiple locations globally if ambiguous)
        prefix = f"[out:json][timeout:30];\narea[name=\"{city_name}\"]->.searchArea;\n("
        for q_type in query_types:
            for key, val in tags_to_query:
                body_statements.append(f"  {q_type}(area.searchArea)[{key}={val}];")
        suffix = "\n);\nout center;"
        query = prefix + "\n" + "\n".join(body_statements) + suffix

    return query

def parse_osm_response(data):
    """
    Parses Overpass API response JSON and returns a list of standardized business dicts.
    """
    businesses = []
    elements = data.get("elements", [])
    
    for element in elements:
        tags = element.get("tags", {})
        if not tags:
            continue
            
        name = tags.get("name")
        if not name:
            continue
            
        # Parse Phone
        phone = tags.get("phone") or tags.get("contact:phone") or tags.get("phone:mobile") or "N/A"
        
        # Parse Website
        website = tags.get("website") or tags.get("contact:website") or tags.get("url") or "NONE"
        if website != "NONE":
            # Basic validation/cleanup of website URL
            website = website.strip()
            if not website.startswith(("http://", "https://")):
                website = "http://" + website
                
        # Parse Address
        addr_parts = []
        if tags.get("addr:housenumber"):
            addr_parts.append(tags.get("addr:housenumber"))
        if tags.get("addr:street"):
            addr_parts.append(tags.get("addr:street"))
        if tags.get("addr:suburb"):
            addr_parts.append(tags.get("addr:suburb"))
        if tags.get("addr:city"):
            addr_parts.append(tags.get("addr:city"))
        if tags.get("addr:postcode"):
            addr_parts.append(tags.get("addr:postcode"))
            
        address = ", ".join(addr_parts) if addr_parts else "N/A"
        
        # Extract lat/lon coordinates
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lon = element.get("lon") or element.get("center", {}).get("lon")
        
        businesses.append({
            "name": name,
            "phone": phone,
            "address": address,
            "website": website,
            "lat": lat,
            "lon": lon,
            "source": "osm"
        })
        
    return businesses

def fetch_leads_from_osm(category, city_name):
    """
    Public entrypoint for OSM fetch.
    """
    print(f"[OSM] Geocoding city '{city_name}'...")
    area_info = geocode_city_to_area(city_name)
    
    # Rate limit compliance for Nominatim
    time.sleep(1.0)
    
    query = build_overpass_query(category, city_name, area_info)
    
    print("[OSM] Querying Overpass API...")
    try:
        response = requests.post(OVERPASS_URL, headers=HEADERS, data={"data": query}, timeout=30)
        response.raise_for_status()
        results = parse_osm_response(response.json())
        print(f"[OSM] Found {len(results)} businesses matching '{category}' in '{city_name}'.")
        return results
    except Exception as e:
        print(f"[OSM] Error fetching from Overpass API: {e}")
        return []
