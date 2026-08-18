import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface DataGridColumn<Row> {
  key: string;
  header: string;
  render: (row: Row) => ReactNode;
  className?: string;
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
}: {
  columns: DataGridColumn<Row>[];
  rows: Row[];
  emptyLabel?: string;
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
      <thead>
        <tr className="border-b border-outline-variant">
          {columns.map((col) => (
            <th
              key={col.key}
              className="px-3 py-2 font-mono text-label-mono text-on-surface-variant uppercase"
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
              <td key={col.key} className={cn("px-3 py-2 font-body text-body-md", col.className)}>
                {col.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
