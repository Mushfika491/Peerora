import { Link } from "react-router-dom";

function HomePage() {
  return (
    <main className="container page">
      <section className="hero">
        <h1>Learn from your peers with Peerora</h1>
        <p>
          Peerora is a university peer learning and tutoring platform. Browse
          tutor profiles by subject, or share your own knowledge by creating a
          tutor profile.
        </p>
        <div className="hero-actions">
          <Link to="/tutors" className="btn btn-primary">
            Find Tutors
          </Link>
          <Link to="/tutors/new" className="btn btn-secondary">
            Create Tutor Profile
          </Link>
        </div>
      </section>

      <section aria-labelledby="home-features-heading">
        <h2 id="home-features-heading" className="visually-hidden">
          What you can do on Peerora
        </h2>
        <div className="feature-grid">
          <article className="feature-card">
            <h3>Browse tutors</h3>
            <p>
              See each tutor's subjects, department, semester, experience, and
              hourly rate in one place.
            </p>
          </article>
          <article className="feature-card">
            <h3>Search and filter</h3>
            <p>Search by name or topic and narrow the list by subject.</p>
          </article>
          <article className="feature-card">
            <h3>Manage your profile</h3>
            <p>
              Create a tutor profile, update it whenever your details change, or
              remove it.
            </p>
          </article>
        </div>
      </section>
    </main>
  );
}

export default HomePage;