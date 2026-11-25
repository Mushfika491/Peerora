// "My tutor profile": opens the tutor's own profile, or the setup form.
import { Navigate } from "react-router-dom";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import { useAsync } from "../../hooks/useAsync";
import { getMyTutorProfile } from "../../services/tutorService";

function TutorProfileRedirect() {
  const { state, reload } = useAsync(getMyTutorProfile, []);
  if (state.status === "loading") {
    return <LoadingState message="Loading your tutor profile..." />;
  }
  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={reload} />;
  }
  return <Navigate to={state.data === null ? "/tutors/new" : `/tutors/${state.data.id}`} replace />;
}

export default TutorProfileRedirect;
