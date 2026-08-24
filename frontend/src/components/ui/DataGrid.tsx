import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

const HIDE_BELOW_CLASSES: Record<NonNullable<DataGridColumn<never>["hideBelow"]>, string> = {
  sm: "hidden sm:table-cell",
  md: "hidden md:table-cell",
};

export interface DataGridColumn<Row> {
  key: string;
  header: string;
  render: (row: Row) => ReactNode;
  className?: string;
  /** Column is hidden below this breakpoint (column-drop, not horizontal
   * scroll — see PHASE_8_9_PLAN.md §9.3.1). Applied to both `<th>` and `<td>`. */
  hideBelow?: "sm" | "md";
}

/**
 * Minimal typed table primitive for tabular screens (leaderboard, XP
 * history, task lists in later phases). Sharp borders, mono headers, no
 * built-in sorting/pagination — those are added per-screen as needed.
 */
export function DataGrid<Row extends { id: string }>({
  columns,
  rows,
  emptyLabel = "No data",
  caption,
}: {
  columns: DataGridColumn<Row>[];
  rows: Row[];
  emptyLabel?: string;
  /** Visually hidden (`sr-only`) — required on every call site so screen
   * reader users know what the table is, per PHASE_8_9_PLAN.md §9.2 item 1. */
  caption: string;
}) {
  if (rows.length === 0) {
    return (
      <p className="border border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
        {emptyLabel}
      </p>
    );
  }

  return (
    <table className="w-full border-collapse text-left">
      <caption className="sr-only">{caption}</caption>
      <thead>
        <tr className="border-b border-outline-variant">
          {columns.map((col) => (
            <th
              key={col.key}
              scope="col"
              className={cn(
                "px-3 py-2 font-mono text-label-mono text-on-surface-variant uppercase",
                col.hideBelow && HIDE_BELOW_CLASSES[col.hideBelow],
              )}
            >
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id} className="border-b border-outline-variant/40">
            {columns.map((col) => (
              <td
                key={col.key}
                className={cn(
                  "px-3 py-2 font-body text-body-md",
                  col.hideBelow && HIDE_BELOW_CLASSES[col.hideBelow],
                  col.className,
                )}
              >
                {col.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
