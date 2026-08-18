import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";

const VARIANT_CLASSES: Record<Variant, string> = {
  // Solid cyber-lime, black text, lime glow on hover — DESIGN.md "Buttons: Primary".
  primary: "bg-neon-lime text-neon-black hover:shadow-[0_0_16px_rgba(195,244,0,0.6)]",
  // Transparent, hot-pink border + text — DESIGN.md "Buttons: Secondary".
  secondary: "border border-neon-pink text-neon-pink hover:shadow-[0_0_12px_rgba(254,0,254,0.5)]",
  // JetBrains Mono text with ">>" prefix, no fill — DESIGN.md "Buttons: Ghost".
  ghost: "text-on-surface-variant hover:text-neon-lime",
};

export function NeonButton({
  variant = "primary",
  className,
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; children?: ReactNode }) {
  return (
    <button
      className={cn(
        "clip-chamfer inline-flex items-center justify-center gap-2 px-5 py-2.5",
        "font-mono text-label-mono uppercase transition-shadow duration-150",
        "disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:shadow-none",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...rest}
    >
      {variant === "ghost" && <span aria-hidden="true">&gt;&gt;</span>}
      {children}
    </button>
  );
}
