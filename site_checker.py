import re
import datetime
import socket
import ssl
import urllib.parse
import requests
from bs4 import BeautifulSoup

# HTTP request headers to simulate a normal browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

def extract_copyright_year(text_content):
    """
    Scans the text content for a 4-digit copyright year.
    It locates 4-digit years starting with '20' and checks if copyright markers
    (e.g., '©', 'copyright', 'copr.') exist within a 60-character neighborhood.
    Returns the latest copyright year found, or None.
    """
    if not text_content:
        return None
        
    indicators = ["copyright", "©", "&copy;", "copr.", "all rights reserved"]
    years = []
    
    # Match any 4-digit year in the range 2000-2099
    year_pattern = re.compile(r'\b(20\d{2})\b')
    
    for match in year_pattern.finditer(text_content):
        year = int(match.group(1))
        # Inspect context window around the matched year
        start_idx = max(0, match.start() - 60)
        end_idx = min(len(text_content), match.end() + 60)
        context = text_content[start_idx:end_idx].lower()
        
        if any(ind in context for ind in indicators):
            years.append(year)
            
    return max(years) if years else None

def check_ssl_expiry(domain, port=443, timeout=5):
    """
    Checks the SSL certificate expiration days remaining for a given domain.
    Returns:
        int: Number of days until the certificate expires.
        None: If the check fails or certificate cannot be retrieved.
    """
    if not domain or domain.lower() in ("localhost", "127.0.0.1"):
        return None
        
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    return None
                expiry_str = cert.get('notAfter')
                if not expiry_str:
                    return None
                expiry_date = datetime.datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry_date - datetime.datetime.now()).days
                return days_left
    except Exception as e:
        print(f"[Site Checker] SSL certificate expiry check failed for {domain}: {e}")
        return None

def check_website(url):
    """
    Checks the quality of a business website and flags issues.
    Returns:
        tuple: (status, reason_flagged)
            - status: "outdated", "ok", or "unchecked"
            - reason_flagged: comma-separated list of flags (e.g. "no_https, no_viewport") or "N/A"
    """
    if not url or url == "NONE":
        return "no_website", "N/A"
        
    # Standardize url format
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
        
    flags = []
    
    # Extract domain for socket SSL check
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.split(':')[0]
    except Exception:
        domain = None
        
    # Check SSL Expiry
    if domain:
        days_left = check_ssl_expiry(domain)
        if days_left is not None:
            if days_left <= 0:
                flags.append("expired_ssl")
            elif days_left < 15:
                flags.append(f"ssl_expiring_soon ({days_left} days)")
    
    # 1. Check HTTPS / SSL
    # If the URL is http, check if we get SSL errors, or if we are redirected to https.
    has_https_support = True
    
    # We will attempt to connect to the website
    try:
        # We perform a GET request with redirect following
        response = requests.get(url, headers=HEADERS, timeout=10, verify=True)
        
        # If we didn't end up on https, we flag no_https
        final_url = response.url
        if not final_url.startswith("https://") and "expired_ssl" not in flags:
            flags.append("no_https")
            
        # Check HTTP Status Code
        if response.status_code >= 400:
            return "outdated", f"failed_load (HTTP {response.status_code})"
            
    except requests.exceptions.SSLError:
        # SSL Verification Failed
        flags.append("no_https")
        has_https_support = False
        # If SSL fails, retry with verify=False to check other heuristics (viewport/copyright)
        try:
            response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if response.status_code >= 400:
                return "outdated", f"failed_load (HTTP {response.status_code} + SSL error)"
        except Exception:
            return "outdated", "failed_load (SSL error & connection failed)"
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        return "outdated", f"failed_load ({type(e).__name__})"
    except Exception as e:
        return "outdated", f"failed_load (error: {str(e)})"

    # Parsed HTML Heuristics
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 2. Check for mobile responsive meta tag (meta viewport)
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not viewport:
            flags.append("no_viewport")
            
        # Extract page text safely to look for copyright
        # Remove script/style tag contents to avoid false positive years
        for script in soup(["script", "style"]):
            script.decompose()
        visible_text = soup.get_text(separator=" ")
        
        # 3. Check for copyright age
        copyright_year = extract_copyright_year(visible_text)
        if copyright_year:
            current_year = datetime.datetime.now().year
            # More than 3 years old means current_year - year > 3
            if current_year - copyright_year > 3:
                flags.append(f"outdated_copyright ({copyright_year})")
    except Exception as e:
        # If parsing fails but page loaded, we evaluate based on collected HTTP flags
        print(f"[Site Checker] Parse warning for {url}: {e}")
        
    if flags:
        return "outdated", ", ".join(flags)
    return "ok", "N/A"
