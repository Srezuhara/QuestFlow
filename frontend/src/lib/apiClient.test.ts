import { describe, expect, it } from "vitest";
import { ApiError } from "./apiClient";

describe("ApiError", () => {
  it("extracts request_id from a problem+json body", () => {
    const error = new ApiError(404, { detail: "Not found", request_id: "abc-123" });
    expect(error.requestId).toBe("abc-123");
    expect(error.body).toEqual({ detail: "Not found", request_id: "abc-123" });
  });

  it("is null when the body has no request_id", () => {
    const error = new ApiError(422, { detail: [{ msg: "bad" }] });
    expect(error.requestId).toBeNull();
  });

  it("is null when the body is not an object", () => {
    const error = new ApiError(500, null);
    expect(error.requestId).toBeNull();
  });
});
