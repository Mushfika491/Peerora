# Peerora: Final Project Report (CSE309)

**Peerora: a peer learning and tutoring platform.**
React + TypeScript + Vite · FastAPI · SQLAlchemy · Pydantic · Alembic · Supabase PostgreSQL · Vercel

This report replaces the planning documents in `docs/01-prd.md`, `docs/02-srs.md` and `docs/03-tdd.md`.
It describes the application **as implemented**. Section 9 states which verification steps have
been carried out and which are still outstanding.

---

## 1. Product Requirements (PRD)

### 1.1 Problem and goal
Students struggle to find classmates who can explain a subject, and study-group work is often
scattered across chats. Peerora gives them three things in one place:

- a directory of peer tutors from their university;
- private study groups with shared, assignable tasks and notes;
- a protected administration area to keep the platform safe.

### 1.2 Users

| User | Description |
|---|---|
| Visitor | Not signed in. Can browse the homepage, the tutor directory and tutor profiles, and can sign up or log in. |
| Student (account type) | Finds tutors, creates and joins study groups, keeps personal records. |
| Tutor (account type) | Everything a student can do, plus publishing **one** tutor profile. |
| Administrator (security role) | Any Student or Tutor account with role `admin`. Manages users, moderates content, reviews the audit log and exports. |

### 1.3 Scope (implemented)
1. Authentication:
   - signup, login and logout;
   - profile editing and password change;
   - session restoration;
   - active sessions and session revocation.
2. Two separate concepts, kept apart in the database and in the code:
   - account type (`student`/`tutor`);
   - security role (`user`/`admin`).
3. Backend-enforced RBAC and ownership checks.
4. Tutor profiles linked to accounts:
   - public directory with search, filters and pagination;
   - owner-only editing;
   - the Student ID is private.
5. Study groups in which the owner gives each member independent create, update and assign permissions, and shared study records (tasks/notes) that can be assigned.
6. Personal study records.
7. Student, Tutor and Admin dashboards.
8. Admin dashboard:
   - overview statistics;
   - user management, including bulk actions;
   - content moderation;
   - audit log;
   - failed-login monitoring;
   - CSV exports.
9. Redesigned, responsive UI.

### 1.4 Out of scope
Several items from the original plan were dropped:

- **Bookings, availability slots and study-material uploads.** These were planned in the original PRD. They are replaced by study groups and records, as the final brief requires.
- **Other dropped items:** payments, chat, video calls, email verification, password-reset email, and real profile-picture storage. The image upload is still a disabled stub.

### 1.5 Changes from the original plan

| Original plan | Implemented | Reason |
|---|---|---|
| Roles `learner`/`tutor`/`admin` in one field | `account_type` (student/tutor) **and** `role` (user/admin) | The final brief requires the two concepts to be kept separate |
| Base path `/api/v1`, PATCH for tutors | `/api`, PUT for tutors | Keeps the working mid-term API contract and its tests |
| SQLite locally | SQLite only in automated tests; Supabase PostgreSQL elsewhere | The existing deployment already used Supabase |
| Bookings and materials | Study groups and study records | The final brief |

---

## 2. Software Requirements (SRS)

### 2.1 Functional requirements

| ID | Requirement | Where implemented |
|---|---|---|
| FR-1 | Visitors sign up as Student or Tutor. The role is always `user`; admin cannot be chosen. | `schemas/auth.py` `SignupIn` (no role field, `extra="forbid"`), `services/auth_service.signup` |
| FR-2 | Login with email and password. Failures get one generic message. | `auth_service.login` |
| FR-3 | Logout revokes the device session and clears the cookie. | `routers/auth.logout` |
| FR-4 | Session restore on reload, via the refresh cookie. | `frontend/src/auth/AuthContext.tsx` |
| FR-5 | View and update the profile. Changing the email requires the current password. Role and account type cannot be changed. | `routers/users.update_me` |
| FR-6 | Password change requires the current password and signs out other sessions. | `auth_service.change_password` |
| FR-7 | List active sessions and revoke one. | `routers/users` |
| FR-7a | Forgotten password: generic reply, hashed single-use token valid for 30 minutes, emailed link, new password checked against the policy, every session ended on success, rate limited, honest "unavailable" message when no email backend is configured. | `services/password_reset_service.py`, `services/email_service.py`, `routers/auth.py` |
| FR-8 | Brute-force protection that resists lockout abuse: within 15 minutes, 5 wrong passwords per (account, IP), 20 per IP, or 50 per account gives HTTP 429. Throttled requests are not counted as guesses. Signup is limited to 10 per IP per hour. | `auth_service.is_login_throttled`, `_recent_signups` + `login_attempts` |
| FR-9 | Tutor accounts create exactly one profile, linked to their account. | `routers/tutors.create_tutor`, `crud.create_tutor` |
| FR-10 | Only the owner (or an admin) can update or delete a tutor profile. | `crud.can_manage` |
| FR-11 | Public directory with server-side `q`, subject, department and mode filters, plus pagination. | `crud.list_tutors` |
| FR-12 | Any user can create a study group and becomes its owner. | `group_service.create_group` |
| FR-13 | Only the owner can rename or delete the group and manage membership: add by email, change each member's permissions, remove. | `group_service` |
| FR-14 | Members read shared records. Creating, updating and assigning need `can_create_records`, `can_update_records` and `can_assign_records` respectively; the owner holds all three. An assignee can always update the status. | `group_service.can_*`, `record_service` |
| FR-15 | Non-members get 404 for a group and all of its content. | `group_service.load_for_member` |
| FR-16 | Personal records are visible only to their creator. | `record_service.load_for_user` |
| FR-17 | After login, users are sent to the right dashboard by role, then by account type. | `frontend/src/auth/dashboardPath.ts` |
| FR-18 | Admin overview statistics. | `admin_service.overview` |
| FR-19 | Admin user list with search, filters and pagination; detail view with records, groups, sessions and activity. | `routers/admin_users` |
| FR-20 | Ban and unban, single or bulk; **a reason (3–500 characters) is required for both** and stored in the audit log. Banning revokes all sessions, and the frontend signs a banned user out on their next request. | `admin_service`, `schemas/admin.py`, `apiClient.ts` |
| FR-21 | Role changes. An admin cannot change their own role or ban an admin. | `admin_service.change_role / _check_can_ban` |
| FR-22 | Moderation: list and search records and groups; delete one or many. | `routers/admin_content` |
| FR-23 | Audit log of logins (success and failure), logout, password change, role change, ban/unban, deletions and exports, with IP, user agent and time. Filterable, and the text search matches the action, IP, browser, details and the actor's or target's email. | `services/audit_service.py`, `routers/admin_audit` |
| FR-24 | Failed logins grouped by IP address and by account. | `admin_service.security_report` |
| FR-25 | CSV export of users, records and activity logs, following the active filters. | `routers/admin_exports` |

### 2.2 Non-functional requirements
- **Security:**
  - Argon2id hashing with a pepper;
  - JWTs that last 15 minutes or less;
  - HttpOnly refresh cookie with rotation;
  - authorization on the server for every request;
  - no secrets in the code, the logs or API responses.
- **Reliability:**
  - DB constraints, FKs and indexes on every table;
  - additive, reversible migrations;
  - a generic 500 response that never shows a stack trace.
- **Usability:**
  - responsive layouts (sidebar becomes a drawer, collapsible navbar);
  - loading, empty and error states;
  - toasts and confirmation dialogs;
  - accessible forms (labels, `aria-invalid`, focus moves to the first error).
- **Maintainability:** layers run router → service → model, with one module per feature.

### 2.3 Permission matrix

| Action | Visitor | User (student) | User (tutor) | Admin |
|---|---|---|---|---|
| Browse tutors / view profile | ✓ | ✓ | ✓ | ✓ (+ Student ID) |
| Create tutor profile | ✗ 401 | ✗ 403 | ✓ (one) | if Tutor type |
| Edit/delete a tutor profile | ✗ 401 | ✗ 403 | own only | ✓ (audited) |
| Create a group | ✗ 401 | ✓ | ✓ | ✓ |
| Any `/api/admin/*` endpoint | ✗ 401 | ✗ 403 | ✗ 403 | ✓ |
| Ban an admin / change own role | | | | ✗ 403 |

**Inside a study group.** Every non-owner permission is independent and set by the owner. Role labels: editor = all three, viewer = none, member = a mix.

| Action | Owner | Member with permission | Member without it | Non-member | Admin |
|---|---|---|---|---|---|
| Read group, members, records | ✓ | ✓ | ✓ | 404 | via moderation |
| Create a record | ✓ | `can_create_records` | 403 | 404 | — |
| Edit a record | ✓ | `can_update_records` | 403 | 404 | — |
| Set or change the assignee | ✓ | `can_assign_records` | 403 | 404 | — |
| Update the status of a record assigned to me | ✓ | ✓ | ✓ | — | — |
| Delete a record | any | own records, with `can_update_records` | 403 | 404 | ✓ (moderation) |
| Rename/delete group, manage members and permissions | ✓ | 403 | 403 | 404 | delete (moderation) |

### 2.4 Status codes
201 created · 200 ok · 204 deleted · 400 wrong current password · 401 missing, invalid,
expired or revoked token · 403 permission denied or banned · 404 not found (also used for
resources the caller may not see) · 409 conflict (duplicate email, Student ID, profile or
member) · 422 validation · 429 throttled · 500 generic error.

---

## 3. System architecture (TDD)

```
Browser ── React SPA (Vite build) ─────────────┐   same origin on Vercel
   pages → services/*.ts → apiClient.ts        │   (vercel.json: /api/* → FastAPI)
           Bearer access token (memory)        ▼
           HttpOnly refresh cookie ──►  FastAPI  main.py
                                         ├─ middleware: CORS, security headers
                                         ├─ routers/      HTTP layer + auth dependencies
                                         ├─ core/         security, permissions, dependencies
                                         ├─ services/     business rules + audit logging
                                         ├─ crud.py       tutor data access (from the MVP)
                                         └─ models/       SQLAlchemy 2.0 ORM
                                                ▼  psycopg 3 (pooler-safe)
                                         Supabase PostgreSQL (RLS on, owner connection)
```

### 3.1 Backend modules

| Module | Responsibility |
|---|---|
| `core/security.py` | Pepper + Argon2id hashing; creating and verifying JWTs (HS256, issuer and required claims); random refresh tokens + SHA-256 |
| `core/permissions.py` | `Permission` enum and `ROLE_PERMISSIONS`: the single source of RBAC truth |
| `core/dependencies.py` | `get_current_user` (token → user → banned? → session alive? → role matches the DB?), `require_permission`, `require_account_type` |
| `core/request_info.py` | Client IP (proxy-aware) and user agent for the audit log |
| `services/auth_service.py` | Signup, login with throttling and attempt recording, logout, password change |
| `services/session_service.py` | Session creation, refresh rotation, reuse detection, revocation |
| `services/group_service.py` / `record_service.py` | Group membership rules and record permissions (pure `can_edit` / `can_delete` functions) |
| `services/admin_service.py` | Overview, user management, the admin restrictions, moderation, audit queries. The filter builders are shared with the exports. |
| `services/audit_service.py` | `log_event()` and `sanitize()`, which drops any key that looks like a password, token or secret |
| `services/export_service.py` | Streamed CSV with formula-injection escaping |
| `routers/*` | Request parsing and dependency declaration only. No SQL. |

### 3.2 Frontend modules

| Module | Responsibility |
|---|---|
| `auth/AuthContext.tsx` | Central auth state (`restoring`/`authenticated`/`guest`); restores the session on load; one shared refresh request at a time |
| `auth/guards.tsx` | `RequireAuth`, `RequireAdmin`, `RequireAccountType`, `GuestOnly`, `DashboardRedirect`. These are for usability; the backend enforces access. |
| `services/apiClient.ts` | Adds the Bearer header; on a 401, refreshes once and retries; error parsing; CSV download |
| `services/*Service.ts` | One module per feature with runtime shape checks |
| `layouts/` | `PublicLayout` (navbar + footer) and `AppLayout` (sidebar whose menu depends on role and account type) |
| `pages/` | Public, auth, account, dashboard, groups, records and admin pages; the existing tutor pages are kept |
| `components/` | The existing accessible form controls, plus Toast, Pagination, StatCard, StatusBadge, PromptDialog, RecordForm and RecordList |

### 3.3 Request flow example: a member without update permission tries to edit a shared record

1. The page calls `GroupDetailPage → RecordList → groupService.updateRecord`, which sends `PATCH /api/records/7` with the Bearer token.
2. `get_current_user` checks the JWT signature and expiry, loads the user, rejects a banned user, confirms the session is not revoked, and checks the token role against the DB role.
3. `record_service.update_record` calls `load_for_user`. Because this is a group record and the caller is a member, the record is returned.
4. `can_edit` checks `group_service.can_update(membership)`, which is false here. The only exception is a request that changes nothing but the status of a record assigned to the caller. Otherwise the result is **403**. Changing the assignee is checked separately with `can_assign`.
5. A non-member gets **404** at step 3, so the record's existence is never revealed.

---

## 4. Database design

All tables have an integer (or UUID) primary key, timestamps, CHECK constraints, foreign keys
with deliberate `ON DELETE` rules, indexes on the lookup columns, and **Row Level Security
enabled**. The backend connects as the table owner, and RLS blocks Supabase's public data API.

| Table | Purpose and key columns | Relationships and constraints | Used by |
|---|---|---|---|
| `users` | `email` (unique, lowercase), `full_name`, `password_hash`, `account_type` ∈ {student, tutor}, `role` ∈ {user, admin}, `is_banned`, `ban_reason`, `banned_at`, `banned_by_id`, `last_login_at` | CHECK: a banned user must have a reason; `banned_by_id` → users (SET NULL); indexes on role, is_banned, created_at | Everything |
| `tutors` (existing) | All mid-term columns unchanged, plus **`user_id`** (nullable) | FK → users (SET NULL), UNIQUE `user_id` (one profile per user) | Tutor directory and profiles |
| `user_sessions` | `id` UUID (the JWT `sid`), `user_id`, IP, user agent, `last_used_at`, `expires_at`, `revoked_at`, `revoked_reason` | FK → users (CASCADE); index (user_id, revoked_at) | Session list and revocation, token validation |
| `refresh_tokens` | `session_id`, `token_hash` (SHA-256, unique), `expires_at`, `used_at` | FK → user_sessions (CASCADE) | Rotation and reuse detection |
| `login_attempts` | `email`, `user_id`, IP, user agent, `success`, `failure_reason` | FK → users (SET NULL); indexes (email, created_at), (ip, created_at) | Throttling and security monitoring |
| `password_reset_tokens` | `user_id`, `token_hash` (SHA-256, unique), `created_at`, `expires_at`, `used_at`, `requested_ip` | FK → users (CASCADE); index (user_id, created_at) | Forgotten password |
| `audit_logs` | `actor_id`, `target_user_id`, `action`, `target_type`, `target_id`, `details` (JSONB, sanitised), IP, user agent, `created_at` | FKs → users (SET NULL); indexes on created_at, action, actor, target | Activity log, exports |
| `study_groups` | `name` (≥ 2 characters), `description`, `subject`, `owner_id` | FK → users (CASCADE); indexes on owner, name | Groups |
| `group_memberships` | `group_id`, `user_id`, `can_create_records`, `can_update_records`, `can_assign_records` (booleans, default false), `group_role` ∈ {owner, editor, viewer, member} (label derived from the booleans), `added_by_id` | UNIQUE (group_id, user_id); role CHECK; FKs CASCADE / SET NULL | Group permissions |
| `study_records` | `title`, `content`, `status` ∈ {todo, in_progress, done}, `due_date`, `group_id` (NULL = personal), `created_by_id`, `assigned_to_id` | FKs: group CASCADE, creator CASCADE, assignee SET NULL; 4 indexes | Records, dashboards, moderation |

```
users 1─0..1 tutors            users 1─* user_sessions 1─* refresh_tokens
users 1─* study_groups(owner)  study_groups 1─* group_memberships *─1 users
study_groups 1─* study_records users 1─* study_records (created_by / assigned_to)
users 1─* audit_logs (actor/target)   users 1─* login_attempts
```

### 4.1 Migrations

| Revision | Change | Data impact |
|---|---|---|
| `3f8a1c2d9b7e` | (mid-term) create `tutors` | — |
| `0002_create_users` | `users` table | additive |
| `0003_link_tutors_to_users` | nullable `tutors.user_id` + FK + unique | **existing rows untouched** (`user_id` NULL; admin-managed until linked) |
| `0004_sessions_and_security` | `user_sessions`, `refresh_tokens`, `login_attempts`, `audit_logs` | additive |
| `0005_study_groups_and_records` | `study_groups`, `group_memberships`, `study_records` | additive |
| `0007_password_reset_tokens` | `password_reset_tokens` table (RLS on PostgreSQL) | additive |
| `0006_group_member_permissions` | three permission columns on `group_memberships`; role CHECK allows `member` | **additive + backfill**: owner/editor rows get all permissions, viewer rows none. Batch mode, so it runs on PostgreSQL and SQLite. |

Each migration has a full `downgrade()`. The procedure:

1. Review the SQL with `alembic upgrade head --sql`.
2. Rehearse on a disposable PostgreSQL: `upgrade head`, then `downgrade base`, then `upgrade head`. Migration 0006 has already been rehearsed on a throwaway SQLite copy of the dev data (section 9).
3. Back up the production database.
4. Apply the migrations.
5. Compare `SELECT count(*) FROM tutors` before and after.

---

## 5. Authentication and authorization design

1. **Passwords**
   - The server computes `HMAC-SHA256(PASSWORD_PEPPER, password)` and stores its Argon2id hash (argon2-cffi defaults).
   - Rules, checked on the backend and mirrored in the frontend: 8–128 characters, at least one letter and one digit, and not equal to the email.
   - Unknown emails still run one hash check, so failed logins take the same time whether or not the account exists.
2. **Access token**
   - An HS256 JWT with the claims `sub` (user id), `role`, `sid` (session id), `type=access`, `iss`, `iat` and `exp`. It lasts at most 15 minutes.
   - Only HS256 is accepted, so a token with `alg=none` is rejected.
   - The frontend keeps it in memory only.
3. **Validating a request** (`get_current_user`)
   - Each of these failures gives 401: a missing token, a malformed or tampered token, an expired token, a revoked or expired session, and a token role that differs from the DB role (for example after a role change).
   - A banned account gives 403.
   - Because the role is always read from the database, a role supplied by the frontend is never trusted.
4. **Refresh tokens**
   - A random 256-bit value. Only its SHA-256 hash is stored.
   - It is sent as the `peerora_refresh` cookie: `HttpOnly; Secure` (in production); `SameSite=Strict; Path=/api/auth`; 7 days.
   - Every refresh **rotates** it: the old token is marked `used_at`.
   - Presenting a used token again is treated as theft: the whole session is revoked, and the audit log records `token_reuse_detected`. The one exception is a repeat within **10 seconds** of the rotation on a still-active session (two tabs, a retried request): it receives a fresh token instead. A stolen token used later, or after logout, still revokes the session.
   - `/refresh` and `/logout` also require the `X-Requested-With: peerora` header as CSRF protection.
5. **Frontend concurrency.** Within a tab, all callers share one refresh promise. Across tabs, the Web Locks API (`navigator.locks`) makes tabs refresh one at a time, so the second tab sends the newest cookie.
6. **Suspended accounts.** 403 responses caused by a ban carry `X-Error-Code: account_suspended`. `apiClient.ts` passes only those to `AuthContext`, which clears the session, shows the reason and redirects to `/login`. Ordinary 403s (missing permissions) never sign the user out.
7. **Brute force.** Failures are counted per (account, IP) (5), per IP (20) and per account (50) over 15 minutes. Throttled requests are not counted. A stranger who knows your email can therefore not lock you out from your own network. Signup is limited to 10 per IP per hour.
8. **RBAC.** Routes declare `require_permission(Permission.X)`, and `ROLE_PERMISSIONS` decides which role holds which permission. Account-type capabilities (owning a tutor profile) use `require_account_type`.
9. **Ownership and IDOR**
   - Services load each resource **through** the caller's ownership or membership.
   - Personal records, sessions and private groups return 404 to everyone else.
   - Tutor profiles are public, so editing someone else's returns 403.
10. **Admin restrictions**
   - An admin cannot change their own role, and cannot ban themself or another admin.
   - Banning revokes all sessions, and `get_current_user` refuses banned accounts on the next request.
   - Every admin mutation is audited, and unbanning (single or bulk) requires a reason.
11. **Admin bootstrap.** `scripts/create_admin.py` takes the password at a hidden prompt. An existing admin can also promote a user in the dashboard.

---

## 6. Implementation details
- **Preserved from the mid-term:**
  - the tutor CRUD contract (paths, PUT semantics, status codes, every validation rule and message);
  - the accessible form components (`FormField`, `SearchableSelect`, `MultiSelect`, `ConfirmDialog`, `ImageUpload`);
  - the runtime response validation in `tutorService.ts`;
  - the Supabase and psycopg configuration;
  - `vercel.json`.
- **Fixed:**
  - the API base-URL bug (`/tutors` vs `/api/tutors`): services now call `/api/...` on the same origin, and the Vite dev proxy forwards `/api`;
  - the template README;
  - the flash messages stored in `location.state` (now toasts);
  - client-side-only filtering of tutors.
- **Removed:** the template `/api/hello` endpoint.
- **Content-Security-Policy:** the API sends `default-src 'none'` (the docs pages are excluded). The production build of the React app gets a `<meta>` policy from `frontend/csp.ts`: `script-src 'self'`, Google Fonts, HTTPS images, `connect-src 'self'`. The dev server has no policy, so hot reloading works.
- **Dependencies:**
  - `backend/requirements.txt` pins the tested versions;
  - `backend/requirements-dev.txt` adds pytest and pytest-cov;
  - `pyproject.toml` declares `requires-python >= 3.11`, because the code uses `StrEnum`.
- **New dependencies:**
  - backend: `PyJWT`, `argon2-cffi`;
  - frontend (dev only): `vitest`, `@testing-library/*`, `jsdom`, `@types/node`.
- **Password reset and email:**
  - `email_service.py` provides `smtp` (production) and `outbox` (local `.eml` files, refused on Vercel) backends with standard-library `smtplib`.
  - Without a backend, reset is reported as unavailable (HTTP 503 for every email) instead of pretending.
  - The reset link carries the token in the URL fragment, so it never reaches server logs.
  - The frontend adds `/forgot-password` and `/reset-password`, and a reusable `PasswordInput` with an accessible eye toggle used on every password field.
- **Timestamps:** every timestamp column uses `UtcDateTime`. It stores UTC and returns timezone-aware UTC on both PostgreSQL and SQLite, so the API always sends an explicit offset. Before this fix, SQLite returned naive values and browsers read them as local time, 6 hours off in Bangladesh. The frontend formats times with `Intl` in the viewer's timezone and treats any offset-less value as UTC.
- **Browser identification:** Brave is recognised from the `Sec-CH-UA` client hint, with the frontend's `navigator.brave.isBrave()` (header `X-Client-Brand`) as a fallback, and recorded as a `Brave` token in the stored user agent. Chrome, Edge, Opera, Firefox and Safari are told apart in that order; anything else is "Unknown browser".
- **Accessibility fix:** `ConfirmDialog` and `PromptDialog` now generate unique element ids (`useId`). Before, two dialogs on one page shared ids, so a "Reason" label could point at the wrong box.

---

## 7. Testing strategy
- **Backend:** `python -m pytest tests` (or `python -m unittest discover -s tests -t . -v`). The real FastAPI app runs on a fresh in-memory SQLite database per test, with foreign keys enabled. Supabase is never touched.

  | Module | Covers |
  |---|---|
  | `test_tutors_api.py` | Mid-term regression tests, updated for authentication, plus server-side filters |
  | `test_auth.py` | Signup (admin rejected, hashing, pepper), login, generic failures, banned login, logout, CSRF header, password change, profile |
  | `test_tokens.py` | Missing, garbage, tampered, wrong-key, `alg=none` and expired JWTs; revoked session; outdated role; banned user |
  | `test_sessions.py` | Rotation, reuse after the grace window revokes the session, concurrent refresh within the window keeps it, logout is never revived, cookie cleared, banned refresh, session list and cross-user revocation |
  | `test_rate_limit.py` | Per-(account, IP) lockout; the owner can still log in from another network; hammering cannot build a global lockout; per-IP and distributed caps; signup limit |
  | `test_group_permissions.py` | Each permission alone (create / update / assign), owner authority, derived labels, only the owner changes permissions, assignee status-only updates, delete rules, immediate revocation, audit of permission changes |
  | `test_config.py` | Settings parsing, secret length checks without leaking values, the 15-minute cap, cookie/proxy flags, CORS, the SQLite and PostgreSQL engine settings |
  | `test_rbac.py` | **Every** protected route gives 401 without a token; **every** admin route gives 403 for users; permission map; generic 500; security headers; docs |
  | `test_tutor_ownership.py` | Account link, tutor-only creation, one profile each, cross-tutor 403, student read-only, admin moderation (audited), legacy profiles |
  | `test_groups.py` / `test_records.py` | Owner, editor, viewer and outsider rules, membership management, assignment rules, personal-record IDOR, cascades, DB constraints |
  | `test_admin_users.py` / `test_admin_content.py` | Overview, filters, pagination, detail, ban/unban (missing, empty, short and long reasons rejected; the reason is audited), suspended-response tagging, admin restrictions, role change, bulk actions, session revocation, moderation |
  | `test_audit.py` / `test_exports.py` | Sanitisation, IP and user agent, search including user email and details combined with filters, failed-login report, CSV filters, CSV-injection escaping, export auditing, admin-only access |
  | `test_rbac.py` (additions) | API CSP header present on JSON and error responses, absent on the docs pages |

- **Frontend:** `npm run test` (Vitest + Testing Library, 35 tests) covers:
  - dashboard routing, safe redirects, password, email and name rules;
  - the route guards and the role-based sidebar menu;
  - session restore with a single refresh request, guest fallback, refresh-and-retry;
  - **suspended accounts are signed out while ordinary 403s are not**;
  - the group page showing only the controls each permission allows, with the owner's per-member toggles;
  - the record form never sending an assignee without assign permission;
  - the admin restrictions in the UI and the required unban reason;
  - the frontend CSP.

  `npm run build` type-checks the whole app.
- **Manual:** [`docs/MANUAL_TEST_CHECKLIST.md`](docs/MANUAL_TEST_CHECKLIST.md) covers every page and role, responsive widths, cookies and console errors.
- **Live:** `tests/live_smoke_test.py` runs read-only checks against a running deployment, plus the login → refresh → logout cycle.

---

## 8. Deployment
- Vercel serves the SPA, and `/api/*` is rewritten to the FastAPI service (the same origin), so the `SameSite=Strict` cookie works.
- Production environment variables: `DATABASE_URL` (Supabase transaction pooler, port 6543), `JWT_SECRET_KEY`, `PASSWORD_PEPPER`, `CORS_ORIGINS`, `COOKIE_SECURE=true`. `TRUST_PROXY_HEADERS` is turned on automatically by `VERCEL=1`.
- Order:
  1. back up the database;
  2. run `alembic upgrade head`;
  3. run `scripts/create_admin.py` / `scripts/seed_demo.py`;
  4. deploy;
  5. run the smoke test.
- The production bundle contains no `localhost` URLs (checked with `grep` on `frontend/dist`).

---

## 9. Verification status (honest record)

| Check | Status |
|---|---|
| Frontend tests (`npm run test`) | ✅ 65/65 passed (17 files), 24 Nov 2026 |
| Frontend type-check and production build | ✅ passed; the CSP `<meta>` is present in `dist/index.html`; no `localhost` in the bundle |
| Backend automated test suite (`python -m pytest tests`, also run with unittest) | ✅ 191 passed + 168 subtests (Python 3.14, pinned dependencies, in-memory SQLite); **98% line coverage** |
| Password reset end-to-end on an isolated server with a throwaway database and the `outbox` backend | ✅ 11/11: generic reply, one email only for the real account, weak password refused, reset succeeds, token not reusable, old access and refresh tokens rejected, old password fails, new one works; no token in the server log |
| Migration 0007: offline PostgreSQL SQL, throwaway SQLite rehearsal (upgrade → downgrade → upgrade), applied to the local dev DB after a backup | ✅ |
| End-to-end HTTP workflow on an isolated backend with a throwaway database | ✅ 29/29 checks: demo logins, independent group permissions, ban → suspended tag → required unban reason, audit email search, concurrent refresh, CSP, throttle |
| Migration 0006 offline SQL (PostgreSQL) | ✅ renders correctly, for both upgrade and downgrade |
| Migration 0006 rehearsal on a throwaway SQLite copy of the dev data (upgrade → downgrade → upgrade, plus a downgrade with a custom `member` row) | ✅ every row preserved; backfill correct; integrity and foreign-key checks clean |
| Migration 0006 applied to the local dev database (after a backup) | ✅ existing groups and memberships preserved |
| Migration SQL rendered offline (`alembic upgrade head --sql`, no DB connection) | ✅ renders without errors. The only change to `tutors` is `ADD COLUMN user_id` + FK + UNIQUE. No DROP, DELETE, TRUNCATE or data UPDATE statements (only Alembic's own version bookkeeping). The downgrade path also renders. |
| Migration rehearsal on a disposable PostgreSQL (upgrade → downgrade → upgrade) | ⏳ pending: no local PostgreSQL or Docker on the development machine; use a scratch Supabase project or Docker, never the production database |
| Production migrations, demo seeding, deployment | ⏳ waiting for the owner's approval |
| Manual checklist | ⏳ to be completed against the running app |

**Risks and notes:**
- The 10-second refresh grace window is a deliberate trade-off: a token stolen and used within 10 seconds of its rotation would get a fresh token. After that, reuse revokes the session.
- The login throttle is stored in the database. It is shared across serverless instances but adds a few count queries per login. An attacker controlling more than 10 IP addresses could still lock one account for 15 minutes.
- The frontend CSP is set with a `<meta>` tag, which cannot enforce `frame-ancestors`. The API sends `X-Frame-Options: DENY`.
- No real PostgreSQL rehearsal was possible locally (no Docker or PostgreSQL). Rehearse on a scratch Supabase project before production.
- Changing `PASSWORD_PEPPER` invalidates every password.

---

## 10. Screenshots to capture for the PDF

1. Homepage (hero and all sections; desktop and mobile)
2. Signup (Student/Tutor choice) and login
3. Student dashboard and Tutor dashboard
4. Tutor directory with filters; tutor profile (public view and owner view)
5. Study group detail as owner (per-member Create/Update/Assign toggles), as a create-only member and as a viewer (different controls); outsider sees "Group not found"
6. Account settings: active sessions
7. Admin overview; user list with filters and bulk bar; user detail (sessions, activity, ban dialog)
8. Content moderation; activity log with filters; security monitoring
9. A downloaded CSV export opened in a spreadsheet
10. `/api/docs`
11. Terminal output of the backend and frontend test runs
12. The Vercel deployment and its environment-variable *names* (values hidden)
