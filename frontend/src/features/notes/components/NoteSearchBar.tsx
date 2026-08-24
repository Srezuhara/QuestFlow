import { useState } from "react";
import { Filter } from "lucide-react";

export function NoteSearchBar({
  value,
  onChange,
  availableTags,
  selectedTags,
  onToggleTag,
}: {
  value: string;
  onChange: (q: string) => void;
  availableTags: string[];
  selectedTags: string[];
  onToggleTag: (tag: string) => void;
}) {
  const [filterOpen, setFilterOpen] = useState(false);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="&gt; SEARCH_VAULT"
          aria-label="Search notes"
          className="clip-chamfer flex-1 border border-outline-variant bg-surface-container-lowest px-3 py-2 font-mono text-label-mono text-on-surface outline-none placeholder:text-on-surface-variant focus:border-neon-lime"
        />
        {availableTags.length > 0 && (
          <button
            type="button"
            aria-label="Filter by tag"
            aria-expanded={filterOpen}
            onClick={() => setFilterOpen((v) => !v)}
            className={
              selectedTags.length > 0
                ? "text-neon-lime"
                : "text-on-surface-variant hover:text-on-surface"
            }
          >
            <Filter size={18} aria-hidden="true" />
          </button>
        )}
      </div>
      {filterOpen && availableTags.length > 0 && (
        <div className="clip-chamfer flex flex-wrap gap-2 border border-outline-variant bg-surface-container-lowest p-3">
          {availableTags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => onToggleTag(tag)}
              className={
                selectedTags.includes(tag)
                  ? "border border-neon-lime px-2 py-0.5 font-mono text-label-mono text-neon-lime uppercase"
                  : "border border-outline-variant px-2 py-0.5 font-mono text-label-mono text-on-surface-variant uppercase hover:border-outline"
              }
            >
              {tag}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
