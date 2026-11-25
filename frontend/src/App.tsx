// Route table.
//   Public pages     -> PublicLayout (navbar + footer)
//   Signed-in pages  -> RequireAuth + AppLayout (role-aware sidebar)
//   Admin pages      -> additionally RequireAdmin
// Guards only shape the UI; the backend authorizes every request itself.
import { Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { DashboardRedirect, GuestOnly, RequireAccountType, RequireAdmin, RequireAuth } from "./auth/guards";
import LoadingState from "./components/LoadingState";
import AppLayout from "./layouts/AppLayout";
import PublicLayout from "./layouts/PublicLayout";
import AboutPage from "./pages/AboutPage";
import AccountPage from "./pages/account/AccountPage";
import AdminAuditPage from "./pages/admin/AdminAuditPage";
import AdminContentPage from "./pages/admin/AdminContentPage";
import AdminOverviewPage from "./pages/admin/AdminOverviewPage";
import AdminSecurityPage from "./pages/admin/AdminSecurityPage";
import AdminUserDetailPage from "./pages/admin/AdminUserDetailPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";
import LoginPage from "./pages/auth/LoginPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import ResetPasswordPage from "./pages/auth/ResetPasswordPage";
import SignupPage from "./pages/auth/SignupPage";
import CreateTutorPage from "./pages/CreateTutorPage";
import DashboardHome from "./pages/dashboard/DashboardHome";
import TutorProfileRedirect from "./pages/dashboard/TutorProfileRedirect";
import EditTutorPage from "./pages/EditTutorPage";
import ForbiddenPage from "./pages/ForbiddenPage";
import GroupDetailPage from "./pages/groups/GroupDetailPage";
import GroupsPage from "./pages/groups/GroupsPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import MyRecordsPage from "./pages/records/MyRecordsPage";
import TutorDetailsPage from "./pages/TutorDetailsPage";
import TutorDirectoryPage from "./pages/TutorDirectoryPage";

function App() {
  const { status } = useAuth();

  // Until the session is restored nothing is rendered, so a signed-in user
  // never briefly sees guest-only content (or is redirected to /login).
  if (status === "restoring") {
    return (
      <div className="boot-screen">
        <LoadingState message="Loading Peerora..." />
      </div>
    );
  }

  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/tutors" element={<TutorDirectoryPage />} />
        <Route path="/tutors/:id" element={<TutorDetailsPage />} />
        <Route path="/login" element={<GuestOnly><LoginPage /></GuestOnly>} />
        <Route path="/signup" element={<GuestOnly><SignupPage /></GuestOnly>} />
        <Route path="/forgot-password" element={<GuestOnly><ForgotPasswordPage /></GuestOnly>} />
        {/* Not guest-only: the emailed link must work even in a signed-in browser. */}
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/forbidden" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
        <Route path="/dashboard" element={<DashboardRedirect />} />
        <Route path="/dashboard/student" element={<RequireAccountType type="student"><DashboardHome variant="student" /></RequireAccountType>} />
        <Route path="/dashboard/tutor" element={<RequireAccountType type="tutor"><DashboardHome variant="tutor" /></RequireAccountType>} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="/groups" element={<GroupsPage />} />
        <Route path="/groups/:id" element={<GroupDetailPage />} />
        <Route path="/records" element={<MyRecordsPage />} />
        <Route path="/tutor-profile" element={<RequireAccountType type="tutor"><TutorProfileRedirect /></RequireAccountType>} />
        <Route path="/tutors/new" element={<RequireAccountType type="tutor"><CreateTutorPage /></RequireAccountType>} />
        <Route path="/tutors/:id/edit" element={<EditTutorPage />} />

        <Route element={<RequireAdmin />}>
          <Route path="/admin" element={<AdminOverviewPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/users/:id" element={<AdminUserDetailPage />} />
          <Route path="/admin/content" element={<AdminContentPage />} />
          <Route path="/admin/audit" element={<AdminAuditPage />} />
          <Route path="/admin/security" element={<AdminSecurityPage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
