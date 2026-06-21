import React from "react";
import { Check } from "lucide-react";

export default function FilterChips({ currentFilter, setCurrentFilter, counts }) {
  const chips = [
    { id: "all", label: "All Leads", count: counts.total, color: "google-blue" },
    { id: "no_website", label: "No Website", count: counts.no_website, color: "google-red" },
    { id: "outdated", label: "Outdated Website", count: counts.outdated, color: "google-yellow" },
    { id: "ok", label: "OK", count: counts.ok, color: "google-green" },
  ];

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1 px-1 custom-scrollbar scrollbar-thin">
      {chips.map((chip) => {
        const isActive = currentFilter === chip.id;
        
        let activeStyles = "bg-google-blue text-white border-google-blue";
        if (isActive) {
          if (chip.id === "no_website") activeStyles = "bg-[#fce8e6] text-google-red border-google-red border";
          else if (chip.id === "outdated") activeStyles = "bg-[#fef7e0] text-[#b06000] border-google-yellow border";
          else if (chip.id === "ok") activeStyles = "bg-[#e6f4ea] text-google-green border-google-green border";
        }

        const idleStyles = "bg-white text-google-textPrimary border-google-border hover:bg-google-bgHover";

        return (
          <button
            key={chip.id}
            onClick={() => setCurrentFilter(chip.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 border rounded-full text-xs font-medium whitespace-nowrap transition-all select-none ${
              isActive ? activeStyles : idleStyles
            }`}
          >
            {isActive && <Check className="h-3 w-3 flex-shrink-0" />}
            <span>{chip.label}</span>
            <span className={`opacity-80 text-[10px] px-1.5 py-0.5 rounded-full ${
              isActive ? "bg-black bg-opacity-10" : "bg-gray-100 text-google-textSecondary"
            }`}>
              {chip.count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
