import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/cn";

/**
 * Icon wrapper applying the "on-state" emissive glow from DESIGN.md Colors
 * (a soft drop-shadow tinted with the icon's own color) when `active`.
 */
export function GlowIcon({
  icon: Icon,
  active = false,
  size = 18,
  className,
}: {
  icon: LucideIcon;
  active?: boolean;
  size?: number;
  className?: string;
}) {
  return (
    <Icon
      size={size}
      className={cn(
        "shrink-0",
        active
          ? "text-neon-lime drop-shadow-[0_0_6px_rgba(195,244,0,0.7)]"
          : "text-on-surface-variant",
        className,
      )}
    />
  );
}
