# Lead Finder

Welcome! We built **Lead Finder** to help web design agencies easily find local businesses that either have **no website** or are running on **outdated, mobile-unresponsive web layouts**. It is designed to be lightweight, fast, and completely free to run—no paid APIs or accounts required.

We pull coordinates, names, and contact details directly from **OpenStreetMap** (using Nominatim and the Overpass API) and offer an optional, rate-limited **Google Maps scraper** (using Playwright) as a fallback. For every business with a website, we run a parallel quality checker to flag responsiveness issues, old copyrights, lack of HTTPS/SSL, or broken links.

---

## 🚀 How it Works (Heuristics)

To help you find high-converting cold calling leads, we audit every discovered website against these quality markers:

1. **Accessibility**: If the page returns a `4xx`/`5xx` error code, or fails to connect/times out, we flag it as `failed_load`.
2. **HTTPS / SSL**: If the website does not support HTTPS or has certificate errors, we flag it as `no_https`.
3. **Mobile Responsive**: We search the HTML head for a `<meta name="viewport">` tag. If it's missing, the site is flagged as `no_viewport` (meaning it's likely not responsive on mobile screens).
4. **Outdated Copyright**: We scan the page text for copyright notices (e.g. "©" or "Copyright") next to a year. If the latest copyright year listed is more than 3 years old, it is flagged as `outdated_copyright`.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
Make sure you have **Python 3.8+** and **Node.js (v18+)** installed on your system.

### 2. Install Backend Dependencies
Install the required packages from the root directory:
```bash
pip install -r requirements.txt
```

### 3. Install Playwright (Optional Fallback)
If you want to use the Google Maps scraper fallback, install the Playwright Chromium browser:
```bash
playwright install chromium
```

---

## 💻 Running the Application

You can use Lead Finder either as a command-line tool or through our custom Google Maps-like Web UI.

### Option A: The Web Interface (Recommended)

1. **Start the local API server**:
   ```bash
   uvicorn api:app --reload
   ```
   *This starts the FastAPI server on `http://localhost:8000`.*

2. **Start the React Frontend**:
   In a new terminal window, navigate to the frontend folder, install dependencies, and launch the dev server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser.*

### Option B: The CLI Tool

Run a search query directly from your command line:
```bash
python main.py --city "Palo Alto" --category "dentist" --output leads.csv
```

#### CLI Flags
* `--city`, `-c` *(Required)*: The target city/region (e.g., "Austin, TX").
* `--category`, `-g` *(Required)*: The business type (e.g., "bakery", "dentist").
* `--output`, `-o` *(Optional)*: Filepath for the CSV export. Defaults to `leads.csv`.
* `--include-maps-scrape` *(Optional Flag)*: Activates the rate-limited Playwright Google Maps fallback scraper.
* `--max-results` *(Optional)*: Caps the number of scraper results. Defaults to `30`.

---

> [!WARNING]  
> Automated scraping of Google Maps may violate Google's Terms of Service. Please use the `--include-maps-scrape` flag responsibly and sparingly.

> [!TIP]
> The backend runs audits in parallel using 30 concurrent threads. Web audits for large batch results (e.g. 500+ leads) will finish in seconds.
