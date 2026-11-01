import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TutorForm from "../components/TutorForm";
import { uploadProfileImage } from "../services/imageService";
import { createTutor } from "../services/tutorService";
import type { TutorFormData } from "../types/tutor";
import { getErrorMessage } from "../utils/messages";

function CreateTutorPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Called by TutorForm only after the form passed validation.
  async function handleSubmit(data: TutorFormData, imageFile: File | null) {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // A newly chosen picture is uploaded first; its address is then saved with
      // the profile. Without a new picture, the existing address (if any) is kept.
      // Image upload is not connected yet, so the form does not allow a new
      // picture to reach this point until imageService is completed.
      const profileImageUrl =
        imageFile === null ? data.profile_image_url : await uploadProfileImage(imageFile);

      const createdTutor = await createTutor({
        ...data,
        profile_image_url: profileImageUrl,
      });

      navigate(`/tutors/${encodeURIComponent(String(createdTutor.id))}`, {
        state: { successMessage: "Tutor profile created successfully." },
      });
    } catch (error) {
      setSubmitError(getErrorMessage(error));
      setIsSubmitting(false);
      // Bring the error message (at the top of the form) into view.
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  return (
    <main className="container page form-page">
      <h1>Create Tutor Profile</h1>
      <p className="page-intro">
        Fill in your details to create a tutor profile. Fields marked with * are
        required.
      </p>

      <TutorForm
        submitLabel="Create profile"
        isSubmitting={isSubmitting}
        submitError={submitError}
        cancelTo="/tutors"
        onSubmit={handleSubmit}
      />
    </main>
  );
}

export default CreateTutorPage;