// Signed-in pages: a sidebar whose menu depends on the security role and the
// account type, plus the page content. On small screens the sidebar becomes
// a slide-in drawer.
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { personalDashboardPath } from "../auth/dashboardPath";
import { Brand } from "../components/Navbar";
import type { User } from "../types/auth";

interface MenuItem {
  to: string;
  label: string;
  end?: boolean;
}

interface MenuSection {
  heading: string;
  items: MenuItem[];
}

export function buildMenu(user: User): MenuSection[] {
  const sections: MenuSection[] = [];

  if (user.role === "admin") {
    sections.push({
      heading: "Administration",
      items: [
        { to: "/admin", label: "Overview", end: true },
        { to: "/admin/users", label: "Users" },
        { to: "/admin/content", label: "Content moderation" },
        { to: "/admin/audit", label: "Activity log" },
        { to: "/admin/security", label: "Security monitoring" },
      ],
    });
  }

  const learning: MenuItem[] = [
    { to: personalDashboardPath(user), label: user.role === "admin" ? "My dashboard" : "Dashboard" },
  ];
  if (user.account_type === "tutor") {
    learning.push({ to: "/tutor-profile", label: "My tutor profile" });
  }
  learning.push(
    { to: "/tutors", label: "Find tutors", end: true },
    { to: "/groups", label: "Study groups" },
    { to: "/records", label: "My records" }
  );
  sections.push({ heading: user.account_type === "tutor" ? "Tutoring" : "Learning", items: learning });
  sections.push({ heading: "Account", items: [{ to: "/account", label: "Account settings" }] });
  return sections;
}

function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  if (user === null) {
    return null; // RequireAuth redirects before this happens
  }

  async function handleLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  const roleLabel = user.role === "admin" ? `Admin · ${user.account_type}` : user.account_type;

  return (
    <div className="app-shell">
      <aside className={isOpen ? "sidebar is-open" : "sidebar"} aria-label="Dashboard navigation">
        <Brand />
        {buildMenu(user).map((section) => (
          <nav key={section.heading} className="sidebar-section" aria-label={section.heading}>
            <p className="sidebar-heading">{section.heading}</p>
            <ul className="sidebar-nav">
              {section.items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) => (isActive ? "sidebar-link active" : "sidebar-link")}
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        ))}
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <strong title={user.full_name}>{user.full_name}</strong>
            <span className="muted small" style={{ textTransform: "capitalize" }}>{roleLabel}</span>
          </div>
          <button type="button" className="btn btn-secondary btn-block" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </aside>
      {isOpen && <div className="sidebar-backdrop" onClick={() => setIsOpen(false)} aria-hidden="true" />}

      <div className="app-main">
        <div className="app-topbar">
          <Brand />
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            aria-expanded={isOpen}
            onClick={() => setIsOpen(true)}
          >
            Menu
          </button>
        </div>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
