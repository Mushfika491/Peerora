import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { dashboardPath } from "../auth/dashboardPath";

// NavLink passes { isActive } to className so the current page's link
// can be highlighted.
function getLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "navbar-link active" : "navbar-link";
}

export function Brand({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="brand" aria-label="Peerora home">
      <span className="brand-mark" aria-hidden="true">P</span>
      Peerora
    </Link>
  );
}

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  // Close the mobile menu after navigating.
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  async function handleLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Brand />

        <button
          type="button"
          className="btn btn-ghost navbar-toggle"
          aria-expanded={isOpen}
          aria-controls="main-menu"
          onClick={() => setIsOpen((open) => !open)}
        >
          {isOpen ? "Close" : "Menu"}
        </button>

        <div id="main-menu" className={isOpen ? "navbar-menu is-open" : "navbar-menu"}>
          <nav aria-label="Main navigation">
            <ul className="navbar-links">
              <li>
                <NavLink to="/" end className={getLinkClassName}>
                  Home
                </NavLink>
              </li>
              <li>
                <NavLink to="/tutors" end className={getLinkClassName}>
                  Find Tutors
                </NavLink>
              </li>
              <li>
                <NavLink to="/about" className={getLinkClassName}>
                  About
                </NavLink>
              </li>
            </ul>
          </nav>

          <ul className="navbar-actions">
            {user === null ? (
              <>
                <li>
                  <Link to="/login" className="btn btn-ghost">
                    Login
                  </Link>
                </li>
                <li>
                  <Link to="/signup" className="btn btn-primary">
                    Sign Up
                  </Link>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link to={dashboardPath(user)} className="btn btn-primary">
                    {user.role === "admin" ? "Admin Dashboard" : "My Dashboard"}
                  </Link>
                </li>
                <li>
                  <button type="button" className="btn btn-ghost" onClick={handleLogout}>
                    Log out
                  </button>
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
