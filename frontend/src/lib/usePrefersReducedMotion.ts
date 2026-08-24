import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

function read(): boolean {
  return typeof window.matchMedia === "function" ? window.matchMedia(QUERY).matches : false;
}

/**
 * Live `prefers-reduced-motion` state — subscribes to OS-level changes
 * rather than reading once at mount, so toggling it while the app is open
 * takes effect immediately. The global CSS rule in `tokens.css:154` only
 * reaches CSS transitions/animations; this hook is for the codebase's
 * JS-driven motion (rAF loops), which that rule cannot touch.
 */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(read);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mql = window.matchMedia(QUERY);
    const onChange = () => setReduced(mql.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return reduced;
}
