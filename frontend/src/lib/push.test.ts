import { afterEach, describe, expect, it, vi } from "vitest";
import { enablePush, getPermissionState, urlBase64ToUint8Array } from "./push";

describe("urlBase64ToUint8Array", () => {
  it("round-trips a URL-safe base64 string back to its original bytes", () => {
    const original = new Uint8Array([0, 1, 2, 253, 254, 255, 16, 32, 64, 128]);
    const base64 = btoa(String.fromCharCode(...original))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

    const roundTripped = urlBase64ToUint8Array(base64);
    expect(Array.from(roundTripped)).toEqual(Array.from(original));
  });
});

describe("getPermissionState", () => {
  it("reports unsupported when Notification does not exist", () => {
    const original = globalThis.Notification;
    // @ts-expect-error - simulating an environment without the Notification API
    delete globalThis.Notification;
    expect(getPermissionState()).toBe("unsupported");
    globalThis.Notification = original;
  });
});

describe("enablePush", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("no-ops (returns null) when permission is denied", async () => {
    vi.stubGlobal("Notification", {
      permission: "denied",
      requestPermission: vi.fn().mockResolvedValue("denied"),
    });
    vi.stubGlobal("navigator", {
      ...navigator,
      serviceWorker: { ready: Promise.resolve({ pushManager: {} }) },
    });
    vi.stubGlobal("PushManager", class {});

    const result = await enablePush();
    expect(result).toBeNull();
  });
});
