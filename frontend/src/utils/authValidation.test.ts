import { describe, expect, it } from "vitest";
import { checkEmail, checkFullName, checkPassword } from "./authValidation";

describe("authValidation", () => {
  it("requires 8+ characters with a letter and a number", () => {
    expect(checkPassword("short1")).toMatch(/at least 8/);
    expect(checkPassword("onlyletters")).toMatch(/letter and one number/);
    expect(checkPassword("12345678")).toMatch(/letter and one number/);
    expect(checkPassword("goodPass123")).toBeUndefined();
  });

  it("rejects a password equal to the email", () => {
    expect(checkPassword("me1@x.io", "ME1@x.io")).toMatch(/email/);
  });

  it("checks email and name", () => {
    expect(checkEmail("")).toMatch(/required/);
    expect(checkEmail("not-an-email")).toMatch(/valid/);
    expect(checkEmail("a@b.co")).toBeUndefined();
    expect(checkFullName("A")).toMatch(/at least 2/);
    expect(checkFullName("Ada Lovelace")).toBeUndefined();
  });
});
