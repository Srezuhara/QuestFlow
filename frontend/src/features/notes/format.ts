/** `09:42` for today, `YESTERDAY`, or `12 OCT` for anything older. */
export function formatShardTime(iso: string, now: Date = new Date()): string {
  const date = new Date(iso);
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const dayDiff = Math.round((startOfToday.getTime() - startOfDate.getTime()) / 86_400_000);

  if (dayDiff === 0) {
    return date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  if (dayDiff === 1) {
    return "YESTERDAY";
  }
  return date.toLocaleDateString(undefined, { day: "2-digit", month: "short" }).toUpperCase();
}
