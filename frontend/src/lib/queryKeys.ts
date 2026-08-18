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
} as const;
