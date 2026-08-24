import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

function stubMatchMedia(initialMatches: boolean) {
  let changeHandler: (() => void) | null = null;
  const mql = {
    matches: initialMatches,
    media: "(prefers-reduced-motion: reduce)",
    onchange: null,
    addEventListener: (_: string, handler: () => void) => {
      changeHandler = handler;
    },
    removeEventListener: () => {
      changeHandler = null;
    },
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  };
  vi.stubGlobal("matchMedia", () => mql);
  return {
    fireChange: (matches: boolean) => {
      mql.matches = matches;
      changeHandler?.();
    },
  };
}

describe("usePrefersReducedMotion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reads the initial matchMedia state", () => {
    stubMatchMedia(true);
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(true);
  });

  it("defaults to false when matchMedia reports no match", () => {
    stubMatchMedia(false);
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(false);
  });

  it("updates live when the OS setting changes", () => {
    const { fireChange } = stubMatchMedia(false);
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(false);

    act(() => fireChange(true));
    expect(result.current).toBe(true);
  });
});
