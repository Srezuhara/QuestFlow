import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import { ChamferBox } from "./ChamferBox";

/**
 * Base card/container surface — DESIGN.md "Cards & Containers": #121212-ish
 * surface-container background, 1px lime→yellow gradient border, chamfered
 * corners. `glow` adds the outer-glow treatment used for active/focused
 * panels instead of a drop shadow (per "Elevation & Depth").
 */
export function NeonPanel({
  className,
  children,
  glow = false,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { children?: ReactNode; glow?: boolean }) {
  return (
    <ChamferBox
      className={cn(
        "relative border border-transparent bg-surface-container p-6",
        "[background:linear-gradient(var(--color-surface-container),var(--color-surface-container))_padding-box,linear-gradient(135deg,var(--color-neon-lime),var(--color-neon-yellow))_border-box]",
        glow && "shadow-[0_0_16px_rgba(195,244,0,0.25)]",
        className,
      )}
      {...rest}
    >
      {children}
    </ChamferBox>
  );
}
