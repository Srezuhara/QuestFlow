import { useRef } from "react";
import { StatusBadge } from "@/components/ui";
import { cn } from "@/lib/cn";
import { formatShardTime } from "../format";
import type { NoteSummaryOut } from "../api";

export function NoteList({
  notes,
  selectedId,
  onSelect,
}: {
  notes: NoteSummaryOut[];
  selectedId: string | undefined;
  onSelect: (noteId: string) => void;
}) {
  const rowRefs = useRef<(HTMLButtonElement | null)[]>([]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (e.key === "ArrowDown") next = Math.min(index + 1, notes.length - 1);
    else if (e.key === "ArrowUp") next = Math.max(index - 1, 0);
    else return;
    e.preventDefault();
    rowRefs.current[next]?.focus();
    const note = notes[next];
    if (note) onSelect(note.id);
  }

  if (notes.length === 0) {
    return (
      <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
        No data shards found
      </p>
    );
  }

  return (
    <div role="listbox" aria-label="Notes" className="flex flex-col gap-2">
      {notes.map((note, index) => {
        const isSelected = note.id === selectedId;
        return (
          <button
            key={note.id}
            ref={(el) => {
              rowRefs.current[index] = el;
            }}
            type="button"
            role="option"
            aria-selected={isSelected}
            tabIndex={isSelected || (selectedId === undefined && index === 0) ? 0 : -1}
            onKeyDown={(e) => handleKeyDown(e, index)}
            onClick={() => onSelect(note.id)}
            className={cn(
              "clip-chamfer flex flex-col gap-1 border p-3 text-left outline-none transition-colors",
              isSelected
                ? "border-neon-lime bg-surface-container shadow-[0_0_12px_rgba(195,244,0,0.25)]"
                : "border-outline-variant bg-surface-container-lowest hover:border-outline",
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="truncate font-body text-body-md text-on-surface">
                {note.is_pinned && <span className="mr-1 text-neon-yellow">★</span>}
                {note.title}
              </span>
              <span className="shrink-0 font-mono text-label-mono text-on-surface-variant">
                {formatShardTime(note.updated_at)}
              </span>
            </div>
            {note.excerpt && (
              <p className="line-clamp-2 font-body text-body-sm text-on-surface-variant">
                {note.excerpt}
              </p>
            )}
            {note.tags.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {note.tags.map((tag) => (
                  <StatusBadge key={tag.id} level="later">
                    {tag.name}
                  </StatusBadge>
                ))}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
