import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { useToast } from "../components/Toast";
import TutorForm from "../components/TutorForm";
import { ApiError } from "../services/apiClient";
import { uploadProfileImage } from "../services/imageService";
import { getTutorById, updateTutor } from "../services/tutorService";
import type { Tutor, TutorFormData } from "../types/tutor";
import { getErrorMessage } from "../utils/messages";
import { tutorToFormValues } from "../utils/validation";

type LoadStatus = "loading" | "success" | "error" | "not-found";

function EditTutorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [tutor, setTutor] = useState<Tutor | null>(null);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadCount, setReloadCount] = useState(0);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Load the existing tutor so the form can be pre-filled.
  useEffect(() => {
    const tutorId = Number(id);
    if (!Number.isInteger(tutorId) || tutorId < 1) {
      setStatus("not-found");
      return;
    }

    let ignore = false;

    async function loadTutor(tutorId: number) {
      setStatus("loading");
      setErrorMessage("");

      try {
        const data = await getTutorById(tutorId);
        if (!ignore) {
          setTutor(data);
          setStatus("success");
        }
      } catch (error) {
        if (!ignore) {
          if (error instanceof ApiError && error.status === 404) {
            setStatus("not-found");
          } else {
            setErrorMessage(getErrorMessage(error));
            setStatus("error");
          }
        }
      }
    }

    loadTutor(tutorId);

    return () => {
      ignore = true;
    };
  }, [id, reloadCount]);

  async function handleSubmit(data: TutorFormData, imageFile: File | null) {
    if (tutor === null) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // A newly chosen picture is uploaded first and replaces the saved one.
      // Without a new picture, data.profile_image_url already holds the saved
      // address, or null if the user removed the picture.
      // Image upload is not connected yet, so the form does not allow a new
      // picture to reach this point until imageService is completed.
      const profileImageUrl =
        imageFile === null ? data.profile_image_url : await uploadProfileImage(imageFile);

      const updatedTutor = await updateTutor(tutor.id, {
        ...data,
        profile_image_url: profileImageUrl,
      });

      toast.success("Tutor profile updated successfully.");
      navigate(`/tutors/${updatedTutor.id}`);
    } catch (error) {
      setSubmitError(getErrorMessage(error));
      setIsSubmitting(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  if (status === "loading") {
    return (
      <div className="form-page">
        <LoadingState message="Loading tutor profile..." />
      </div>
    );
  }

  if (status === "not-found") {
    return (
      <div className="form-page">
        <EmptyState
          headingLevel="h1"
          title="Tutor not found"
          message="This tutor profile does not exist, so it cannot be edited."
          actionLabel="Back to all tutors"
          actionTo="/tutors"
        />
      </div>
    );
  }

  if (status === "error" || tutor === null) {
    return (
      <div className="form-page">
        <ErrorState
          title="Could not load this tutor"
          message={errorMessage || "The tutor profile could not be loaded."}
          onRetry={() => setReloadCount((count) => count + 1)}
        />
      </div>
    );
  }

  const detailsPath = `/tutors/${tutor.id}`;

  // Only the owner or an administrator may edit (the backend enforces this too).
  if (user === null || (user.id !== tutor.user_id && user.role !== "admin")) {
    return (
      <div className="form-page">
        <EmptyState
          title="You cannot edit this profile"
          message="Only the owner of a tutor profile (or an administrator) can edit it."
          actionLabel="Back to the profile"
          actionTo={detailsPath}
        />
      </div>
    );
  }

  return (
    <div className="form-page">
      <Link to={detailsPath} className="back-link">
        &larr; Back to profile
      </Link>

      <h1>Edit Tutor Profile</h1>
      <p className="page-intro">
        Update the details below and save your changes. Fields marked with * are
        required.
      </p>

      <TutorForm
        initialValues={tutorToFormValues(tutor)}
        submitLabel="Save changes"
        isSubmitting={isSubmitting}
        submitError={submitError}
        cancelTo={detailsPath}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

export default EditTutorPage;