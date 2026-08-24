import { useCallback, useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { usePrefersReducedMotion } from "@/lib/usePrefersReducedMotion";

export interface SvgViewport {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface CameraTarget {
  x: number;
  y: number;
  scale: number;
}

export const MIN_SCALE = 0.5;
export const MAX_SCALE = 2.5;
const WHEEL_ZOOM_FACTOR = 1.1;
const BUTTON_ZOOM_FACTOR = 1.25;
const ANIMATE_DEFAULT_DURATION_MS = 900;
// Below this, a requested camera move has nowhere meaningful to go — apply
// directly rather than scheduling 900ms of frames for an imperceptible move.
const NOOP_FOCUS_EPSILON = 2;
const NOOP_SCALE_EPSILON = 0.01;
// A pointerdown that never moves past this many CSS px is a tap/click, not a
// drag — captured pointer must stay uncaptured until we're sure, otherwise a
// plain click on a node (which needs its own click handler to fire normally)
// gets swallowed by the capture. Chromium retargets the synthesized `click`
// event away from the original element once `setPointerCapture` has fired
// for that pointer, even for a zero-movement tap.
const DRAG_THRESHOLD_PX = 4;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
}

/**
 * The pan that puts user-space point `(px, py)` at the viewport centre,
 * given `viewBox = (base.x + pan.x, base.y + pan.y, base.width / s, base.height / s)`.
 * Exported standalone so `cameraTarget.ts` and tests can use it without the hook.
 */
export function panForCenter(base: SvgViewport, px: number, py: number, scale: number) {
  return {
    x: px - base.x - base.width / (2 * scale),
    y: py - base.y - base.height / (2 * scale),
  };
}

/**
 * Local pan/zoom controller for an inline SVG — no new dependency (per the
 * plan §6.11). Pan is expressed as an offset into `baseViewport`'s
 * coordinate space; zoom shrinks/grows the visible `viewBox` around a fixed
 * scale factor. `viewBoxAttr` is the ready-to-spread `viewBox` string.
 */
export function useSvgPanZoom(
  baseViewport: SvgViewport,
  opts?: { minScale?: number; maxScale?: number },
) {
  const minScale = opts?.minScale ?? MIN_SCALE;
  const maxScale = opts?.maxScale ?? MAX_SCALE;
  const prefersReducedMotion = usePrefersReducedMotion();

  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragState = useRef<{
    pointerId: number;
    startClientX: number;
    startClientY: number;
    startPanX: number;
    startPanY: number;
    captured: boolean;
  } | null>(null);
  const animationRef = useRef<number | null>(null);

  const viewWidth = baseViewport.width / scale;
  const viewHeight = baseViewport.height / scale;
  const viewBoxAttr = `${baseViewport.x + pan.x} ${baseViewport.y + pan.y} ${viewWidth} ${viewHeight}`;

  const cancelAnimation = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);

  useEffect(() => cancelAnimation, [cancelAnimation]);

  const zoomBy = useCallback(
    (factor: number) => {
      cancelAnimation();
      const next = clamp(scale * factor, minScale, maxScale);
      if (next === scale) return;
      setPan((p) => ({
        x: p.x + (baseViewport.width / 2) * (1 / scale - 1 / next),
        y: p.y + (baseViewport.height / 2) * (1 / scale - 1 / next),
      }));
      setScale(next);
    },
    [scale, minScale, maxScale, baseViewport.width, baseViewport.height, cancelAnimation],
  );

  const zoomIn = useCallback(() => zoomBy(BUTTON_ZOOM_FACTOR), [zoomBy]);
  const zoomOut = useCallback(() => zoomBy(1 / BUTTON_ZOOM_FACTOR), [zoomBy]);
  const reset = useCallback(() => {
    cancelAnimation();
    setScale(1);
    setPan({ x: 0, y: 0 });
  }, [cancelAnimation]);

  // Current focal point (the user-space point currently at viewport centre),
  // derived fresh each call via refs so `animateTo` always starts from the
  // live state without needing scale/pan in its own dependency array.
  const scaleRef = useRef(scale);
  scaleRef.current = scale;
  const panRef = useRef(pan);
  panRef.current = pan;

  const animateTo = useCallback(
    (target: CameraTarget, animOpts?: { durationMs?: number }) => {
      cancelAnimation();
      const durationMs = animOpts?.durationMs ?? ANIMATE_DEFAULT_DURATION_MS;

      const startScale = scaleRef.current;
      const startFocusX = baseViewport.x + panRef.current.x + baseViewport.width / (2 * startScale);
      const startFocusY =
        baseViewport.y + panRef.current.y + baseViewport.height / (2 * startScale);

      const targetScale = clamp(target.scale, minScale, maxScale);

      const applyFinal = () => {
        setScale(targetScale);
        setPan(panForCenter(baseViewport, target.x, target.y, targetScale));
      };

      if (prefersReducedMotion) {
        applyFinal();
        return;
      }

      const focusDelta = Math.hypot(target.x - startFocusX, target.y - startFocusY);
      const scaleDelta = Math.abs(targetScale - startScale);
      if (focusDelta < NOOP_FOCUS_EPSILON && scaleDelta < NOOP_SCALE_EPSILON) {
        applyFinal();
        return;
      }

      const startTime = performance.now();
      const step = (now: number) => {
        const t = Math.min(1, (now - startTime) / durationMs);
        const eased = easeInOutCubic(t);
        const fx = startFocusX + (target.x - startFocusX) * eased;
        const fy = startFocusY + (target.y - startFocusY) * eased;
        const s = startScale + (targetScale - startScale) * eased;
        setScale(s);
        setPan(panForCenter(baseViewport, fx, fy, s));
        if (t < 1) {
          animationRef.current = requestAnimationFrame(step);
        } else {
          animationRef.current = null;
        }
      };
      animationRef.current = requestAnimationFrame(step);
    },
    [baseViewport, minScale, maxScale, cancelAnimation, prefersReducedMotion],
  );

  const fitAll = useCallback(() => {
    const centerX = baseViewport.x + baseViewport.width / 2;
    const centerY = baseViewport.y + baseViewport.height / 2;
    animateTo({ x: centerX, y: centerY, scale: minScale });
  }, [animateTo, baseViewport, minScale]);

  // React attaches its synthetic `onWheel` handler at the root as a
  // *passive* listener, so `event.preventDefault()` inside a normal JSX
  // `onWheel` prop is silently ignored (Chrome logs "Unable to
  // preventDefault inside passive event listener invocation") and the page
  // scrolls out from under the zoom gesture. Attaching a real, non-passive
  // `wheel` listener directly to the SVG DOM node — via this callback ref —
  // is the documented way around it.
  const zoomByRef = useRef(zoomBy);
  zoomByRef.current = zoomBy;
  const attachedElRef = useRef<SVGSVGElement | null>(null);
  const wheelHandlerRef = useRef((e: WheelEvent) => {
    e.preventDefault();
    zoomByRef.current(e.deltaY < 0 ? WHEEL_ZOOM_FACTOR : 1 / WHEEL_ZOOM_FACTOR);
  });

  const svgRef = useCallback((node: SVGSVGElement | null) => {
    if (attachedElRef.current) {
      attachedElRef.current.removeEventListener("wheel", wheelHandlerRef.current);
    }
    attachedElRef.current = node;
    if (node) {
      node.addEventListener("wheel", wheelHandlerRef.current, { passive: false });
    }
  }, []);

  const onPointerDown = useCallback(
    (e: ReactPointerEvent<SVGSVGElement>) => {
      cancelAnimation();
      // Deliberately does NOT call setPointerCapture here — see
      // DRAG_THRESHOLD_PX's comment. Capture happens lazily in
      // `onPointerMove`, only once real dragging is confirmed.
      dragState.current = {
        pointerId: e.pointerId,
        startClientX: e.clientX,
        startClientY: e.clientY,
        startPanX: pan.x,
        startPanY: pan.y,
        captured: false,
      };
    },
    [pan.x, pan.y, cancelAnimation],
  );

  const onPointerMove = useCallback(
    (e: ReactPointerEvent<SVGSVGElement>) => {
      const drag = dragState.current;
      if (!drag || drag.pointerId !== e.pointerId) return;
      const rect = e.currentTarget.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;

      const movedX = e.clientX - drag.startClientX;
      const movedY = e.clientY - drag.startClientY;
      if (!drag.captured) {
        if (Math.abs(movedX) < DRAG_THRESHOLD_PX && Math.abs(movedY) < DRAG_THRESHOLD_PX) {
          return;
        }
        e.currentTarget.setPointerCapture(e.pointerId);
        drag.captured = true;
      }

      const unitsPerPxX = viewWidth / rect.width;
      const unitsPerPxY = viewHeight / rect.height;
      const dx = movedX * unitsPerPxX;
      const dy = movedY * unitsPerPxY;
      setPan({ x: drag.startPanX - dx, y: drag.startPanY - dy });
    },
    [viewWidth, viewHeight],
  );

  const onPointerUp = useCallback((e: ReactPointerEvent<SVGSVGElement>) => {
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    dragState.current = null;
  }, []);

  return {
    scale,
    viewBoxAttr,
    zoomIn,
    zoomOut,
    reset,
    animateTo,
    fitAll,
    cancelAnimation,
    svgRef,
    onPointerDown,
    onPointerMove,
    onPointerUp,
  };
}
