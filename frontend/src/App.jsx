import React, { useState, useEffect } from "react";
import { Globe } from "lucide-react";

// Components
import SearchBar from "./components/SearchBar";
import FilterChips from "./components/FilterChips";
import ResultsList from "./components/ResultsList";
import MapView from "./components/MapView";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Helper to jitter duplicate coordinates so overlapping markers are all clickable
const adjustDuplicateCoordinates = (leadsList) => {
  const coordsMap = new Map();
  return leadsList.map((lead) => {
    if (
      lead.latitude === null ||
      lead.longitude === null ||
      lead.latitude === undefined ||
      lead.longitude === undefined
    ) {
      return lead;
    }

    const key = `${lead.latitude.toFixed(5)}_${lead.longitude.toFixed(5)}`;
    if (coordsMap.has(key)) {
      const count = coordsMap.get(key) + 1;
      coordsMap.set(key, count);

      // Distribute overlapping markers in a neat spiral/circle (approx 4-5 meters offset)
      const angle = (count * 2 * Math.PI) / 8;
      const offsetRadius = 0.00004 * count;

      return {
        ...lead,
        latitude: lead.latitude + Math.cos(angle) * offsetRadius,
        longitude: lead.longitude + Math.sin(angle) * offsetRadius
      };
    } else {
      coordsMap.set(key, 0);
      return lead;
    }
  });
};

export default function App() {
  const [category, setCategory] = useState("dentist");
  const [city, setCity] = useState("Palo Alto");
  const [includeMapsScrape, setIncludeMapsScrape] = useState(false);

  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [selectedLead, setSelectedLead] = useState(null);
  const [hoveredLeadId, setHoveredLeadId] = useState(null);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [hasPhoneOnly, setHasPhoneOnly] = useState(false);

  const [counts, setCounts] = useState({
    total: 0,
    no_website: 0,
    outdated: 0,
    ok: 0,
    unchecked: 0
  });

  // Automatically fetch initial data on load
  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setSelectedLead(null);
    setCurrentFilter("all");
    setHasPhoneOnly(false);

    try {
      const url = new URL(`${API_URL}/api/leads`);
      url.searchParams.append("category", category);
      url.searchParams.append("city", city);
      url.searchParams.append("include_maps_scrape", includeMapsScrape);
      url.searchParams.append("max_results", 30);

      const response = await fetch(url.toString());
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Search request failed. Please check your inputs.");
      }

      const data = await response.json();

      // Apply offset to overlapping coordinates
      const adjustedLeads = adjustDuplicateCoordinates(data.leads || []);

      setLeads(adjustedLeads);

      if (data.summary) {
        setCounts(data.summary);
      } else {
        // Fallback calculations if summary is missing
        setCounts({
          total: adjustedLeads.length,
          no_website: adjustedLeads.filter((l) => l.status === "no_website").length,
          outdated: adjustedLeads.filter((l) => l.status === "outdated").length,
          ok: adjustedLeads.filter((l) => l.status === "ok").length,
          unchecked: adjustedLeads.filter((l) => l.status === "unchecked").length
        });
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not connect to the Lead Finder API. Make sure the backend server is running.");
      setLeads([]);
      setCounts({ total: 0, no_website: 0, outdated: 0, ok: 0, unchecked: 0 });
    } finally {
      setLoading(false);
    }
  };

  // Derive counts dynamically for the filters
  const dynamicCounts = {
    total: leads.filter((l) => !hasPhoneOnly || (l.phone && l.phone !== "N/A" && l.phone.trim() !== "")).length,
    no_website: leads.filter((l) => l.status === "no_website" && (!hasPhoneOnly || (l.phone && l.phone !== "N/A" && l.phone.trim() !== ""))).length,
    outdated: leads.filter((l) => l.status === "outdated" && (!hasPhoneOnly || (l.phone && l.phone !== "N/A" && l.phone.trim() !== ""))).length,
    ok: leads.filter((l) => l.status === "ok" && (!hasPhoneOnly || (l.phone && l.phone !== "N/A" && l.phone.trim() !== ""))).length,
    unchecked: leads.filter((l) => l.status === "unchecked" && (!hasPhoneOnly || (l.phone && l.phone !== "N/A" && l.phone.trim() !== ""))).length,
    has_phone: leads.filter((l) => {
      if (currentFilter !== "all" && l.status !== currentFilter) return false;
      return l.phone && l.phone !== "N/A" && l.phone.trim() !== "";
    }).length
  };

  // Filter leads shown in sidebar and on map
  const filteredLeads = leads.filter((lead) => {
    // 1. Status Filter
    if (currentFilter !== "all" && lead.status !== currentFilter) {
      return false;
    }
    // 2. Phone Filter
    if (hasPhoneOnly) {
      const hasPhone = lead.phone && lead.phone !== "N/A" && lead.phone.trim() !== "";
      if (!hasPhone) return false;
    }
    return true;
  });

  return (
    <div className="flex h-screen w-screen overflow-hidden font-sans text-google-textPrimary">
      {/* Left Sidebar */}
      <div className="w-[400px] h-full flex flex-col bg-white border-r border-google-border shadow-md z-10 flex-shrink-0">
        {/* Header container */}
        <div className="p-4 flex flex-col gap-3 border-b border-google-border">
          {/* Logo Title */}
          <div className="flex items-center gap-2 select-none">
            <div className="bg-google-blue text-white p-1.5 rounded-lg flex items-center justify-center">
              <Globe className="h-5 w-5" />
            </div>
            <h1 className="text-lg font-bold text-google-textPrimary tracking-tight">
              Lead Finder
            </h1>
          </div>

          {/* SearchBar */}
          <SearchBar
            category={category}
            setCategory={setCategory}
            city={city}
            setCity={setCity}
            includeMapsScrape={includeMapsScrape}
            setIncludeMapsScrape={setIncludeMapsScrape}
            onSearch={handleSearch}
            loading={loading}
          />

          {/* Filter Chips */}
          <FilterChips
            currentFilter={currentFilter}
            setCurrentFilter={setCurrentFilter}
            hasPhoneOnly={hasPhoneOnly}
            setHasPhoneOnly={setHasPhoneOnly}
            counts={dynamicCounts}
          />
        </div>

        {/* scrollable List */}
        <ResultsList
          leads={filteredLeads}
          loading={loading}
          error={error}
          selectedLead={selectedLead}
          onSelectLead={setSelectedLead}
          setHoveredLeadId={setHoveredLeadId}
        />
      </div>

      {/* Right Map View */}
      <div className="flex-grow h-full relative z-0">
        <MapView
          leads={filteredLeads}
          selectedLead={selectedLead}
          hoveredLeadId={hoveredLeadId}
          onSelectLead={setSelectedLead}
        />
      </div>
    </div>
  );
}
