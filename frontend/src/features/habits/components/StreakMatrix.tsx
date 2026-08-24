import { useRef, useState } from "react";
import { NeonPanel } from "@/components/ui";
import { useHabitMatrix } from "../hooks";
import type { HabitOut, MatrixCellStatus } from "../api";

const STATUS_CLASSES: Record<MatrixCellStatus, string> = {
  empty: "bg-surface-container-high",
  partial: "bg-neon-lime/30",
  hit: "bg-neon-lime/70",
  exceeded: "bg-neon-lime shadow-[0_0_8px_rgba(195,244,0,0.8)]",
  broken: "bg-neon-pink shadow-[0_0_8px_rgba(254,0,254,0.6)]",
};

function formatCellLabel(date: string, count: number, target: number, status: MatrixCellStatus) {
  const pretty = new Date(`${date}T00:00:00`).toLocaleDateString(undefined, {
    month: "long",
    day: "numeric",
  });
  return `${pretty} — ${count} of ${target}, ${status}`;
}

export function StreakMatrix({ habits }: { habits: HabitOut[] }) {
  const [selectedId, setSelectedId] = useState<string | undefined>(habits[0]?.id);
  const activeId = selectedId ?? habits[0]?.id;
  const { data: matrix, isLoading } = useHabitMatrix(activeId);
  const cellRefs = useRef<(HTMLButtonElement | null)[]>([]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (e.key === "ArrowRight") next = index + 1;
    else if (e.key === "ArrowLeft") next = index - 1;
    else if (e.key === "ArrowDown") next = index + 7;
    else if (e.key === "ArrowUp") next = index - 7;
    else return;
    e.preventDefault();
    cellRefs.current[next]?.focus();
  }

  return (
    <NeonPanel>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-surface-container-highest pb-4">
        <h2 className="font-display text-title-md text-on-surface uppercase">Streak Matrix</h2>
        {habits.length > 1 && (
          <select
            value={activeId}
            onChange={(e) => setSelectedId(e.target.value)}
            aria-label="Select habit"
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-1.5 font-mono text-label-mono text-on-surface outline-none focus:border-neon-lime"
          >
            {habits.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {habits.length === 0 ? (
        <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
          Create a habit to start tracking a streak
        </p>
      ) : isLoading || !matrix ? (
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">
          &gt;&gt; loading matrix...
        </p>
      ) : (
        <div className="overflow-x-auto">
          <div className="grid w-max grid-cols-[repeat(30,minmax(24px,1fr))] gap-1.5">
            {matrix.cells.map((cell, index) => (
              <button
                key={cell.date}
                ref={(el) => {
                  cellRefs.current[index] = el;
                }}
                type="button"
                tabIndex={index === 0 ? 0 : -1}
                onKeyDown={(e) => handleKeyDown(e, index)}
                title={formatCellLabel(cell.date, cell.count, matrix.cells.length, cell.status)}
                aria-label={formatCellLabel(
                  cell.date,
                  cell.count,
                  habits.find((h) => h.id === activeId)?.target_per_period ?? 1,
                  cell.status,
                )}
                className={`size-6 outline-none focus-visible:ring-2 focus-visible:ring-neon-lime focus-visible:ring-offset-2 focus-visible:ring-offset-surface-container ${STATUS_CLASSES[cell.status]}`}
              />
            ))}
          </div>
        </div>
      )}
    </NeonPanel>
  );
}
