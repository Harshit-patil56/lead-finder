import React from "react";
import { Search, MapPin, Loader } from "lucide-react";

export default function SearchBar({
  category,
  setCategory,
  city,
  setCity,
  includeMapsScrape,
  setIncludeMapsScrape,
  onSearch,
  loading
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (category.trim() && city.trim()) {
      onSearch();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full flex flex-col gap-3">
      {/* Pill Search Bar */}
      <div className="flex items-center w-full bg-white rounded-full border border-google-border shadow-md hover:shadow-lg transition-shadow duration-200 px-4 py-1.5">
        <Search className="text-google-textSecondary mr-2 h-5 w-5 flex-shrink-0" />
        
        {/* Category Input */}
        <input
          type="text"
          placeholder="Search category (e.g. dentist)"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-1/2 text-sm text-google-textPrimary placeholder-google-textSecondary bg-transparent border-none outline-none py-1.5 focus:ring-0"
          required
        />
        
        {/* Vertical Separator */}
        <div className="h-6 w-px bg-google-border mx-2"></div>
        
        <MapPin className="text-google-textSecondary mr-1 h-5 w-5 flex-shrink-0" />
        
        {/* City Input */}
        <input
          type="text"
          placeholder="City/Region"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="w-1/2 text-sm text-google-textPrimary bg-transparent border-none outline-none py-1.5 focus:ring-0 placeholder-google-textSecondary"
          required
        />
        
        {/* Search button */}
        <button
          type="submit"
          disabled={loading}
          className="bg-google-blue hover:bg-opacity-90 text-white rounded-full p-2 ml-1 flex items-center justify-center transition-colors flex-shrink-0"
        >
          {loading ? (
            <Loader className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Google Maps Scraper Flag Toggle */}
      <div className="flex items-center px-4 gap-2">
        <label className="flex items-center cursor-pointer select-none text-xs text-google-textSecondary font-medium">
          <input
            type="checkbox"
            checked={includeMapsScrape}
            onChange={(e) => setIncludeMapsScrape(e.target.checked)}
            className="rounded border-google-border text-google-blue focus:ring-google-blue mr-2 h-3.5 w-3.5"
          />
          Include Google Maps Fallback Scraper
        </label>
      </div>
    </form>
  );
}
