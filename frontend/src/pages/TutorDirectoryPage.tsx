import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import TutorCard from "../components/TutorCard";
import { getTutors } from "../services/tutorService";
import type { Tutor } from "../types/tutor";
import { getErrorMessage, getSuccessMessage } from "../utils/messages";

type LoadStatus = "loading" | "success" | "error";

function TutorDirectoryPage() {
  // A success message may arrive from another page (e.g. after deleting a profile).
  const location = useLocation();
  const successMessage = getSuccessMessage(location.state);

  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadCount, setReloadCount] = useState(0); // changing it reloads the data
  const [searchText, setSearchText] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("");

  // Load the tutors when the page opens, and again whenever "Try again" is clicked.
  useEffect(() => {
    // Prevents updating state if the page was left before the request finished.
    let ignore = false;

    async function loadTutors() {
      setStatus("loading");
      setErrorMessage("");

      try {
        const data = await getTutors();
        if (!ignore) {
          setTutors(data);
          setStatus("success");
        }
      } catch (error) {
        if (!ignore) {
          setErrorMessage(getErrorMessage(error));
          setStatus("error");
        }
      }
    }

    loadTutors();

    return () => {
      ignore = true;
    };
  }, [reloadCount]);

  // Unique, sorted subjects taken from all tutors, for the filter dropdown.
  const subjects = Array.from(
    new Set(tutors.flatMap((tutor) => tutor.subjects))
  ).sort((a, b) => a.localeCompare(b));

  // Apply the subject filter and the search text.
  const query = searchText.trim().toLowerCase();
  const filteredTutors = tutors.filter((tutor) => {
    // A tutor matches when ANY of their subjects equals the selected one.
    const matchesSubject =
      selectedSubject === "" || tutor.subjects.includes(selectedSubject);

    const matchesSearch =
      query === "" ||
      [tutor.full_name, tutor.headline, tutor.department, ...tutor.subjects].some(
        (text) => text.toLowerCase().includes(query)
      );

    return matchesSubject && matchesSearch;
  });

  const hasActiveFilters = searchText !== "" || selectedSubject !== "";

  function clearFilters() {
    setSearchText("");
    setSelectedSubject("");
  }

  return (
    <main className="container page">
      <div className="page-header">
        <h1>Find Tutors</h1>
        <Link to="/tutors/new" className="btn btn-primary">
          Create Tutor Profile
        </Link>
      </div>

      {successMessage !== null && (
        <div className="alert alert-success" role="status">
          {successMessage}
        </div>
      )}

      {status === "loading" && <LoadingState message="Loading tutors..." />}

      {status === "error" && (
        <ErrorState
          title="Could not load tutors"
          message={errorMessage}
          onRetry={() => setReloadCount((count) => count + 1)}
        />
      )}

      {status === "success" && tutors.length === 0 && (
        <EmptyState
          title="No tutor profiles yet"
          message="There are no tutors to show. Be the first to create a profile."
          actionLabel="Create Tutor Profile"
          actionTo="/tutors/new"
        />
      )}

      {status === "success" && tutors.length > 0 && (
        <>
          <div className="toolbar">
            <div className="form-field">
              <label htmlFor="tutor-search">Search</label>
              <input
                id="tutor-search"
                type="search"
                className="form-input"
                placeholder="Name, subject, department or headline"
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
              />
            </div>

            <div className="form-field">
              <label htmlFor="subject-filter">Subject</label>
              <select
                id="subject-filter"
                className="form-input"
                value={selectedSubject}
                onChange={(event) => setSelectedSubject(event.target.value)}
              >
                <option value="">All subjects</option>
                {subjects.map((subject) => (
                  <option key={subject} value={subject}>
                    {subject}
                  </option>
                ))}
              </select>
            </div>

            {hasActiveFilters && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            )}
          </div>

          <p className="results-count" aria-live="polite">
            Showing {filteredTutors.length} of {tutors.length} tutors
          </p>

          {filteredTutors.length === 0 ? (
            <EmptyState
              title="No matching tutors"
              message="Try a different search or choose another subject."
            />
          ) : (
            <div className="tutor-grid">
              {filteredTutors.map((tutor) => (
                <TutorCard key={tutor.id} tutor={tutor} />
              ))}
            </div>
          )}
        </>
      )}
    </main>
  );
}

export default TutorDirectoryPage;