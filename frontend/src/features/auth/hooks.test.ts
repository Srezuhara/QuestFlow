import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/apiClient";
import { authErrorMessage } from "./hooks";

describe("authErrorMessage", () => {
  it("uses the server detail for a 409 conflict", () => {
    const error = new ApiError(409, { detail: "Handle already taken" });
    expect(authErrorMessage(error)).toBe("Handle already taken");
  });

  it("falls back to a generic conflict message when detail is missing", () => {
    const error = new ApiError(409, {});
    expect(authErrorMessage(error)).toBe("That email or handle is already taken.");
  });

  it("reports invalid credentials for a 401", () => {
    const error = new ApiError(401, {});
    expect(authErrorMessage(error)).toBe("Invalid email or password.");
  });

  it("reports a validation message for a 422", () => {
    const error = new ApiError(422, {});
    expect(authErrorMessage(error)).toBe("Please check the form for errors.");
  });

  it("falls back to a generic message for non-ApiError values", () => {
    expect(authErrorMessage(new Error("network down"))).toBe(
      "Something went wrong. Please try again.",
    );
  });
});
