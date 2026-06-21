import React from "react";
import { Phone, Globe, Globe2, AlertCircle, CheckCircle, MapPinOff } from "lucide-react";

export default function ResultCard({
  lead,
  isSelected,
  onSelect,
  onHoverStart,
  onHoverEnd
}) {
  const { business_name, phone, address, website, status, reason_flagged, latitude, longitude } = lead;

  const hasCoords = latitude !== null && longitude !== null && latitude !== undefined && longitude !== undefined;

  // Status badge styling
  let badgeText = "OK";
  let badgeColor = "bg-[#e6f4ea] text-google-green border-google-green";
  let BadgeIcon = CheckCircle;

  if (status === "no_website") {
    badgeText = "No Website";
    badgeColor = "bg-[#fce8e6] text-google-red border-google-red";
    BadgeIcon = AlertCircle;
  } else if (status === "outdated") {
    badgeText = "Outdated Website";
    badgeColor = "bg-[#fef7e0] text-[#b06000] border-google-yellow";
    BadgeIcon = AlertCircle;
  } else if (status === "unchecked") {
    badgeText = "Unchecked";
    badgeColor = "bg-gray-100 text-google-textSecondary border-google-border";
    BadgeIcon = AlertCircle;
  }

  const handleCardClick = () => {
    onSelect(lead);
  };

  return (
    <div
      onClick={handleCardClick}
      onMouseEnter={onHoverStart}
      onMouseLeave={onHoverEnd}
      className={`px-4 py-3 border-b border-google-border cursor-pointer transition-colors duration-150 select-none text-left ${
        isSelected ? "bg-google-bgHover border-l-4 border-l-google-blue pl-3" : "hover:bg-google-bgHover"
      }`}
    >
      {/* Name and Status Badge */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <h3 className="font-semibold text-google-textPrimary text-base leading-snug">
          {business_name}
        </h3>
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeColor}`}>
          <BadgeIcon className="h-3 w-3 flex-shrink-0" />
          {badgeText}
        </span>
      </div>

      {/* Address */}
      <p className="text-google-textSecondary text-sm mb-2 line-clamp-2">
        {address || "No address listed"}
      </p>

      {/* Details Row */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-google-textSecondary">
        {/* Phone */}
        <div className="flex items-center gap-1">
          <Phone className="h-3.5 w-3.5 text-google-textSecondary flex-shrink-0" />
          <span>{phone && phone !== "N/A" ? phone : "No phone listed"}</span>
        </div>

        {/* Website Link */}
        <div className="flex items-center gap-1">
          {website && website !== "NONE" ? (
            <>
              <Globe className="h-3.5 w-3.5 text-google-blue flex-shrink-0" />
              <a
                href={website}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-google-blue hover:underline font-medium line-clamp-1 max-w-[150px]"
              >
                Visit Site
              </a>
            </>
          ) : (
            <>
              <Globe2 className="h-3.5 w-3.5 text-google-red opacity-60 flex-shrink-0" />
              <span className="text-google-red opacity-80">No website found</span>
            </>
          )}
        </div>
      </div>

      {/* Outdated Reason */}
      {status === "outdated" && reason_flagged && reason_flagged !== "N/A" && (
        <div className="mt-2 text-xs bg-[#fef7e0] border border-[#f5c642] border-opacity-30 rounded px-2.5 py-1 text-[#8f4d00]">
          <strong>Flags:</strong> {reason_flagged}
        </div>
      )}

      {/* Coordinate warning */}
      {!hasCoords && (
        <div className="mt-2 flex items-center gap-1 text-[11px] text-[#ea4335] bg-[#fce8e6] bg-opacity-30 px-2 py-0.5 rounded w-fit border border-[#ea4335] border-opacity-10">
          <MapPinOff className="h-3 w-3" />
          <span>Location unavailable on map</span>
        </div>
      )}
    </div>
  );
}
