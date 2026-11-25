import { Link } from "react-router-dom";

function AboutPage() {
  return (
    <main className="container page">
      <article className="prose">
        <p className="eyebrow">About</p>
        <h1>About Peerora</h1>
        <p className="page-intro">
          Peerora is a peer learning and tutoring platform for university students,
          built as a CSE309 course project.
        </p>

        <h2>What you can do</h2>
        <ul className="check-list">
          <li>Browse and search peer tutor profiles by subject, department and teaching mode.</li>
          <li>Tutors publish one profile with their subjects, experience and optional hourly rate.</li>
          <li>Anyone with an account can create study groups and share tasks and notes.</li>
          <li>Keep personal study records that only you can see.</li>
        </ul>

        <h2>Accounts</h2>
        <p>
          When you sign up you choose a <strong>Student</strong> or <strong>Tutor</strong> account.
          The account type decides which dashboard you see. Administrator access cannot be
          requested at signup; it is granted only by existing administrators.
        </p>

        <h2>Privacy and security</h2>
        <p>
          Passwords are hashed with Argon2id. Sign-in sessions are short-lived and can be
          reviewed and ended from your account settings. Your University Student ID is only
          shown to you and to administrators.
        </p>

        <div className="inline-actions section-gap">
          <Link to="/tutors" className="btn btn-primary">Find tutors</Link>
          <Link to="/signup" className="btn btn-secondary">Create an account</Link>
        </div>
      </article>
    </main>
  );
}

export default AboutPage;
