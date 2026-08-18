import { act, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";
import { RequireAuth } from "./RequireAuth";
import { useAuthStore } from "./store";

function renderGuarded() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/login" element={<p>login screen</p>} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <p>protected content</p>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  act(() => useAuthStore.setState({ user: null, status: "pending" }));
});

describe("RequireAuth", () => {
  it("renders nothing while the bootstrap check is pending", () => {
    act(() => useAuthStore.setState({ status: "pending" }));
    renderGuarded();
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
    expect(screen.queryByText("login screen")).not.toBeInTheDocument();
  });

  it("redirects to /login once unauthenticated", () => {
    act(() => useAuthStore.setState({ status: "unauthenticated" }));
    renderGuarded();
    expect(screen.getByText("login screen")).toBeInTheDocument();
  });

  it("renders the protected content once authenticated", () => {
    act(() => useAuthStore.setState({ status: "authenticated" }));
    renderGuarded();
    expect(screen.getByText("protected content")).toBeInTheDocument();
  });
});
