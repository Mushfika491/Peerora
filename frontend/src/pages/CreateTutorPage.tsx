import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";
import TutorForm from "../components/TutorForm";
import { uploadProfileImage } from "../services/imageService";
import { createTutor } from "../services/tutorService";
import type { TutorFormData } from "../types/tutor";
import { getErrorMessage } from "../utils/messages";
import { EMPTY_TUTOR_FORM_VALUES } from "../utils/validation";

function CreateTutorPage() {
  const navigate = useNavigate();
  const { user, setUser } = useAuth();
  const toast = useToast();
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

      if (user !== null) {
        setUser({ ...user, has_tutor_profile: true });
      }
      toast.success("Tutor profile created successfully.");
      navigate(`/tutors/${createdTutor.id}`);
    } catch (error) {
      setSubmitError(getErrorMessage(error));
      setIsSubmitting(false);
      // Bring the error message (at the top of the form) into view.
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  // One profile per tutor account: send tutors who already have one to it.
  if (user?.has_tutor_profile && !isSubmitting) {
    return <Navigate to="/tutor-profile" replace />;
  }

  return (
    <div className="form-page">
      <h1>Create Tutor Profile</h1>
      <p className="page-intro">
        Fill in your details to create a tutor profile. Fields marked with * are
        required.
      </p>

      <TutorForm
        initialValues={{ ...EMPTY_TUTOR_FORM_VALUES, full_name: user?.full_name ?? "" }}
        submitLabel="Create profile"
        isSubmitting={isSubmitting}
        submitError={submitError}
        cancelTo="/dashboard"
        onSubmit={handleSubmit}
      />
    </div>
  );
}

export default CreateTutorPage;