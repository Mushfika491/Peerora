import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { ApiError } from "../services/apiClient";
import { deleteTutor, getTutorById } from "../services/tutorService";
import type { Tutor } from "../types/tutor";
import {
  formatCgpa,
  formatDate,
  formatHourlyRate,
  formatSemester,
  getInitials,
  getTeachingModeLabel,
  getTutoringExperienceLabel,
} from "../utils/format";
import { getErrorMessage, getSuccessMessage } from "../utils/messages";

type LoadStatus = "loading" | "success" | "error" | "not-found";

function TutorDetailsPage() {
  // "id" comes from the URL /tutors/:id
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const successMessage = getSuccessMessage(location.state);

  const [tutor, setTutor] = useState<Tutor | null>(null);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadCount, setReloadCount] = useState(0);
  const [imageFailed, setImageFailed] = useState(false);

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

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
      setImageFailed(false);

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

  async function handleConfirmDelete() {
    if (tutor === null) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteTutor(tutor.id);
      navigate("/tutors", {
        state: { successMessage: "Tutor profile deleted successfully." },
      });
    } catch (error) {
      setDeleteError(getErrorMessage(error));
      setIsDeleting(false);
      setIsDeleteDialogOpen(false);
    }
  }

  if (status === "loading") {
    return (
      <main className="container page">
        <LoadingState message="Loading tutor profile..." />
      </main>
    );
  }

  if (status === "not-found") {
    return (
      <main className="container page">
        <EmptyState
          title="Tutor not found"
          message="This tutor profile does not exist. It may have been deleted."
          actionLabel="Back to all tutors"
          actionTo="/tutors"
        />
      </main>
    );
  }

  if (status === "error" || tutor === null) {
    return (
      <main className="container page">
        <ErrorState
          title="Could not load this tutor"
          message={errorMessage || "The tutor profile could not be loaded."}
          onRetry={() => setReloadCount((count) => count + 1)}
        />
      </main>
    );
  }

  const showImage = tutor.profile_image_url !== null && !imageFailed;
  const tutorPath = `/tutors/${encodeURIComponent(String(tutor.id))}`;

  return (
    <main className="container page">
      <Link to="/tutors" className="back-link">
        &larr; Back to all tutors
      </Link>

      {successMessage !== null && (
        <div className="alert alert-success" role="status">
          {successMessage}
        </div>
      )}

      {deleteError !== null && (
        <div className="alert alert-error" role="alert">
          {deleteError}
        </div>
      )}

      <article className="details-card">
        <div className="details-header">
          {showImage ? (
            <img
              className="details-avatar"
              src={tutor.profile_image_url ?? ""}
              alt={`Profile photo of ${tutor.full_name}`}
              onError={() => setImageFailed(true)}
            />
          ) : (
            <div
              className="details-avatar details-avatar-fallback"
              aria-hidden="true"
            >
              {getInitials(tutor.full_name)}
            </div>
          )}

          <div>
            <h1>{tutor.full_name}</h1>
            <p className="details-headline">{tutor.headline}</p>
          </div>
        </div>

        <h2>Subjects You Can Tutor</h2>
        <ul className="chip-list" aria-label="Subjects this tutor can teach">
          {tutor.subjects.map((subject) => (
            <li key={subject} className="badge">
              {subject}
            </li>
          ))}
        </ul>

        <h2>About Me</h2>
        <p className="details-bio">{tutor.bio}</p>

        <h2>Academic Information</h2>
        <dl className="tutor-meta">
          <dt>University Student ID</dt>
          <dd>{tutor.student_id}</dd>
          <dt>Department</dt>
          <dd>{tutor.department}</dd>
          <dt>Current semester</dt>
          <dd>{formatSemester(tutor.semester)}</dd>
          <dt>CGPA</dt>
          <dd>{formatCgpa(tutor.cgpa)}</dd>
        </dl>

        <h2>Tutoring Details</h2>
        <dl className="tutor-meta">
          <dt>Previous tutoring experience</dt>
          <dd>{getTutoringExperienceLabel(tutor.tutoring_experience)}</dd>
          <dt>Teaching mode</dt>
          <dd>{getTeachingModeLabel(tutor.teaching_mode)}</dd>
          <dt>Hourly rate</dt>
          <dd>{formatHourlyRate(tutor.hourly_rate)}</dd>
        </dl>

        <p className="details-timestamps">
          Created on {formatDate(tutor.created_at)} &middot; Last updated on{" "}
          {formatDate(tutor.updated_at)}
        </p>

        <div className="details-actions">
          <Link to={`${tutorPath}/edit`} className="btn btn-primary">
            Edit profile
          </Link>
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => setIsDeleteDialogOpen(true)}
          >
            Delete profile
          </button>
        </div>
      </article>

      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        title="Delete tutor profile?"
        message={`Are you sure you want to delete the profile of ${tutor.full_name}? This action cannot be undone.`}
        confirmLabel="Delete"
        isProcessing={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setIsDeleteDialogOpen(false)}
      />
    </main>
  );
}

export default TutorDetailsPage;