# Peerora: Peer Learning and Tutoring Platform

Peerora is a university peer-tutoring platform. Students find peer tutors.
Tutors publish profiles. Everyone can organise study groups with shared,
assignable study records. Administrators manage users and moderate content
from a separate admin dashboard.

CSE309 final project. Stack: **React + TypeScript + Vite** frontend, **FastAPI + SQLAlchemy + Pydantic**
backend, **Supabase PostgreSQL** with **Alembic** migrations, deployed on **Vercel**.

## Features

- **Accounts and authentication**
  - Signup as **Student** or **Tutor**. Admin can never be chosen at signup.
  - Login and logout. The session is restored after a page reload.
  - Profile editing and password change (the current password is required).
  - Active-session list with per-device revocation.
  - A banned user is signed out of the browser on their next request.
  - Show/hide toggle (eye icon) on every password field.
  - **Forgot password:** the reset link is emailed and expires after 30 minutes. See [Password reset and email](#password-reset-and-email).
- **Security**
  - Argon2id password hashing with a server-side pepper.
  - 15-minute JWT access tokens.
  - Rotating refresh tokens in HttpOnly cookies, with reuse detection. Simultaneous refreshes from two tabs are tolerated.
  - Login throttling that resists lockout abuse (see [Security notes](#security-notes)), and signup rate limiting.
  - A complete audit log.
  - Security headers, a Content-Security-Policy, and no stack traces in responses.
- **RBAC**
  - The security role (`user`/`admin`) is stored separately from the account type (`student`/`tutor`).
  - Central permission map (`backend/peerora/core/permissions.py`).
  - Reusable FastAPI dependencies, plus ownership checks in every service.
- **Tutors**
  - Public directory with server-side search, filters and pagination.
  - One profile per tutor account. Only the owner (or an admin) can edit or delete it.
  - The Student ID is private.
- **Study groups**
  - The owner manages members by email and gives each one **independent permissions** to create, update and assign shared records (see [Group permissions](#group-permissions)).
  - Shared records (tasks and notes) with assignment and status.
  - Non-members see nothing (404).
- **Personal records:** visible only to their creator.
- **Dashboards:** Student, Tutor and Admin. Admins land on the admin dashboard first.
- **Admin dashboard**
  - Overview statistics.
  - User management: search, filters, pagination, detail view, ban/unban (a reason is required for both and recorded in the activity log), bulk ban/unban, role changes, session revocation.
  - Content moderation: single and bulk delete.
  - Activity log with filters and a text search (action, IP, browser, details, or a user's email).
  - Failed-login monitoring.
  - CSV exports that follow the active filters.

## Architecture

```
frontend/  React SPA     pages → services/*.ts → apiClient.ts (Bearer token, auto-refresh)
backend/   FastAPI       routers → services (business rules, audit) → models (SQLAlchemy)
             core/        security (hashing, JWT), permissions (RBAC), dependencies (auth)
             alembic/     migrations (tutors → users → sessions/audit → groups → member permissions)
vercel.json  /api/* → FastAPI service, everything else → the SPA (same origin)
```

See [`FINAL_REPORT.md`](FINAL_REPORT.md) for the full PRD/SRS/TDD, database design, security design and test results.

## Project status

| Part | Status |
|---|---|
| All features, authentication, RBAC, groups, admin dashboard | ✅ Complete; tested end to end on a local frontend and backend connected to the Supabase PostgreSQL database (see [`docs/PHASE3_E2E_TEST_REPORT.md`](docs/PHASE3_E2E_TEST_REPORT.md)) |
| Backend tests / frontend tests / type-check / build | ✅ Passing locally (see [Tests](#tests)) |
| Supabase migrations 0002–0008 | ✅ Applied to the Supabase database (with backups taken first) |
| Demo accounts | ✅ Created in the Supabase database (see [Demo accounts](#demo-accounts)) |
| Vercel deployment | ⏳ Not done yet (needs the owner's approval) |

## Group permissions

Every group has exactly one **owner**. The owner can do everything:
- rename, edit or delete the group;
- add and remove members;
- change each member's permissions.

Every other member can read the group, its members and its records. They also have three independent permissions:

| Permission | Allows |
|---|---|
| `can_create_records` | Adding shared records |
| `can_update_records` | Editing shared records. Also lets the member delete records **they** created. |
| `can_assign_records` | Choosing or changing who a record is assigned to |

- The member's role is a **label derived from these permissions**: `editor` has all three, `viewer` has none, and `member` is any other combination.
- In the UI the owner toggles each permission per member (Members tab), or uses the *All* / *None* shortcuts.
- Whatever their permissions, the person a record is assigned to can always change that record's status.
- Every rule is enforced by the API (`backend/peerora/services/group_service.py`, `record_service.py`), so a direct API request cannot bypass it.
- API: `PATCH /api/groups/{id}/members/{user_id}` accepts a preset (`"group_role": "editor" | "viewer"`) and/or individual booleans (`can_create_records`, `can_update_records`, `can_assign_records`).

## Requirements

- Python **3.11+** with `venv` (on Ubuntu: `sudo apt install python3-venv`). The code uses `enum.StrEnum`.
- Node.js 22+

Backend dependencies are pinned to the tested versions in `backend/requirements.txt` (production). `backend/requirements-dev.txt` adds pytest and pytest-cov.

## Environment variables

Names only. Never commit real values. Copy `backend/.env.example` to `backend/.env` for local use, and set the same names in Vercel for production.

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | Supabase PostgreSQL connection string, for local development and production (session pooler locally, transaction pooler on Vercel). Private: see [Database](#database) |
| `JWT_SECRET_KEY` | backend | Signs access tokens (≥ 32 random characters) |
| `PASSWORD_PEPPER` | backend | Server-side password pepper (≥ 16 characters; keep a private copy) |
| `ACCESS_TOKEN_MINUTES` | backend | Access-token lifetime, at most 15 (default 15) |
| `REFRESH_TOKEN_DAYS` | backend | Refresh-session lifetime (default 7) |
| `COOKIE_SECURE` | backend | `true` in production (default); `false` only for local http |
| `TRUST_PROXY_HEADERS` | backend | Read client IP from `X-Forwarded-For` (automatic on Vercel) |
| `CORS_ORIGINS` | backend | Allowed frontend origins, comma-separated |
| `EMAIL_BACKEND` | backend | `smtp` (production), `outbox` (local development only), or unset (password reset by email reported as unavailable) |
| `PUBLIC_APP_URL` | backend | Frontend address used in reset links, e.g. `https://your-app.vercel.app` (required in production) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `SMTP_SSL`, `EMAIL_FROM` | backend | SMTP provider settings for `EMAIL_BACKEND=smtp` (`SMTP_PASSWORD` is a secret) |
| `EMAIL_OUTBOX_DIR` | backend | Where `outbox` writes `.eml` files (default `backend/dev-outbox/`, git-ignored) |
| `EMAIL_OUTBOX_ALLOW_REMOTE_DB` | backend | Default `false`: `outbox` is refused against the Supabase database, so local runs cannot create real reset tokens by accident. Set `true` only on purpose for a local reset test; never on Vercel |
| `VITE_API_BASE_URL` | frontend | **Leave empty / unset** (same origin). Set it only to use a backend on another origin; the value must not end in `/api`. |

Rate limits (`LOGIN_*`, `MAX_SIGNUPS_PER_IP`, `REFRESH_REUSE_GRACE_SECONDS`) are constants in `backend/peerora/constants.py`, not environment variables.

## Run locally

**Backend** (terminal 1):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt   # production deps + pytest
cp .env.example .env               # then fill in DATABASE_URL (Supabase), JWT_SECRET_KEY, PASSWORD_PEPPER
fastapi dev main.py                # http://localhost:8000/api/docs
```

**Frontend** (terminal 2):

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173 (Vite proxies /api to :8000)
```

## Database

Peerora uses the existing **Supabase PostgreSQL** project as its database, both for local development and in production.

- `DATABASE_URL` is private. Set it only through environment variables that stay out of Git:
  - **Locally:** in `backend/.env`, which Git ignores, or as a variable in your shell. Real environment variables take priority over `backend/.env`.
  - **On Vercel:** under Settings → Environment Variables.
- Never commit a connection string, and never put real values in `backend/.env.example` (it holds placeholders only).
- Locally, use the Supabase **session pooler** (port 5432); on Vercel, use the **transaction pooler** (port 6543). Keep `COOKIE_SECURE=false` locally, because the dev servers use plain `http://localhost`.
- A local backend works on the **real** data, so anything you do in the app changes it. Use the demo accounts for testing.
- Schema changes go through Alembic only; see [Database migrations](#database-migrations).

## Database migrations

Migrations are additive and keep all existing data:
- `0003` only adds a nullable `tutors.user_id` column.
- `0006` adds the three member-permission columns and fills them from the existing roles: owner and editor get all three, viewer gets none.

Every migration has a downgrade. `alembic upgrade head` changes the database that `DATABASE_URL` points at, which is the Supabase database, so take a backup first and apply migrations only with the owner's approval.

```bash
cd backend
alembic upgrade head --sql > /tmp/peerora-migration.sql   # 1. review the SQL first (no DB connection)
alembic upgrade head                                      # 2. apply (back up the database first)
alembic downgrade -1                                      # roll back one step if needed
```

Rehearse on a disposable PostgreSQL database (`DATABASE_URL` pointing at it) before touching the real one: `upgrade head`, then `downgrade base`, then `upgrade head`.

## Admin accounts and demo data

Admins cannot sign up. Create them with the bootstrap script. Passwords are typed at a hidden prompt and never printed. These scripts write to the database in `DATABASE_URL` (Supabase), so run them only when you mean to:

```bash
cd backend
python -m scripts.create_admin --email admin@example.com --name "Ada Admin" --account-type student
python -m scripts.create_admin --email someone@example.com --promote
python -m scripts.seed_demo        # 2 admins, 4 users, tutor profiles, records, mixed-permission group
```

### Demo accounts

These are created by `scripts/seed_demo.py`. Passwords are handed in through the submission form only, never in this repository.

| Email | Account type | Security role |
|---|---|---|
| admin1@peerora.demo | Student | admin |
| admin2@peerora.demo | Tutor | admin |
| student1@peerora.demo | Student | user (owner of "CSE309 Project Group") |
| student2@peerora.demo | Student | user (viewer in the group: no permissions) |
| tutor1@peerora.demo | Tutor | user (editor in the group: create, update and assign) |
| tutor2@peerora.demo | Tutor | user (not a member, so the group is hidden from them) |

To demonstrate independent permissions, log in as student1, open the group's **Members** tab, and give student2 only **Create**. As student2 you can then add records but not edit them or pick an assignee.

## Tests

```bash
cd backend && python -m pytest tests --cov=peerora --cov=main  # backend (in-memory SQLite, never Supabase)
cd backend && python -m unittest discover -s tests -t . -v     # the same suite without pytest
cd frontend && npm run test && npm run build                   # frontend tests + type-check + build
python backend/tests/live_smoke_test.py https://<deployment>   # against a running deployment
```

Latest local results: see [`FINAL_REPORT.md`](FINAL_REPORT.md), section 9.

The live smoke test creates no data. Set `SMOKE_EMAIL` and `SMOKE_PASSWORD` (a normal demo account) to include the login → refresh → logout cycle.

The manual verification checklist is in [`docs/MANUAL_TEST_CHECKLIST.md`](docs/MANUAL_TEST_CHECKLIST.md).

## API documentation

Interactive OpenAPI docs: `/api/docs` (Swagger UI) and `/api/redoc`.

## Password reset and email

1. On the login page, **Forgot password?** opens `/forgot-password`, which asks for the account's email.
2. `POST /api/auth/password-reset/request` always answers with the same generic message, whether or not the email has an account. A real, non-banned account gets a new token, and the email is sent in the background so the reply time gives nothing away.
3. The token is 256 random bits. The database stores only its SHA-256 hash. It expires after **30 minutes**, works **once**, and requesting a new link retires the older ones.
4. The link is `PUBLIC_APP_URL/reset-password#token=…`. The token sits after `#`, so browsers never send it to any server or proxy log, and the page removes it from the address bar straight away.
5. `POST /api/auth/password-reset/confirm` checks the token and the password policy, sets the new password, and **signs out every session** of the account.
6. Rate limits:
   - 5 reset requests per IP address per hour (HTTP 429);
   - at most 3 emails per account per hour; extra requests get the same generic reply, but no email.

   Every request and completion is audited; the token never is.

**Email setup.** No email provider was configured before this feature. Choose one:
- **Production:** set `EMAIL_BACKEND=smtp`, `PUBLIC_APP_URL` and the `SMTP_*` / `EMAIL_FROM` values in Vercel. Any SMTP provider works, using Python's standard `smtplib`; no extra dependency is needed.
- **Local testing:** add `EMAIL_BACKEND=outbox` to `backend/.env` and restart the backend. Reset emails then appear as `.eml` files in `backend/dev-outbox/` (git-ignored, readable only by you). Open the newest one and copy the link into the browser. The `outbox` backend refuses to run on Vercel.
- **Neither:** the Forgot password page says plainly that reset by email isn't available and suggests contacting an administrator. The API answers `503` for every email address, so nothing is pretended and no account can be enumerated.

## Security notes

- **Login throttling.** Failed passwords are counted per *(account, IP address)*. After 5 failures, that address is blocked for that account for 15 minutes, but the account owner can still sign in from their own network. One address is also limited to 20 failures across all accounts. The account as a whole locks only after 50 failures, which takes many addresses. Requests refused by the throttle never count as guesses.
- **Signup** is limited to 10 new accounts per IP address per hour.
- **Refresh tokens** rotate on every use. Presenting an old token again revokes the whole session, unless it happens within 10 seconds of the rotation: that is what two tabs refreshing at once, or a retried request, look like. Browser tabs also take turns refreshing (Web Locks API).
- **Suspended accounts.** The API marks "account suspended" 403 responses with `X-Error-Code: account_suspended`. The frontend signs the user out only for those, never for ordinary permission errors.
- **Timestamps** are stored in UTC and always sent by the API with an explicit offset (`...Z`), on PostgreSQL and in the in-memory test database alike (`UtcDateTime` column type in `backend/peerora/models/helpers.py`). The browser shows them in the viewer's own timezone (UTC+6 in Bangladesh). Audit date filters use the viewer's local day boundaries. CSV exports use UTC (`created_at_utc`).
- **Browser in the activity log.** Brave sends Chrome's exact User-Agent. The backend recognises Brave from the browser's `Sec-CH-UA` client hint (sent over HTTPS and on localhost) or from a frontend `navigator.brave` check, and stores a `Brave` token with the user agent. Other Chromium browsers are never labelled Brave. Brave sessions recorded before this change still show as Chrome.
- **Content-Security-Policy.**
  - API responses: `default-src 'none'`. The interactive docs pages are excluded because they load from a CDN.
  - The built React app gets a `<meta>` policy allowing only its own scripts, Google Fonts and HTTPS images (`frontend/csp.ts`). The dev server is left without a policy so hot reloading works.

## Deploy to Vercel

1. In Vercel → Settings → Environment Variables, set `DATABASE_URL`, `JWT_SECRET_KEY`,
   `PASSWORD_PEPPER`, `CORS_ORIGINS` (the deployment URL) and `COOKIE_SECURE=true`.
   **Remove or empty `VITE_API_BASE_URL`** if the mid-term setup defined it. The app now calls `/api/...` on its own origin, so a value ending in `/api` would produce `/api/api/...`.
2. Back up the database and apply the migrations (`alembic upgrade head`, after reviewing `alembic upgrade head --sql`). Migrate **before** deploying: the new code needs the new tables and columns.
3. Create the admins and demo data (scripts above).
4. Deploy (push to `main`, or run `vercel --prod`).
5. Run the live smoke test against the deployment URL.

The frontend and API share one origin (`vercel.json` rewrites `/api/*`), so the
`SameSite=Strict` refresh cookie works in production.
