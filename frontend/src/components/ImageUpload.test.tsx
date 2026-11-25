import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MAX_IMAGE_SIZE_BYTES } from "../utils/validation";
import ImageUpload from "./ImageUpload";

function renderUpload() {
  const onFileChange = vi.fn();
  render(
    <ImageUpload id="photo" label="Profile picture" file={null} existingUrl=""
      onFileChange={onFileChange} onRemoveExisting={() => {}} />
  );
  return onFileChange;
}

function choose(size: number) {
  const file = new File([new Uint8Array(size)], "photo.jpg", { type: "image/jpeg" });
  fireEvent.change(screen.getByLabelText("Profile picture"), { target: { files: [file] } });
  return file;
}

describe("ImageUpload with the 10 MB limit", () => {
  it("tells the user the limit is 10 MB", () => {
    renderUpload();
    expect(screen.getByText("JPG, JPEG, PNG or WebP. Maximum size 10 MB.")).toBeInTheDocument();
  });

  it("accepts a file exactly at the limit", () => {
    const onFileChange = renderUpload();
    const file = choose(MAX_IMAGE_SIZE_BYTES);
    expect(onFileChange).toHaveBeenCalledWith(file);
    expect(screen.queryByText(/must be 10 MB or smaller/)).not.toBeInTheDocument();
  });

  it("rejects a file over the limit and keeps the previous picture", () => {
    const onFileChange = renderUpload();
    choose(MAX_IMAGE_SIZE_BYTES + 1);
    expect(onFileChange).not.toHaveBeenCalled();
    expect(screen.getByText("Profile picture must be 10 MB or smaller.")).toBeInTheDocument();
  });
});
