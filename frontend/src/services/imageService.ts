import { ApiError } from "./apiClient";
import { validateProfileImage } from "../utils/validation";

// Whether pictures can really be stored. This stays false until real Supabase
// Storage upload is implemented in uploadProfileImage below. While it is
// false, the form refuses to save a profile that has a picture selected.
export const IMAGE_UPLOAD_AVAILABLE: boolean = false;

export const IMAGE_UPLOAD_UNAVAILABLE_MESSAGE =
  "Image upload is not connected yet. Remove the image to save the profile without a picture.";

// Uploads a profile picture and returns its public address.
//
// FUTURE: Supabase Storage integration goes here. The rest of the application
// only needs this function to return the public URL of the stored image, so
// the upload route (directly from the browser, or through the FastAPI backend)
// can be chosen later without changing any page or component.
// When the real upload works, change IMAGE_UPLOAD_AVAILABLE to true.
export async function uploadProfileImage(file: File): Promise<string> {
  // The same format and size rules as the form, checked again before any upload.
  const validationMessage = validateProfileImage(file);
  if (validationMessage !== undefined) {
    throw new ApiError(validationMessage);
  }

  if (!IMAGE_UPLOAD_AVAILABLE) {
    throw new ApiError(IMAGE_UPLOAD_UNAVAILABLE_MESSAGE);
  }

  // Not reachable until the real upload is written above this line.
  throw new ApiError("Image upload has not been implemented.");
}