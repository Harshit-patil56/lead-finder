import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { Phone, Globe, Copy, AlertTriangle, Check } from "lucide-react";

// Import Leaflet styles
import "leaflet/dist/leaflet.css";

// Helper to create Google Maps style custom markers (red/yellow/green)
const createCustomIcon = (status, isHighlighted) => {
  let color = "#ea4335"; // Google red (no website)
  if (status === "ok") {
    color = "#34a853"; // Google green (ok)
  } else if (status === "outdated") {
    color = "#fbbc04"; // Google yellow (outdated)
  } else if (status === "unchecked") {
    color = "#5f6368"; // Gray (unchecked)
  }

  const scale = isHighlighted ? "scale(1.3)" : "scale(1.0)";
  const zIndex = isHighlighted ? 1000 : 1;

  // Custom Google Maps Pin SVG
  const html = `
    <div style="transform: ${scale}; transform-origin: bottom center; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3)); z-index: ${zIndex}; cursor: pointer;">
      <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="${color}" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
        <circle cx="12" cy="10" r="3" fill="#ffffff"/>
      </svg>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: "custom-leaflet-marker",
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30]
  });
};

// Map controller to handle auto-fitting bounds and panning/zooming to selected lead
function MapController({ leads, selectedLead }) {
  const map = useMap();

  // Fit bounds when leads list changes
  useEffect(() => {
    if (!leads || leads.length === 0) return;

    const validCoords = leads
      .filter(l => l.latitude !== null && l.longitude !== null && l.latitude !== undefined && l.longitude !== undefined)
      .map(l => [l.latitude, l.longitude]);

    if (validCoords.length > 0) {
      map.fitBounds(validCoords, { padding: [50, 50], maxZoom: 15 });
    }
  }, [leads, map]);

  // Pan to selected lead when selected programmatically
  useEffect(() => {
    if (selectedLead && selectedLead.latitude !== null && selectedLead.longitude !== null && selectedLead.latitude !== undefined && selectedLead.longitude !== undefined) {
      map.setView([selectedLead.latitude, selectedLead.longitude], 16, {
        animate: true,
        duration: 0.8
      });
    }
  }, [selectedLead, map]);

  return null;
}

// Subcomponent for Marker to handle programmatic popup opening
const MarkerWithPopup = ({ lead, isSelected, hoveredLeadId, onSelectLead }) => {
  const markerRef = useRef(null);

  useEffect(() => {
    if (isSelected && markerRef.current) {
      markerRef.current.openPopup();
    }
  }, [isSelected]);

  const isHighlighted = hoveredLeadId === lead.business_name || isSelected;
  const icon = createCustomIcon(lead.status, isHighlighted);

  const [copied, setCopied] = React.useState(false);

  const handleCopyAddress = (e) => {
    e.stopPropagation();
    if (lead.address) {
      navigator.clipboard.writeText(lead.address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Status badge classes inside popup
  let statusBadgeText = "OK";
  let statusBadgeColor = "bg-[#e6f4ea] text-google-green border-google-green";
  if (lead.status === "no_website") {
    statusBadgeText = "No Website";
    statusBadgeColor = "bg-[#fce8e6] text-google-red border-google-red";
  } else if (lead.status === "outdated") {
    statusBadgeText = "Outdated";
    statusBadgeColor = "bg-[#fef7e0] text-[#b06000] border-google-yellow";
  } else if (lead.status === "unchecked") {
    statusBadgeText = "Unchecked";
    statusBadgeColor = "bg-gray-100 text-google-textSecondary border-google-border";
  }

  return (
    <Marker
      ref={markerRef}
      position={[lead.latitude, lead.longitude]}
      icon={icon}
      eventHandlers={{
        click: () => {
          onSelectLead(lead);
        }
      }}
    >
      <Popup>
        <div className="flex flex-col gap-2 max-w-[240px] text-left">
          {/* Header */}
          <div className="flex flex-col gap-1">
            <h4 className="font-bold text-google-textPrimary text-sm leading-snug">
              {lead.business_name}
            </h4>
            <span className={`inline-flex items-center w-fit px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusBadgeColor}`}>
              {statusBadgeText}
            </span>
          </div>

          {/* Address */}
          <p className="text-google-textSecondary text-xs">
            {lead.address || "No address listed"}
          </p>

          {/* Outdated Reason */}
          {lead.status === "outdated" && lead.reason_flagged && lead.reason_flagged !== "N/A" && (
            <div className="text-[10px] bg-[#fef7e0] border border-[#f5c642] border-opacity-30 rounded px-2 py-1 text-[#8f4d00]">
              <strong>Reason:</strong> {lead.reason_flagged}
            </div>
          )}

          {/* Phone */}
          {lead.phone && lead.phone !== "N/A" && (
            <div className="flex items-center gap-1.5 text-xs text-google-textSecondary">
              <Phone className="h-3.5 w-3.5 flex-shrink-0" />
              <span>{lead.phone}</span>
            </div>
          )}

          {/* Action Row */}
          <div className="flex gap-2 mt-2 pt-2 border-t border-google-border">
            {lead.phone && lead.phone !== "N/A" && (
              <a
                href={`tel:${lead.phone}`}
                className="flex-1 flex items-center justify-center gap-1 text-xs bg-google-blue hover:bg-opacity-95 !text-white font-medium py-1.5 px-2.5 rounded transition-colors duration-150 no-underline"
              >
                <Phone className="h-3 w-3" />
                Call
              </a>
            )}

            <button
              onClick={handleCopyAddress}
              className="flex-1 flex items-center justify-center gap-1 text-xs bg-white hover:bg-google-bgHover text-google-textPrimary border border-google-border font-medium py-1.5 px-2.5 rounded transition-colors duration-150"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-google-green" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  Copy
                </>
              )}
            </button>
          </div>

          {/* Website Target */}
          <div className="mt-1 flex items-center justify-center">
            {lead.website && lead.website !== "NONE" ? (
              <a
                href={lead.website}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] !text-google-blue hover:underline font-medium inline-flex items-center gap-1 mt-1"
              >
                <Globe className="h-3 w-3" />
                Open Website
              </a>
            ) : (
              <span className="text-[11px] text-google-red opacity-80 mt-1">
                No website found
              </span>
            )}
          </div>
        </div>
      </Popup>
    </Marker>
  );
};

export default function MapView({ leads, selectedLead, hoveredLeadId, onSelectLead }) {
  // Filter leads with valid coordinates
  const validLeads = leads ? leads.filter(
    (l) => l.latitude !== null && l.longitude !== null && l.latitude !== undefined && l.longitude !== undefined
  ) : [];

  const hasLocations = validLeads.length > 0;

  return (
    <div className="w-full h-full relative">
      {hasLocations ? (
        <MapContainer
          center={[37.4419, -122.143]} // Default to Palo Alto coordinates
          zoom={13}
          style={{ width: "100%", height: "100%" }}
          zoomControl={false} // Custom zoom buttons if needed, or hide to match clean layout
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {validLeads.map((lead, idx) => (
            <MarkerWithPopup
              key={idx}
              lead={lead}
              isSelected={selectedLead && selectedLead.business_name === lead.business_name}
              hoveredLeadId={hoveredLeadId}
              onSelectLead={onSelectLead}
            />
          ))}

          <MapController leads={validLeads} selectedLead={selectedLead} />
        </MapContainer>
      ) : (
        <div className="w-full h-full bg-google-bgHover flex flex-col items-center justify-center text-center p-6 border-l border-google-border">
          <AlertTriangle className="h-12 w-12 text-google-textSecondary opacity-30 mb-2" />
          <h3 className="font-semibold text-google-textPrimary mb-1">No Locations to Display</h3>
          <p className="text-xs text-google-textSecondary max-w-xs">
            Start a query or select a category with geographic details to display pins on the map.
          </p>
        </div>
      )}
    </div>
  );
}
