# Lead Finder Web Interface

We built this React client to give you an interactive, visual search interface styled after Google Maps. It lets you inspect lead cards, query details, and view pins dynamically on a full-screen map.

---

## ✨ Features

- **Google Maps Layout**: An aligned list panel on the left with search pills, filters, and scrollable results next to a full-screen interactive Leaflet map.
- **Bidirectional Sync**: 
  - Hover over a card in the sidebar to highlight its corresponding pin on the map.
  - Click on a card to automatically fly the map over to its coordinates and open its marker popup.
  - Click on a marker pin to view the business name, address, phone number, website status, and specific audit flags.
- **Coordinates Jittering**: If multiple businesses share the exact same address, the map automatically spreads them out in a neat circular spiral on zoom so all pins remain easily clickable.
- **Responsive Badges**: Quickly see who is missing a website (Red badge) or running an outdated site (Yellow badge).

---

## 🛠️ Getting Started

### 1. Install Frontend Packages
Navigate to this directory in your terminal and install the node dependencies:
```bash
npm install
```

### 2. Configure Environment Variables (Optional)
By default, the app is configured to talk to the local API on `http://localhost:8000`. If you are running the backend on a different host or port, create a `.env` file in this directory:
```env
VITE_API_URL=http://your-custom-api-host:8000
```

### 3. Launch Development Server
Start the Vite local development server:
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

---

> [!NOTE]  
> The map rendering is fully powered by OpenStreetMap tiles and Leaflet.js. It requires **no API keys** or paid services to run!
