import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
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

  const [tutor, setTutor] = useState<Tutor | null>(null);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadCount, setReloadCount] = useState(0);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Load the existing tutor so the form can be pre-filled.
  useEffect(() => {
    if (id === undefined) {
      setErrorMessage("No tutor id was found in the address.");
      setStatus("error");
      return;
    }

    let ignore = false;

    async function loadTutor(tutorId: string) {
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

    loadTutor(id);

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

      navigate(`/tutors/${encodeURIComponent(String(updatedTutor.id))}`, {
        state: { successMessage: "Tutor profile updated successfully." },
      });
    } catch (error) {
      setSubmitError(getErrorMessage(error));
      setIsSubmitting(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  if (status === "loading") {
    return (
      <main className="container page form-page">
        <LoadingState message="Loading tutor profile..." />
      </main>
    );
  }

  if (status === "not-found") {
    return (
      <main className="container page form-page">
        <EmptyState
          title="Tutor not found"
          message="This tutor profile does not exist, so it cannot be edited."
          actionLabel="Back to all tutors"
          actionTo="/tutors"
        />
      </main>
    );
  }

  if (status === "error" || tutor === null) {
    return (
      <main className="container page form-page">
        <ErrorState
          title="Could not load this tutor"
          message={errorMessage || "The tutor profile could not be loaded."}
          onRetry={() => setReloadCount((count) => count + 1)}
        />
      </main>
    );
  }

  const detailsPath = `/tutors/${encodeURIComponent(String(tutor.id))}`;

  return (
    <main className="container page form-page">
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
    </main>
  );
}

export default EditTutorPage;