import { describe, expect, it } from "vitest";
import { ApiError, isAccountSuspended, toQuery } from "./apiClient";

describe("apiClient helpers", () => {
  it("recognises only tagged 403 responses as a suspended account", () => {
    expect(isAccountSuspended(new ApiError("Suspended", 403, "account_suspended"))).toBe(true);
    expect(isAccountSuspended(new ApiError("No permission", 403, null))).toBe(false);
    expect(isAccountSuspended(new ApiError("Expired", 401, "account_suspended"))).toBe(false);
    expect(isAccountSuspended(new Error("other"))).toBe(false);
  });

  it("builds query strings without empty values", () => {
    expect(toQuery({ q: "sam", role: "", page: 2, status: null })).toBe("?q=sam&page=2");
    expect(toQuery({})).toBe("");
  });
});
