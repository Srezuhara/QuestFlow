import { icons, HelpCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * The backend stores icon names as kebab-case lucide identifiers (e.g.
 * `"brain-circuit"`, seeded by the skill-node/achievement catalog
 * migrations) — `lucide-react`'s `icons` lookup map is keyed by PascalCase
 * (`BrainCircuit`). Converts and falls back to a generic icon for any name
 * that doesn't resolve, so a catalog typo degrades gracefully instead of
 * crashing the tree/wall render.
 */
export function lucideByName(kebabName: string): LucideIcon {
  const pascal = kebabName
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
  return icons[pascal as keyof typeof icons] ?? HelpCircle;
}
