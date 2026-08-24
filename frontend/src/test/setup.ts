import "@testing-library/jest-dom/vitest";

// Node 22+'s built-in (experimental) global `localStorage` shadows jsdom's
// real per-window implementation with a non-functional stub when no
// `--localstorage-file` path is configured (surfaces as "getItem is not a
// function"). Detect that and fall back to an in-memory Storage polyfill so
// tests can rely on window.localStorage regardless of the Node version
// running them.
if (typeof window.localStorage?.getItem !== "function") {
  const store = new Map<string, string>();
  const memoryStorage: Storage = {
    getItem: (key) => (store.has(key) ? (store.get(key) ?? null) : null),
    setItem: (key, value) => {
      store.set(key, String(value));
    },
    removeItem: (key) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
    key: (index) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size;
    },
  };
  Object.defineProperty(window, "localStorage", { value: memoryStorage, configurable: true });
}

// jsdom does not implement `matchMedia` — any code that checks
// `prefers-reduced-motion` (or any other media query) throws without this.
// Installed only when missing, mirroring the localStorage polyfill above.
if (typeof window.matchMedia !== "function") {
  window.matchMedia = (media: string): MediaQueryList =>
    ({
      matches: false,
      media,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList;
}
