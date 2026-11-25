// Public tutor directory. Search, filters and pagination run on the server
// (GET /api/tutors?q=&subject=&department=&teaching_mode=&limit=&offset=) and
// are kept in the URL, so a filtered list can be bookmarked or shared.
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Pagination from "../components/Pagination";
import TutorCard from "../components/TutorCard";
import { ALL_SUBJECTS, DEPARTMENTS, TEACHING_MODE_OPTIONS } from "../constants/tutorOptions";
import { useAsync } from "../hooks/useAsync";
import { searchTutors } from "../services/tutorService";

const PAGE_SIZE = 12;
const SORTED_SUBJECTS = [...ALL_SUBJECTS].sort((a, b) => a.localeCompare(b));

function TutorDirectoryPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const filters = {
    q: params.get("q") ?? "",
    subject: params.get("subject") ?? "",
    department: params.get("department") ?? "",
    teaching_mode: params.get("teaching_mode") ?? "",
  };
  const page = Math.max(1, Number(params.get("page") ?? "1") || 1);
  const [searchText, setSearchText] = useState(filters.q);

  const { state, reload } = useAsync(
    () =>
      searchTutors({
        ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== "")),
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      }),
    [params.toString()]
  );

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value === "") next.delete(key);
    else next.set(key, value);
    if (key !== "page") next.delete("page");
    setParams(next);
  }

  const hasActiveFilters = Object.values(filters).some((value) => value !== "");

  function clearFilters() {
    setSearchText("");
    setParams(new URLSearchParams());
  }

  const canCreateProfile = user !== null && user.account_type === "tutor" && !user.has_tutor_profile;

  return (
    <main className="container page">
      <div className="page-header">
        <div>
          <h1>Find Tutors</h1>
          <p className="page-intro" style={{ margin: 0 }}>
            Browse peer tutors by subject, department and teaching mode.
          </p>
        </div>
        {canCreateProfile && (
          <Link to="/tutors/new" className="btn btn-primary">Create Tutor Profile</Link>
        )}
      </div>

      <form className="filter-bar" onSubmit={(event) => { event.preventDefault(); setFilter("q", searchText.trim()); }}>
        <div className="form-field grow">
          <label htmlFor="tutor-search">Search</label>
          <input id="tutor-search" type="search" className="form-input"
            placeholder="Name, subject, department or headline"
            value={searchText} onChange={(event) => setSearchText(event.target.value)} />
        </div>
        <div className="form-field">
          <label htmlFor="subject-filter">Subject</label>
          <select id="subject-filter" className="form-input" value={filters.subject}
            onChange={(event) => setFilter("subject", event.target.value)}>
            <option value="">All subjects</option>
            {SORTED_SUBJECTS.map((subject) => (
              <option key={subject} value={subject}>{subject}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="department-filter">Department</label>
          <select id="department-filter" className="form-input" value={filters.department}
            onChange={(event) => setFilter("department", event.target.value)}>
            <option value="">All departments</option>
            {DEPARTMENTS.map((department) => (
              <option key={department} value={department}>{department}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="mode-filter">Teaching mode</label>
          <select id="mode-filter" className="form-input" value={filters.teaching_mode}
            onChange={(event) => setFilter("teaching_mode", event.target.value)}>
            <option value="">Any mode</option>
            {TEACHING_MODE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        <button type="submit" className="btn btn-primary">Search</button>
        {hasActiveFilters && (
          <button type="button" className="btn btn-secondary" onClick={clearFilters}>Clear filters</button>
        )}
      </form>

      {state.status === "loading" && <LoadingState message="Loading tutors..." />}

      {state.status === "error" && (
        <ErrorState title="Could not load tutors" message={state.message} onRetry={reload} />
      )}

      {state.status === "success" && state.data.total === 0 && (
        hasActiveFilters ? (
          <EmptyState title="No matching tutors" message="Try a different search or remove some filters." />
        ) : (
          <EmptyState title="No tutor profiles yet" message="There are no tutors to show yet." />
        )
      )}

      {state.status === "success" && state.data.total > 0 && (
        <>
          <p className="results-count" aria-live="polite">
            {state.data.total} tutor{state.data.total === 1 ? "" : "s"} found
          </p>
          <div className="tutor-grid">
            {state.data.tutors.map((tutor) => (
              <TutorCard key={tutor.id} tutor={tutor} />
            ))}
          </div>
          {state.data.total > PAGE_SIZE && (
            <Pagination page={page} pageSize={PAGE_SIZE} total={state.data.total}
              onPageChange={(value) => setFilter("page", String(value))} />
          )}
        </>
      )}
    </main>
  );
}

export default TutorDirectoryPage;
