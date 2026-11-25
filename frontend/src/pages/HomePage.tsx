import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { dashboardPath } from "../auth/dashboardPath";
import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import TutorCard from "../components/TutorCard";
import { useAsync } from "../hooks/useAsync";
import { getTutors } from "../services/tutorService";

const STEPS = [
  { title: "Create your account", text: "Sign up as a Student to find help, or as a Tutor to share what you know." },
  { title: "Find the right peer", text: "Search tutors by subject, department and teaching mode." },
  { title: "Study together", text: "Create a study group, add classmates and share tasks and notes." },
  { title: "Track your progress", text: "Assign tasks to members and move them from To do to Done." },
];

function FeaturedTutors() {
  // The three newest tutor profiles. GET /api/tutors is public.
  const { state } = useAsync(() => getTutors({ limit: 3 }), []);

  if (state.status === "loading") {
    return <LoadingState message="Loading tutors..." />;
  }
  if (state.status === "error") {
    return <p className="muted">Featured tutors could not be loaded right now.</p>;
  }
  if (state.data.length === 0) {
    return (
      <EmptyState
        title="No tutors yet"
        message="Be the first tutor on Peerora."
        actionLabel="Sign up as a tutor"
        actionTo="/signup?type=tutor"
      />
    );
  }
  return (
    <div className="tutor-grid">
      {state.data.map((tutor) => (
        <TutorCard key={tutor.id} tutor={tutor} />
      ))}
    </div>
  );
}

function HomePage() {
  const { user } = useAuth();

  return (
    <main>
      {/* ===== Hero ===== */}
      <section className="home-hero">
        <div className="container home-hero-grid">
          <div>
            <p className="eyebrow">Peer learning for university students</p>
            <h1>Learn faster with help from the students who just aced it.</h1>
            <p className="lead">
              Peerora connects you with peer tutors from your university and gives
              your study group one place to plan, share and finish the work.
            </p>
            <div className="home-hero-actions">
              <Link to="/tutors" className="btn btn-primary btn-lg">
                Find a tutor
              </Link>
              {user === null ? (
                <Link to="/signup" className="btn btn-secondary btn-lg">
                  Create a free account
                </Link>
              ) : (
                <Link to={dashboardPath(user)} className="btn btn-secondary btn-lg">
                  Go to my dashboard
                </Link>
              )}
            </div>
          </div>
          <div className="hero-panel" aria-hidden="true">
            <div className="hero-panel-row">
              <span className="hero-dot">AR</span>
              <div>
                <strong>Algorithms tutor</strong>
                <p className="muted small" style={{ margin: 0 }}>CSE · Semester 7 · Online</p>
              </div>
            </div>
            <div className="hero-panel-row">
              <span className="hero-dot">SG</span>
              <div>
                <strong>DBMS Study Group</strong>
                <p className="muted small" style={{ margin: 0 }}>4 members · 6 open tasks</p>
              </div>
            </div>
            <div className="hero-panel-row">
              <span className="hero-dot">✓</span>
              <div>
                <strong>Normalization exercises</strong>
                <p className="muted small" style={{ margin: 0 }}>Assigned to you · Due Friday</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== How it works ===== */}
      <section className="home-section" aria-labelledby="how-heading">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">How Peerora works</p>
            <h2 id="how-heading">From stuck to sorted in four steps</h2>
          </div>
          <div className="steps-grid">
            {STEPS.map((step) => (
              <article key={step.title} className="step-card">
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ===== Featured tutors ===== */}
      <section className="home-section alt" aria-labelledby="featured-heading">
        <div className="container">
          <div className="page-header">
            <div>
              <p className="eyebrow">Featured tutors</p>
              <h2 id="featured-heading" style={{ margin: 0 }}>Meet some of our peer tutors</h2>
            </div>
            <Link to="/tutors" className="btn btn-secondary">
              View all tutors
            </Link>
          </div>
          <FeaturedTutors />
        </div>
      </section>

      {/* ===== Study groups ===== */}
      <section className="home-section" aria-labelledby="groups-heading">
        <div className="container split">
          <div>
            <p className="eyebrow">Study groups</p>
            <h2 id="groups-heading">Organise your study group in one shared space</h2>
            <ul className="check-list">
              <li>Create a group for a course and add classmates by email.</li>
              <li>Give each member a role: editors manage tasks, viewers follow along.</li>
              <li>Share tasks and notes, assign them and track their status.</li>
              <li>Only members can see what happens inside the group.</li>
            </ul>
            <Link to={user === null ? "/signup" : "/groups"} className="btn btn-primary">
              {user === null ? "Start a study group" : "Open my study groups"}
            </Link>
          </div>
          <div className="hero-panel">
            <p className="eyebrow">Group roles</p>
            <dl className="tutor-meta" style={{ margin: 0 }}>
              <dt>Owner</dt>
              <dd>Renames or deletes the group and manages members.</dd>
              <dt>Editor</dt>
              <dd>Creates, edits and assigns shared records.</dd>
              <dt>Viewer</dt>
              <dd>Reads everything and updates tasks assigned to them.</dd>
            </dl>
          </div>
        </div>
      </section>

      {/* ===== Why Peerora ===== */}
      <section className="home-section alt" aria-labelledby="why-heading">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Why Peerora</p>
            <h2 id="why-heading">Built for students, by students</h2>
          </div>
          <div className="steps-grid">
            <article className="feature-card">
              <h3>Relatable tutors</h3>
              <p>Learn from peers who took the same courses recently.</p>
            </article>
            <article className="feature-card">
              <h3>Fair and flexible</h3>
              <p>Tutors set their own teaching mode and optional hourly rate.</p>
            </article>
            <article className="feature-card">
              <h3>Private by default</h3>
              <p>Your Student ID, records and groups are only visible to the right people.</p>
            </article>
            <article className="feature-card">
              <h3>Secure accounts</h3>
              <p>Modern password hashing, short-lived sessions and active-session control.</p>
            </article>
          </div>
        </div>
      </section>

      <section className="home-section">
        <div className="container">
          <div className="cta-band">
            <h2>Ready to learn together?</h2>
            <p>Join as a Student or a Tutor. It takes less than a minute.</p>
            <div className="home-hero-actions" style={{ justifyContent: "center" }}>
              <Link to="/signup?type=student" className="btn btn-secondary btn-lg">
                I am a Student
              </Link>
              <Link to="/signup?type=tutor" className="btn btn-secondary btn-lg">
                I am a Tutor
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

export default HomePage;
