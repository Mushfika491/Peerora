import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  DEPARTMENTS,
  SEMESTERS,
  SUBJECT_GROUPS,
  TEACHING_MODE_OPTIONS,
  TUTORING_EXPERIENCE_OPTIONS,
} from "../constants/tutorOptions";
import {
  IMAGE_UPLOAD_AVAILABLE,
  IMAGE_UPLOAD_UNAVAILABLE_MESSAGE,
} from "../services/imageService";
import { isTeachingMode, isTutoringExperience } from "../types/tutor";
import type { TutorFormData } from "../types/tutor";
import {
  BIO_MAX_LENGTH,
  EMPTY_TUTOR_FORM_VALUES,
  HEADLINE_MAX_LENGTH,
  countCharacters,
  hasErrors,
  toTutorFormData,
  validateTutorForm,
} from "../utils/validation";
import type { TutorFormErrors, TutorFormValues } from "../utils/validation";
import FormField from "./FormField";
import ImageUpload from "./ImageUpload";
import MultiSelect from "./MultiSelect";
import SearchableSelect from "./SearchableSelect";

interface TutorFormProps {
  initialValues?: TutorFormValues; // used by the edit page; omitted when creating
  submitLabel: string; // e.g. "Create profile" or "Save changes"
  isSubmitting: boolean; // true while the API request is running
  submitError?: string | null; // error message from the API, shown above the form
  cancelTo: string; // where the Cancel button goes
  // Called only after validation passes. "imageFile" is a newly chosen picture
  // that still has to be uploaded (null when there is none). In "data",
  // profile_image_url holds the already saved address, if any.
  onSubmit: (data: TutorFormData, imageFile: File | null) => void;
}

// The order in which fields appear on screen. After a failed submit, the first
// field with an error in this order receives the keyboard focus. Each name is
// also the id of that field's control.
const FIELD_ORDER: readonly (keyof TutorFormValues)[] = [
  "full_name",
  "student_id",
  "department",
  "semester",
  "cgpa",
  "profile_image_file",
  "headline",
  "subjects",
  "teaching_mode",
  "hourly_rate",
  "tutoring_experience",
  "bio",
];

function focusFirstError(errors: TutorFormErrors) {
  const firstField = FIELD_ORDER.find((field) => errors[field] !== undefined);
  if (firstField !== undefined) {
    document.getElementById(firstField)?.focus();
  }
}

function TutorForm({
  initialValues = EMPTY_TUTOR_FORM_VALUES,
  submitLabel,
  isSubmitting,
  submitError = null,
  cancelTo,
  onSubmit,
}: TutorFormProps) {
  const [values, setValues] = useState<TutorFormValues>(initialValues);
  const [errors, setErrors] = useState<TutorFormErrors>({});

  // Updates one field and removes that field's old error message.
  // The generic type K links the field name to the type of its value, so
  // TypeScript rejects a wrong value type.
  function updateField<K extends keyof TutorFormValues>(
    field: K,
    value: TutorFormValues[K]
  ) {
    setValues((previous) => ({ ...previous, [field]: value }));
    setErrors((previous) => {
      const updated = { ...previous };
      delete updated[field];
      return updated;
    });
  }

  // The two native dropdowns return plain text, so the text is checked before
  // it is stored in a field that only accepts specific values.
  function handleTeachingModeChange(event: ChangeEvent<HTMLSelectElement>) {
    const selected = event.target.value;
    updateField("teaching_mode", isTeachingMode(selected) ? selected : "");
  }

  function handleExperienceChange(event: ChangeEvent<HTMLSelectElement>) {
    const selected = event.target.value;
    updateField(
      "tutoring_experience",
      isTutoringExperience(selected) ? selected : ""
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    // Stop the browser from reloading the page.
    event.preventDefault();

    const validationErrors = validateTutorForm(values);

    // A picture cannot be saved until storage is really connected.
    if (
      values.profile_image_file !== null &&
      validationErrors.profile_image_file === undefined &&
      !IMAGE_UPLOAD_AVAILABLE
    ) {
      validationErrors.profile_image_file = IMAGE_UPLOAD_UNAVAILABLE_MESSAGE;
    }

    setErrors(validationErrors);

    if (hasErrors(validationErrors)) {
      focusFirstError(validationErrors);
      return;
    }

    const savedImageUrl = values.profile_image_url.trim();
    onSubmit(
      toTutorFormData(values, savedImageUrl === "" ? null : savedImageUrl),
      values.profile_image_file
    );
  }

  return (
    <form className="tutor-form" onSubmit={handleSubmit} noValidate>
      {submitError !== null && (
        <div className="alert alert-error" role="alert">
          {submitError}
        </div>
      )}

      {hasErrors(errors) && (
        <div className="alert alert-error" role="alert">
          Please correct the highlighted fields and try again.
        </div>
      )}

      {/* A disabled fieldset disables every input and button inside it */}
      <fieldset className="form-fieldset" disabled={isSubmitting}>
        {/* ===== A. Personal and academic information ===== */}
        <section className="form-section" aria-labelledby="section-personal">
          <h2 id="section-personal" className="form-section-title">
            Personal &amp; Academic Information
          </h2>

          <FormField
            id="full_name"
            label="Full name"
            required
            error={errors.full_name}
          >
            {(control) => (
              <input
                {...control}
                name="full_name"
                type="text"
                className="form-input"
                autoComplete="name"
                value={values.full_name}
                onChange={(event) => updateField("full_name", event.target.value)}
              />
            )}
          </FormField>

          <FormField
            id="student_id"
            label="University Student ID"
            required
            hint="Exactly 7 characters. Student status is not verified."
            error={errors.student_id}
          >
            {(control) => (
              <input
                {...control}
                name="student_id"
                type="text"
                className="form-input"
                autoComplete="off"
                value={values.student_id}
                onChange={(event) => updateField("student_id", event.target.value)}
              />
            )}
          </FormField>

          <SearchableSelect
            id="department"
            label="Department"
            required
            options={DEPARTMENTS}
            value={values.department}
            onChange={(department) => updateField("department", department)}
            placeholder="Search for your department"
            noResultsText="No matching department."
            error={errors.department}
          />

          <div className="form-row">
            <FormField
              id="semester"
              label="Current Semester"
              required
              error={errors.semester}
            >
              {(control) => (
                <select
                  {...control}
                  name="semester"
                  className="form-input"
                  value={values.semester}
                  onChange={(event) => updateField("semester", event.target.value)}
                >
                  <option value="">Select semester</option>
                  {SEMESTERS.map((semester) => (
                    <option key={semester} value={semester}>
                      {semester}
                    </option>
                  ))}
                </select>
              )}
            </FormField>

            <FormField
              id="cgpa"
              label="CGPA"
              required
              hint="Between 0.00 and 4.00, for example 3.75."
              error={errors.cgpa}
            >
              {(control) => (
                <input
                  {...control}
                  name="cgpa"
                  type="text"
                  inputMode="decimal"
                  className="form-input"
                  autoComplete="off"
                  value={values.cgpa}
                  onChange={(event) => updateField("cgpa", event.target.value)}
                />
              )}
            </FormField>
          </div>

          <ImageUpload
            id="profile_image_file"
            label="Profile picture (optional)"
            hint="JPG, JPEG, PNG or WebP, up to 2 MB. Picture upload is not connected yet, so a profile cannot be saved with a new picture for now."
            file={values.profile_image_file}
            existingUrl={values.profile_image_url}
            onFileChange={(file) => updateField("profile_image_file", file)}
            onRemoveExisting={() => updateField("profile_image_url", "")}
            error={errors.profile_image_file}
          />
        </section>

        {/* ===== B. Tutoring information ===== */}
        <section className="form-section" aria-labelledby="section-tutoring">
          <h2 id="section-tutoring" className="form-section-title">
            Tutoring Information
          </h2>

          <FormField
            id="headline"
            label="Headline"
            required
            counter={`${countCharacters(values.headline)} / ${HEADLINE_MAX_LENGTH}`}
            error={errors.headline}
          >
            {(control) => (
              <input
                {...control}
                name="headline"
                type="text"
                className="form-input"
                placeholder="CSE Student | Python & Programming Fundamentals Tutor"
                value={values.headline}
                onChange={(event) => updateField("headline", event.target.value)}
              />
            )}
          </FormField>

          <MultiSelect
            id="subjects"
            label="Subjects You Can Tutor"
            required
            groups={SUBJECT_GROUPS}
            values={values.subjects}
            onChange={(subjects) => updateField("subjects", subjects)}
            hint="Select every subject you are comfortable teaching."
            error={errors.subjects}
          />

          <div className="form-row">
            <FormField
              id="teaching_mode"
              label="Teaching Mode"
              required
              error={errors.teaching_mode}
            >
              {(control) => (
                <select
                  {...control}
                  name="teaching_mode"
                  className="form-input"
                  value={values.teaching_mode}
                  onChange={handleTeachingModeChange}
                >
                  <option value="">Select teaching mode</option>
                  {TEACHING_MODE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
            </FormField>

            <FormField
              id="hourly_rate"
              label="Hourly Rate (BDT, optional)"
              hint="Leave empty if you prefer not to state a rate."
              error={errors.hourly_rate}
            >
              {(control) => (
                <input
                  {...control}
                  name="hourly_rate"
                  type="text"
                  inputMode="decimal"
                  className="form-input"
                  autoComplete="off"
                  value={values.hourly_rate}
                  onChange={(event) => updateField("hourly_rate", event.target.value)}
                />
              )}
            </FormField>
          </div>
        </section>

        {/* ===== C. Teaching experience ===== */}
        <section className="form-section" aria-labelledby="section-experience">
          <h2 id="section-experience" className="form-section-title">
            Teaching Experience
          </h2>

          <FormField
            id="tutoring_experience"
            label="Previous Tutoring Experience"
            required
            error={errors.tutoring_experience}
          >
            {(control) => (
              <select
                {...control}
                name="tutoring_experience"
                className="form-input"
                value={values.tutoring_experience}
                onChange={handleExperienceChange}
              >
                <option value="">Select your experience</option>
                {TUTORING_EXPERIENCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            )}
          </FormField>
        </section>

        {/* ===== D. About me ===== */}
        <section className="form-section" aria-labelledby="section-about">
          <h2 id="section-about" className="form-section-title">
            About Me
          </h2>

          <FormField
            id="bio"
            label="About Me"
            required
            counter={`${countCharacters(values.bio)} / ${BIO_MAX_LENGTH}`}
            error={errors.bio}
          >
            {(control) => (
              <textarea
                {...control}
                name="bio"
                className="form-input"
                rows={6}
                placeholder="Describe your academic background, the topics you enjoy teaching, and how you like to teach (for example, working through examples or practising problems together)."
                value={values.bio}
                onChange={(event) => updateField("bio", event.target.value)}
              />
            )}
          </FormField>
        </section>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            {isSubmitting ? "Saving..." : submitLabel}
          </button>
          <Link to={cancelTo} className="btn btn-secondary">
            Cancel
          </Link>
        </div>
      </fieldset>
    </form>
  );
}

export default TutorForm;