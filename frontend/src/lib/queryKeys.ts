/**
 * Centralized TanStack Query key factory — every feature adds its own key
 * namespace here as it lands.
 */
export const queryKeys = {
  tasks: {
    all: ["tasks"] as const,
  },
  projects: {
    all: ["projects"] as const,
  },
  tags: {
    all: ["tags"] as const,
  },
  progress: {
    me: ["progress", "me"] as const,
    xpEvents: ["progress", "xp-events"] as const,
  },
  dashboard: {
    root: ["dashboard"] as const,
  },
  habits: {
    all: ["habits"] as const,
    matrix: (habitId: string) => ["habits", habitId, "matrix"] as const,
  },
  focus: {
    sessions: ["focus", "sessions"] as const,
    active: ["focus", "active"] as const,
    calendar: (year: number, month: number) => ["focus", "calendar", year, month] as const,
  },
  preferences: ["preferences"] as const,
  notes: {
    all: ["notes"] as const,
    list: (q: string, tags: string[]) => ["notes", "list", q, tags] as const,
    detail: (id: string) => ["notes", id] as const,
  },
  skillTree: {
    me: ["skill-tree"] as const,
  },
  achievements: {
    all: ["achievements"] as const,
  },
  xp: {
    // A single key for the whole paginated ledger — TanStack Query's
    // `useInfiniteQuery` caches all fetched pages under one key and threads
    // the cursor through `pageParam`, not through the key itself.
    history: ["xp", "history"] as const,
    summary: (days: number) => ["xp", "summary", days] as const,
  },
  reminders: {
    all: ["reminders"] as const,
    list: (status: string | undefined) => ["reminders", "list", status ?? "all"] as const,
  },
  push: {
    subscriptions: ["push", "subscriptions"] as const,
    publicKey: ["push", "public-key"] as const,
  },
  notifications: {
    all: ["notifications"] as const,
  },
  social: {
    leaderboard: (limit: number, offset: number) =>
      ["social", "leaderboard", limit, offset] as const,
    feed: ["social", "feed"] as const,
  },
} as const;
