import React from "react";
import ResultCard from "./ResultCard";
import { Search, AlertTriangle, Inbox } from "lucide-react";

export default function ResultsList({
  leads,
  loading,
  error,
  selectedLead,
  onSelectLead,
  setHoveredLeadId
}) {
  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {/* Google-like top progress loading bar */}
        <div className="w-full h-1 bg-[#e8f0fe] overflow-hidden relative">
          <div className="absolute top-0 bottom-0 left-0 bg-google-blue w-1/3 animate-[loadingBar_1.5s_infinite_linear]"></div>
        </div>
        
        {/* Render 5 skeleton cards */}
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="px-4 py-4 border-b border-google-border animate-pulse text-left">
            <div className="flex justify-between items-start mb-2.5">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-5 bg-gray-200 rounded-full w-24"></div>
            </div>
            <div className="h-3 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div className="flex gap-4">
              <div className="h-3.5 bg-gray-100 rounded w-1/4"></div>
              <div className="h-3.5 bg-gray-100 rounded w-1/4"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-google-red bg-[#fce8e6] bg-opacity-20 border-t border-b border-google-red border-opacity-10">
        <AlertTriangle className="h-8 w-8 mb-2 flex-shrink-0" />
        <h4 className="font-semibold text-google-textPrimary mb-1">Search Failed</h4>
        <p className="text-xs text-google-textSecondary max-w-xs">{error}</p>
      </div>
    );
  }

  if (!leads || leads.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-google-textSecondary">
        <Inbox className="h-10 w-10 text-google-border mb-3" />
        <h4 className="font-medium text-google-textPrimary mb-1">No Leads Found</h4>
        <p className="text-xs max-w-xs">
          Search for a category and city to locate businesses with missing or outdated websites.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Count Header */}
      <div className="px-4 py-2 bg-google-bgHover border-b border-google-border text-left text-xs font-semibold text-google-textSecondary">
        {leads.length} {leads.length === 1 ? "result" : "results"} found
      </div>

      {/* Result Cards Scrollable List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar min-h-0">
        {leads.map((lead, idx) => (
          <ResultCard
            key={idx}
            lead={lead}
            isSelected={selectedLead && selectedLead.business_name === lead.business_name}
            onSelect={onSelectLead}
            onHoverStart={() => setHoveredLeadId(lead.business_name)}
            onHoverEnd={() => setHoveredLeadId(null)}
          />
        ))}
      </div>
    </div>
  );
}
