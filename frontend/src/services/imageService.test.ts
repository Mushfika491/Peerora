import { describe, expect, it } from "vitest";
import { MAX_IMAGE_SIZE_BYTES } from "../utils/validation";
import { IMAGE_UPLOAD_UNAVAILABLE_MESSAGE, uploadProfileImage } from "./imageService";

const file = (size: number) => new File([new Uint8Array(size)], "photo.webp", { type: "image/webp" });

describe("uploadProfileImage re-checks the size before any upload", () => {
  it("refuses a file over 10 MB with the size message", async () => {
    await expect(uploadProfileImage(file(MAX_IMAGE_SIZE_BYTES + 1))).rejects.toThrow("Profile picture must be 10 MB or smaller.");
  });

  it("lets a 10 MB file through the size check (upload itself is not connected yet)", async () => {
    await expect(uploadProfileImage(file(MAX_IMAGE_SIZE_BYTES))).rejects.toThrow(IMAGE_UPLOAD_UNAVAILABLE_MESSAGE);
  });
});
