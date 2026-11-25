import { describe, expect, it } from "vitest";
import { makeUser } from "../test/helpers";
import { buildMenu } from "./AppLayout";

const links = (user: ReturnType<typeof makeUser>) => buildMenu(user).flatMap((section) => section.items.map((i) => i.to));

describe("role-based sidebar menu", () => {
  it("shows administration links only to admins", () => {
    expect(links(makeUser({ role: "user" })).some((to) => to.startsWith("/admin"))).toBe(false);
    expect(links(makeUser({ role: "admin" }))).toEqual(
      expect.arrayContaining(["/admin", "/admin/users", "/admin/content", "/admin/audit", "/admin/security"])
    );
  });

  it("gives tutors their profile link and keeps an admin's personal dashboard", () => {
    expect(links(makeUser({ account_type: "tutor" }))).toContain("/tutor-profile");
    expect(links(makeUser({ account_type: "student" }))).not.toContain("/tutor-profile");
    expect(links(makeUser({ role: "admin", account_type: "tutor" }))).toContain("/dashboard/tutor");
  });
});
