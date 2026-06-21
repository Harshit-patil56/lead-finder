import React from "react";
import { Check, Phone } from "lucide-react";

export default function FilterChips({ 
  currentFilter, 
  setCurrentFilter, 
  hasPhoneOnly, 
  setHasPhoneOnly, 
  counts 
}) {
  const chips = [
    { id: "all", label: "All Leads", count: counts.total, isStatus: true },
    { id: "no_website", label: "No Website", count: counts.no_website, isStatus: true },
    { id: "outdated", label: "Outdated Website", count: counts.outdated, isStatus: true },
    { id: "ok", label: "OK", count: counts.ok, isStatus: true },
    { id: "has_phone", label: "With Phone", count: counts.has_phone, isStatus: false },
  ];

  return (
    <div className="flex flex-wrap gap-2 pt-1 w-full">
      {chips.map((chip) => {
        const isActive = chip.isStatus ? (currentFilter === chip.id) : hasPhoneOnly;
        
        let activeStyles = "bg-google-blue text-white border-google-blue";
        if (isActive) {
          if (chip.id === "no_website") activeStyles = "bg-[#fce8e6] text-google-red border-google-red border";
          else if (chip.id === "outdated") activeStyles = "bg-[#fef7e0] text-[#b06000] border-google-yellow border";
          else if (chip.id === "ok") activeStyles = "bg-[#e6f4ea] text-google-green border-google-green border";
          else if (chip.id === "has_phone") activeStyles = "bg-[#e8f0fe] text-google-blue border-google-blue border";
        }

        const idleStyles = "bg-white text-google-textPrimary border-google-border hover:bg-google-bgHover";

        const handleClick = () => {
          if (chip.isStatus) {
            setCurrentFilter(chip.id);
          } else {
            setHasPhoneOnly(!hasPhoneOnly);
          }
        };

        return (
          <button
            key={chip.id}
            type="button"
            onClick={handleClick}
            className={`flex items-center gap-1.5 px-3 py-1.5 border rounded-full text-xs font-medium cursor-pointer transition-all select-none ${
              isActive ? activeStyles : idleStyles
            }`}
          >
            {isActive ? (
              <Check className="h-3 w-3 flex-shrink-0" />
            ) : (
              chip.id === "has_phone" && <Phone className="h-3 w-3 text-google-textSecondary flex-shrink-0" />
            )}
            <span>{chip.label}</span>
            <span className={`opacity-80 text-[10px] px-1.5 py-0.5 rounded-full ${
              isActive 
                ? "bg-black/10 text-current" 
                : "bg-gray-100 text-google-textSecondary"
            }`}>
              {chip.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
