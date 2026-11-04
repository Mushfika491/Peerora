import { Link, NavLink } from "react-router-dom";

// NavLink passes { isActive } to className so the current page's link
// can be highlighted.
function getLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "navbar-link active" : "navbar-link";
}

function Navbar() {
  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand">
          Peerora
        </Link>

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
              <NavLink to="/tutors/new" className={getLinkClassName}>
                Create Tutor Profile
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

export default Navbar;