import type { ElementType, ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * 45° clipped-corner container — DESIGN.md "Shapes". Wraps the shared
 * `clip-chamfer` utility (defined once in tokens.css) so every sharp-edged
 * surface in the app clips identically.
 */
export function ChamferBox({
  as: Component = "div",
  className,
  children,
  ...rest
}: {
  as?: ElementType;
  className?: string;
  children?: ReactNode;
  [key: string]: unknown;
}) {
  return (
    <Component className={cn("clip-chamfer", className)} {...rest}>
      {children}
    </Component>
  );
}
