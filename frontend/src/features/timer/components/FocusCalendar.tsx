import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { NeonPanel } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { FocusDaySummaryOut } from "../api";

const WEEKDAY_LABELS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

function todayIsoDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function intensityClass(focusSeconds: number, maxSeconds: number): string {
  if (focusSeconds <= 0) return "bg-surface-container-high";
  const ratio = maxSeconds > 0 ? focusSeconds / maxSeconds : 0;
  if (ratio > 0.66) return "bg-neon-lime/70";
  if (ratio > 0.33) return "bg-neon-lime/40";
  return "bg-neon-lime/20";
}

export function FocusCalendar({
  year,
  month,
  days,
  isLoading,
  selectedDate,
  onSelectDate,
  onPrevMonth,
  onNextMonth,
}: {
  year: number;
  month: number;
  days: FocusDaySummaryOut[] | undefined;
  isLoading: boolean;
  selectedDate: string;
  onSelectDate: (date: string) => void;
  onPrevMonth: () => void;
  onNextMonth: () => void;
}) {
  const cellRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const firstOfMonth = new Date(year, month - 1, 1);
  const leadingBlanks = firstOfMonth.getDay();
  const maxFocusSeconds = Math.max(0, ...(days ?? []).map((d) => d.focus_seconds));
  const today = todayIsoDate();
  const monthLabel = firstOfMonth.toLocaleDateString(undefined, { month: "long", year: "numeric" });

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
      <div className="mb-6 flex items-center justify-between border-b border-surface-container-highest pb-4">
        <h2 className="font-display text-title-md text-on-surface uppercase">Focus Calendar</h2>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onPrevMonth}
            aria-label="Previous month"
            className="text-on-surface-variant hover:text-neon-lime"
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
          <span className="w-36 text-center font-mono text-label-mono text-on-surface uppercase">
            {monthLabel}
          </span>
          <button
            type="button"
            onClick={onNextMonth}
            aria-label="Next month"
            className="text-on-surface-variant hover:text-neon-lime"
          >
            <ChevronRight size={18} aria-hidden="true" />
          </button>
        </div>
      </div>

      {isLoading || !days ? (
        <p className="font-mono text-label-mono text-on-surface-variant uppercase">
          &gt;&gt; loading calendar...
        </p>
      ) : (
        <div className="overflow-x-auto">
          <div className="grid min-w-[420px] grid-cols-7 gap-2">
            {WEEKDAY_LABELS.map((label) => (
              <span
                key={label}
                className="text-center font-mono text-label-mono text-on-surface-variant"
              >
                {label}
              </span>
            ))}

            {Array.from({ length: leadingBlanks }).map((_, i) => (
              <span key={`blank-${i}`} aria-hidden="true" />
            ))}

            {days.map((day, index) => {
              const isToday = day.date === today;
              const isSelected = day.date === selectedDate;
              const dayNumber = Number(day.date.slice(-2));
              return (
                <button
                  key={day.date}
                  ref={(el) => {
                    cellRefs.current[index] = el;
                  }}
                  type="button"
                  tabIndex={day.date === selectedDate ? 0 : -1}
                  onClick={() => onSelectDate(day.date)}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  aria-label={`${day.date} — ${day.session_count} session${day.session_count === 1 ? "" : "s"}, ${Math.round(day.focus_seconds / 60)} minutes`}
                  aria-current={isToday ? "date" : undefined}
                  className={cn(
                    "flex aspect-square min-w-9 flex-col items-center justify-center gap-0.5 outline-none focus-visible:ring-2 focus-visible:ring-neon-lime focus-visible:ring-offset-2 focus-visible:ring-offset-surface-container",
                    intensityClass(day.focus_seconds, maxFocusSeconds),
                    isToday && "ring-1 ring-neon-lime",
                    isSelected && "outline outline-2 outline-neon-pink",
                  )}
                >
                  <span className="font-mono text-label-mono text-on-surface">{dayNumber}</span>
                  {day.session_count > 0 && (
                    <span className="size-1 rounded-full bg-neon-pink" aria-hidden="true" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </NeonPanel>
  );
}
