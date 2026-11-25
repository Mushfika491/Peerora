import { describe, expect, it } from "vitest";
import { dashboardPath, personalDashboardPath, safeNextPath } from "./dashboardPath";

describe("dashboardPath", () => {
  it("sends students and tutors to their own dashboard", () => {
    expect(dashboardPath({ role: "user", account_type: "student" })).toBe("/dashboard/student");
    expect(dashboardPath({ role: "user", account_type: "tutor" })).toBe("/dashboard/tutor");
  });

  it("gives the admin dashboard priority over the account type", () => {
    expect(dashboardPath({ role: "admin", account_type: "student" })).toBe("/admin");
    expect(dashboardPath({ role: "admin", account_type: "tutor" })).toBe("/admin");
  });

  it("keeps the personal dashboard reachable for admins", () => {
    expect(personalDashboardPath({ account_type: "tutor" })).toBe("/dashboard/tutor");
  });

  it("accepts only internal paths as the post-login redirect", () => {
    expect(safeNextPath("/groups/3")).toBe("/groups/3");
    expect(safeNextPath("https://evil.example")).toBeNull();
    expect(safeNextPath("//evil.example")).toBeNull();
    expect(safeNextPath(null)).toBeNull();
  });
});
