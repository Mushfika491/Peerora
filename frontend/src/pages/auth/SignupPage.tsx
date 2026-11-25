import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { dashboardPath } from "../../auth/dashboardPath";
import FormField from "../../components/FormField";
import PasswordInput from "../../components/PasswordInput";
import { useToast } from "../../components/Toast";
import type { AccountType } from "../../types/auth";
import { checkEmail, checkFullName, checkPassword } from "../../utils/authValidation";
import { getErrorMessage } from "../../utils/messages";

type Field = "full_name" | "email" | "password" | "confirm";

// Public signup offers exactly two account types. Administrator is never an
// option here (and the backend rejects it even if someone tries).
const ACCOUNT_TYPES: { value: AccountType; title: string; text: string }[] = [
  { value: "student", title: "Student", text: "Find tutors and join study groups" },
  { value: "tutor", title: "Tutor", text: "Publish a tutor profile and help peers" },
];

function SignupPage() {
  const { signup } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialType: AccountType = searchParams.get("type") === "tutor" ? "tutor" : "student";

  const [accountType, setAccountType] = useState<AccountType>(initialType);
  const [values, setValues] = useState<Record<Field, string>>({
    full_name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update(field: Field, value: string) {
    setValues((previous) => ({ ...previous, [field]: value }));
    setErrors((previous) => ({ ...previous, [field]: undefined }));
  }

  function validate(): Partial<Record<Field, string>> {
    const found: Partial<Record<Field, string>> = {
      full_name: checkFullName(values.full_name),
      email: checkEmail(values.email),
      password: checkPassword(values.password, values.email),
      confirm: values.confirm !== values.password ? "The passwords do not match." : undefined,
    };
    return Object.fromEntries(Object.entries(found).filter(([, message]) => message !== undefined));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate();
    setErrors(found);
    const firstField = (["full_name", "email", "password", "confirm"] as Field[]).find((f) => found[f]);
    if (firstField !== undefined) {
      document.getElementById(`signup-${firstField}`)?.focus();
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const user = await signup({
        full_name: values.full_name.trim(),
        email: values.email.trim(),
        password: values.password,
        account_type: accountType,
      });
      toast.success("Your account was created.");
      const target = user.account_type === "tutor" ? "/tutors/new" : dashboardPath(user);
      navigate(target, { replace: true });
    } catch (caught) {
      setSubmitError(getErrorMessage(caught));
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <aside className="auth-aside">
        <h2>Join Peerora</h2>
        <p>One account for learning and teaching with your peers.</p>
        <ul>
          <li>Students: find tutors and study together</li>
          <li>Tutors: share your strongest subjects</li>
          <li>Everyone: private records and study groups</li>
        </ul>
      </aside>
      <section className="auth-panel">
        <div className="auth-card card">
          <h1>Create your account</h1>
          <p className="muted">Fields marked with * are required.</p>

          {submitError !== null && (
            <div className="alert alert-error" role="alert">
              {submitError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <fieldset className="form-fieldset" disabled={isSubmitting}>
              <fieldset className="form-fieldset form-field">
                <legend style={{ fontWeight: 600, marginBottom: "0.35rem" }}>I want to join as *</legend>
                <div className="choice-grid">
                  {ACCOUNT_TYPES.map((option) => (
                    <label key={option.value} className="choice-card">
                      <input
                        type="radio"
                        name="account_type"
                        value={option.value}
                        checked={accountType === option.value}
                        onChange={() => setAccountType(option.value)}
                      />
                      <strong>{option.title}</strong>
                      <span>{option.text}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <FormField id="signup-full_name" label="Full name" required error={errors.full_name}>
                {(control) => (
                  <input {...control} className="form-input" autoComplete="name"
                    value={values.full_name} onChange={(e) => update("full_name", e.target.value)} />
                )}
              </FormField>
              <FormField id="signup-email" label="Email" required error={errors.email}>
                {(control) => (
                  <input {...control} type="email" className="form-input" autoComplete="email"
                    value={values.email} onChange={(e) => update("email", e.target.value)} />
                )}
              </FormField>
              <FormField id="signup-password" label="Password" required error={errors.password}
                hint="At least 8 characters, with at least one letter and one number.">
                {(control) => (
                  <PasswordInput {...control} autoComplete="new-password"
                    value={values.password} onChange={(e) => update("password", e.target.value)} />
                )}
              </FormField>
              <FormField id="signup-confirm" label="Confirm password" required error={errors.confirm}>
                {(control) => (
                  <PasswordInput {...control} autoComplete="new-password"
                    value={values.confirm} onChange={(e) => update("confirm", e.target.value)} />
                )}
              </FormField>
              <button type="submit" className="btn btn-primary btn-block">
                {isSubmitting ? "Creating account..." : "Create account"}
              </button>
            </fieldset>
          </form>
          <p className="auth-switch muted">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>
      </section>
    </main>
  );
}

export default SignupPage;
