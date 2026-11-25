import { Link } from "react-router-dom";
import { Brand } from "./Navbar";

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <Brand />
            <p className="small" style={{ marginTop: "0.75rem", maxWidth: 360 }}>
              A peer learning and tutoring platform where university students find
              tutors among their peers and organise study groups.
            </p>
          </div>
          <div>
            <h2>Explore</h2>
            <ul>
              <li><Link to="/tutors">Find Tutors</Link></li>
              <li><Link to="/about">About Peerora</Link></li>
            </ul>
          </div>
          <div>
            <h2>Account</h2>
            <ul>
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/signup">Sign Up</Link></li>
            </ul>
          </div>
        </div>
        <p className="footer-bottom">
          &copy; {new Date().getFullYear()} Peerora &middot; CSE309 course project
        </p>
      </div>
    </footer>
  );
}

export default Footer;
