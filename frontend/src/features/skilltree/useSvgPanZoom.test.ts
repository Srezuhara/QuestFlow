import { act, renderHook } from "@testing-library/react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSvgPanZoom } from "./useSvgPanZoom";

const BASE_VIEWPORT = { x: -200, y: -200, width: 400, height: 400 };
const CLAMP_OPTS = { minScale: 0.5, maxScale: 2.5 };

// The hook attaches its wheel listener imperatively (via `svgRef`, not a
// JSX `onWheel` prop — see the hook's own comment on why), so the test
// exercises it the same way the real DOM would: attach the ref to a real
// SVG element, then dispatch a real `wheel` event at it.
function wheel(svgRef: (node: SVGSVGElement | null) => void, deltaY: number) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  document.body.appendChild(svg);
  svgRef(svg);
  svg.dispatchEvent(new WheelEvent("wheel", { deltaY, bubbles: true, cancelable: true }));
  svgRef(null);
  svg.remove();
}

function parseViewBox(viewBoxAttr: string) {
  const [x, y, width, height] = viewBoxAttr.split(" ").map(Number);
  return { x, y, width, height };
}

function viewBoxCenter(viewBoxAttr: string) {
  const { x, y, width, height } = parseViewBox(viewBoxAttr);
  return { x: x + width / 2, y: y + height / 2 };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("useSvgPanZoom", () => {
  it("zooms in on negative wheel delta and out on positive", () => {
    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT, CLAMP_OPTS));

    act(() => wheel(result.current.svgRef, -100));
    expect(result.current.scale).toBeGreaterThan(1);

    const afterZoomIn = result.current.scale;
    act(() => wheel(result.current.svgRef, 100));
    expect(result.current.scale).toBeLessThan(afterZoomIn);
  });

  it("clamps zoom at the maximum scale", () => {
    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT, CLAMP_OPTS));

    for (let i = 0; i < 50; i++) {
      act(() => wheel(result.current.svgRef, -100));
    }
    expect(result.current.scale).toBeLessThanOrEqual(CLAMP_OPTS.maxScale);
    expect(result.current.scale).toBeCloseTo(CLAMP_OPTS.maxScale, 5);
  });

  it("clamps zoom at the minimum scale", () => {
    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT, CLAMP_OPTS));

    for (let i = 0; i < 50; i++) {
      act(() => wheel(result.current.svgRef, 100));
    }
    expect(result.current.scale).toBeGreaterThanOrEqual(CLAMP_OPTS.minScale);
    expect(result.current.scale).toBeCloseTo(CLAMP_OPTS.minScale, 5);
  });

  it("reset restores scale to 1", () => {
    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT));

    act(() => result.current.zoomIn());
    expect(result.current.scale).not.toBe(1);

    act(() => result.current.reset());
    expect(result.current.scale).toBe(1);
  });

  it("zoom is centre-anchored: the viewBox centre is unchanged across a zoom-in (DA-3)", () => {
    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT));

    const before = viewBoxCenter(result.current.viewBoxAttr);
    act(() => result.current.zoomIn());
    const after = viewBoxCenter(result.current.viewBoxAttr);

    expect(after.x).toBeCloseTo(before.x, 5);
    expect(after.y).toBeCloseTo(before.y, 5);
  });

  it("animateTo reaches the target synchronously with no rAF scheduled when reduced motion is preferred", () => {
    vi.stubGlobal("matchMedia", (media: string) => ({
      matches: true,
      media,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }));
    const rafSpy = vi.spyOn(window, "requestAnimationFrame");

    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT));

    act(() => result.current.animateTo({ x: 150, y: -80, scale: 1.5 }));

    expect(rafSpy).not.toHaveBeenCalled();
    expect(result.current.scale).toBeCloseTo(1.5, 5);
    const center = viewBoxCenter(result.current.viewBoxAttr);
    expect(center.x).toBeCloseTo(150, 5);
    expect(center.y).toBeCloseTo(-80, 5);
  });

  it("onPointerDown cancels an in-flight animation", () => {
    const rafSpy = vi.spyOn(window, "requestAnimationFrame").mockReturnValue(1);
    const cancelSpy = vi.spyOn(window, "cancelAnimationFrame");

    const { result } = renderHook(() => useSvgPanZoom(BASE_VIEWPORT));

    act(() => result.current.animateTo({ x: 150, y: -80, scale: 1.5 }));
    expect(rafSpy).toHaveBeenCalled();

    act(() => {
      result.current.onPointerDown({
        pointerId: 1,
        clientX: 0,
        clientY: 0,
      } as unknown as ReactPointerEvent<SVGSVGElement>);
    });

    expect(cancelSpy).toHaveBeenCalled();
  });
});
