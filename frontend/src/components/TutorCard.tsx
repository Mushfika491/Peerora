import { useState } from "react";
import { Link } from "react-router-dom";
import type { Tutor } from "../types/tutor";
import {
  formatHourlyRate,
  formatSemester,
  getInitials,
  getTeachingModeLabel,
  getTutoringExperienceLabel,
} from "../utils/format";

interface TutorCardProps {
  tutor: Tutor;
}

const BIO_PREVIEW_LENGTH = 140;
const MAX_VISIBLE_SUBJECTS = 3;

// Shortens a long "About Me" text and adds "..." at the end.
function createBioPreview(bio: string): string {
  const text = bio.trim();
  if (text.length <= BIO_PREVIEW_LENGTH) {
    return text;
  }
  return `${text.slice(0, BIO_PREVIEW_LENGTH).trimEnd()}...`;
}

function TutorCard({ tutor }: TutorCardProps) {
  // If the image address is broken, switch to the initials fallback.
  const [imageFailed, setImageFailed] = useState(false);

  const showImage = tutor.profile_image_url !== null && !imageFailed;

  // Only the first few subjects are shown; the details page lists all of them.
  const visibleSubjects = tutor.subjects.slice(0, MAX_VISIBLE_SUBJECTS);
  const hiddenSubjectCount = tutor.subjects.length - visibleSubjects.length;

  return (
    <article className="tutor-card">
      <div className="tutor-card-header">
        {showImage ? (
          <img
            className="tutor-avatar"
            src={tutor.profile_image_url ?? ""}
            alt={`Profile photo of ${tutor.full_name}`}
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="tutor-avatar tutor-avatar-fallback" aria-hidden="true">
            {getInitials(tutor.full_name)}
          </div>
        )}

        <h3 className="tutor-card-name">{tutor.full_name}</h3>
      </div>

      <ul className="chip-list" aria-label="Subjects">
        {visibleSubjects.map((subject) => (
          <li key={subject} className="badge">
            {subject}
          </li>
        ))}
        {hiddenSubjectCount > 0 && (
          <li className="badge">+{hiddenSubjectCount} more</li>
        )}
      </ul>

      <p className="tutor-card-headline">{tutor.headline}</p>
      <p className="tutor-card-bio">{createBioPreview(tutor.bio)}</p>

      <dl className="tutor-meta">
        <dt>Department</dt>
        <dd>{tutor.department}</dd>
        <dt>Semester</dt>
        <dd>{formatSemester(tutor.semester)}</dd>
        <dt>Experience</dt>
        <dd>{getTutoringExperienceLabel(tutor.tutoring_experience)}</dd>
        <dt>Rate</dt>
        <dd>{formatHourlyRate(tutor.hourly_rate)}</dd>
        <dt>Mode</dt>
        <dd>{getTeachingModeLabel(tutor.teaching_mode)}</dd>
      </dl>

      <div className="tutor-card-footer">
        <Link
          to={`/tutors/${encodeURIComponent(String(tutor.id))}`}
          className="btn btn-primary"
        >
          View profile
        </Link>
      </div>
    </article>
  );
}

export default TutorCard;