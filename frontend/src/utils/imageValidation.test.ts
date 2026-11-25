import { describe, expect, it } from "vitest";
import { ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE_BYTES, MAX_IMAGE_SIZE_MB, validateProfileImage } from "./validation";

const MB = 1024 * 1024;

// A real File of exactly `size` bytes (jsdom computes .size from the content).
function image(size: number, type = "image/png", name = "photo.png"): File {
  return new File([new Uint8Array(size)], name, { type });
}

describe("profile picture size limit", () => {
  it("is 10 MB = 10 x 1024 x 1024 bytes", () => {
    expect(MAX_IMAGE_SIZE_MB).toBe(10);
    expect(MAX_IMAGE_SIZE_BYTES).toBe(10 * 1024 * 1024);
    expect(MAX_IMAGE_SIZE_BYTES).toBe(10_485_760);
  });

  it("accepts an image smaller than 10 MB", () => {
    expect(validateProfileImage(image(3 * MB))).toBeUndefined();
    expect(validateProfileImage(image(MAX_IMAGE_SIZE_BYTES - 1))).toBeUndefined();
  });

  it("accepts an image exactly at the 10 MB limit", () => {
    const exactly = image(MAX_IMAGE_SIZE_BYTES);
    expect(exactly.size).toBe(10_485_760);
    expect(validateProfileImage(exactly)).toBeUndefined();
  });

  it("rejects an image larger than 10 MB, with a message naming the limit", () => {
    expect(validateProfileImage(image(MAX_IMAGE_SIZE_BYTES + 1))).toBe("Profile picture must be 10 MB or smaller.");
    expect(validateProfileImage(image(12 * MB))).toBe("Profile picture must be 10 MB or smaller.");
  });

  it("accepts sizes between the old 2 MB and the new 10 MB limit", () => {
    expect(validateProfileImage(image(2 * MB + 1))).toBeUndefined();
    expect(validateProfileImage(image(9 * MB))).toBeUndefined();
  });
});

describe("other image rules are unchanged", () => {
  it("still allows exactly JPG/JPEG, PNG and WebP", () => {
    expect(ALLOWED_IMAGE_TYPES).toEqual(["image/jpeg", "image/png", "image/webp"]);
    for (const type of ALLOWED_IMAGE_TYPES) {
      expect(validateProfileImage(image(1024, type))).toBeUndefined();
    }
  });

  it("still rejects other formats, even when small", () => {
    for (const type of ["image/gif", "image/svg+xml", "application/pdf", ""]) {
      expect(validateProfileImage(image(1024, type, "file"))).toBe("Profile picture must be a JPG, JPEG, PNG, or WebP image.");
    }
  });

  it("checks the format before the size, and still rejects empty files", () => {
    expect(validateProfileImage(image(12 * MB, "image/gif"))).toMatch(/JPG, JPEG, PNG, or WebP/);
    expect(validateProfileImage(image(0))).toBe("Profile picture file is empty.");
  });
});
