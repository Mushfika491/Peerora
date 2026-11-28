<div align="center">

Independent University, Bangladesh
CSE309 – Web Application & Internet

# Final Project Submission Report

## Peerora: A University Peer Learning and Tutoring Platform

</div>

**Submitted by:**

| Field | Value |
|---|---|
| Name | Mushfika Ali Ema |
| Student ID | 2230049 |
| Section | 05 |
| Project Title | Peerora: A University Peer Learning and Tutoring Platform |
| Vercel URL | <https://peerora-uni.vercel.app/> |
| GitHub Repository | <https://github.com/Mushfika491/Peerora> |

**Submitted to:**
Sayef Reyadh
Adjunct Lecturer
Department of Computer Science & Engineering
Independent University, Bangladesh

**Course:** CSE309 – Web Application & Internet
**Semester:** Autumn 2026
**Date of Submission:** 28 November 2026

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
  - [1.1 Project overview](#11-project-overview)
  - [1.2 What was built since the mid assessment](#12-what-was-built-since-the-mid-assessment)
  - [1.3 Live links](#13-live-links)
- [Part A. Product Requirements (PRD)](#part-a-product-requirements-prd)
  - [A1. Problem Statement](#a1-problem-statement)
  - [A2. Users and Roles](#a2-users-and-roles)
  - [A3. Goals and Success Measures](#a3-goals-and-success-measures)
  - [A4. Scope and Non-Goals](#a4-scope-and-non-goals)
  - [A5. User Stories](#a5-user-stories)
- [Part B. Software Requirements (SRS)](#part-b-software-requirements-srs)
  - [B1. Introduction](#b1-introduction)
  - [B2. Functional Requirements](#b2-functional-requirements)
  - [B3. Non-Functional Requirements](#b3-non-functional-requirements)
  - [B4. Roles and Permission Matrix](#b4-roles-and-permission-matrix)
  - [B5. Use Cases](#b5-use-cases)
  - [B6. Acceptance Criteria](#b6-acceptance-criteria)
  - [B7. Traceability Matrix](#b7-traceability-matrix)
- [Part C. Technical Design (TDD)](#part-c-technical-design-tdd)
  - [C1. Technology Stack](#c1-technology-stack)
  - [C2. System Architecture](#c2-system-architecture)
  - [C3. Backend and Frontend Structure](#c3-backend-and-frontend-structure)
  - [C4. Data Model](#c4-data-model)
  - [C5. API Design](#c5-api-design)
  - [C6. JWT Authentication Design](#c6-jwt-authentication-design)
  - [C7. RBAC Design](#c7-rbac-design)
  - [C8. Admin Dashboard Design](#c8-admin-dashboard-design)
  - [C9. Security Design and Threats](#c9-security-design-and-threats)
  - [C10. Deployment on Vercel](#c10-deployment-on-vercel)
  - [C11. Testing](#c11-testing)
- [Part D. Evidence: Screenshots of the Running Application](#part-d-evidence-screenshots-of-the-running-application)
- [Part E. Project Management and Conclusion](#part-e-project-management-and-conclusion)
  - [E1. How to Run and Test](#e1-how-to-run-and-test)
  - [E2. GitHub Work](#e2-github-work)
  - [E3. Limitations](#e3-limitations)
  - [E4. Future Work](#e4-future-work)
  - [E5. Sources, Libraries and Tools](#e5-sources-libraries-and-tools)

### List of Figures

| No. | Caption | Section |
|---|---|---|
| Figure 1 | Use case diagram | B5 |
| Figure 2 | System architecture | C2 |
| Figure 3 | Entity-relationship diagram | C4 |
| Figure 4 | JWT lifecycle sequence diagram | C6 |
| Figure 5 | Authorisation flow for one request | C7 |
| Figure 6 | Admin pages and the endpoints they call | C8 |
| Figure 7 | Deployment layout | C10 |

### List of Tables

| No. | Caption | Section |
|---|---|---|
| Table 1 | Live links | 1.3 |
| Table 2 | Users and roles | A2 |
| Table 3 | Goals and success measures | A3 |
| Table 4 | User stories | A5 |
| Table 5 | Functional requirements: authentication (FR-AUTH) | B2 |
| Table 6 | Functional requirements: RBAC (FR-RBAC) | B2 |
| Table 7 | Functional requirements: admin (FR-ADM) | B2 |
| Table 8 | Functional requirements: domain (FR-DOM) | B2 |
| Table 9 | Non-functional requirements | B3 |
| Table 10 | Endpoint groups by role | B4 |
| Table 11 | Group permissions | B4 |
| Table 12 | Admin rules | B4 |
| Table 13 | Use case descriptions | B5 |
| Table 14 | Acceptance criteria | B6 |
| Table 15 | Traceability matrix | B7 |
| Table 16 | Technology stack | C1 |
| Table 17–26 | Database tables and columns | C4 |
| Table 27 | API endpoint list | C5 |
| Table 28 | Access token claims | C6 |
| Table 29 | Admin pages, endpoints, filters, actions and audit events | C8 |
| Table 30 | Threats, defences and code locations | C9 |
| Table 31 | Environment variables | C10 |
| Table 32 | Automated test results | C11 |
| Table 33 | GitHub pull requests | E2 |
| Table 34 | Sources, libraries and tools | E5 |

### List of Screenshots

Screenshots S1–S21 are listed in [Part D](#part-d-evidence-screenshots-of-the-running-application). They are added to the PDF version of this report. Page numbers are assigned in the PDF.

---

## 1. Executive Summary

### 1.1 Project overview

**Peerora** is a web platform for university students. Students use it to find peer tutors and to organise group study. Students and tutors can create private **study groups**. In each group, the owner decides what every member is allowed to do with shared **study records** (tasks and notes): create them, update them, or assign them. Tutor accounts publish one public **tutor profile** in a searchable directory. Every user can also keep private personal records. **Administrators** use a separate dashboard. In it they manage accounts (including bans and role changes), moderate groups and records, read a complete activity log, monitor failed logins and export data as CSV. The users are IUB students (account type *Student*), students who tutor (account type *Tutor*) and platform administrators (security role *admin*).

**Stack:** React 18 + TypeScript + Vite (frontend) · FastAPI + SQLAlchemy 2 + Pydantic + Alembic (backend) · Supabase PostgreSQL (database) · Vercel (hosting).

### 1.2 What was built since the mid assessment

The mid assessment delivered an unauthenticated tutor-profile CRUD MVP (PR #5). The final version adds the following:

- **JWT authentication with refresh and logout.** Signup, login, a 15-minute HS256 access token held in memory, a rotating refresh token in an `HttpOnly` cookie with reuse detection, logout, an active-session list with per-device revocation, password change and a forgotten-password flow.
- **Role-based access control.** Two independent attributes: the security role (`user`/`admin`) and the account type (`student`/`tutor`). A central permission map (`core/permissions.py`), reusable FastAPI dependencies, ownership checks inside queries, and per-member group permissions (`can_create_records`, `can_update_records`, `can_assign_records`).
- **Admin dashboard.** Overview statistics, a user list with search, filters, pagination and bulk ban/unban, a user detail page (sessions, groups, records, activity), moderation of records and groups, the activity log, a security view of failed logins, and CSV exports that follow the active filters.
- **Audit logging, brute-force protection and deployment.** 22 audit event types with secrets stripped out, login throttling per (account, IP), per IP and per account, signup and password-reset rate limits, security headers and a CSP. Deployment is configured for Vercel (`vercel.json`) with the Supabase PostgreSQL database.

### 1.3 Live links

**Table 1: Live links**

| Resource | Link |
|---|---|
| GitHub repository | <https://github.com/Mushfika491/Peerora> |
| Hosting platform | Vercel |
| Vercel frontend | <https://peerora-uni.vercel.app/> |
| API base | <https://peerora-uni.vercel.app/api> (served on the same origin as the frontend) |
| API docs (Swagger UI) | <https://peerora-uni.vercel.app/api/docs> (ReDoc at <https://peerora-uni.vercel.app/api/redoc>) |
| Database hosting | Supabase (PostgreSQL) |
| Video demo | <https://youtu.be/7jwnrHsJEKQ> |

Test account user IDs and passwords are **not** in this file. They are in the PDF report (Appendix).

---

## Part A. Product Requirements (PRD)

### A1. Problem Statement

University students who struggle with a course often have no structured way to find a classmate or senior who can explain the subject. Today they ask around in Facebook groups, Messenger or WhatsApp. They cannot see who actually knows the course, which department and semester that person is in, or whether they tutor online or in person. Finding help therefore depends on who you happen to know.

Group study has the same problem. Tasks and notes are scattered across chat threads. Nobody can tell who is responsible for which task or what is done. Anyone in the chat can edit or delete shared information, and nothing records who changed what. For a platform that holds student data, there is a further need: accounts must be protected, a misbehaving account must be stopped quickly, and administrators must be able to see what happened.

### A2. Users and Roles

**Table 2: Users and roles**

| Role | Who they are | Main tasks | Must never be able to |
|---|---|---|---|
| Visitor | Anyone who is not signed in | Browse the home page, the tutor directory and public tutor profiles; sign up; log in; request a password reset | Read or change any private data, see a tutor's Student ID, call any authenticated or admin endpoint (401) |
| User (Student account) | A signed-in student, security role `user` | Manage own profile, password and sessions; create study groups; keep personal records; work in groups according to the permissions given | Create a tutor profile (403), read another user's personal records (404), see groups they are not in (404), reach `/api/admin/*` (403), choose or change their own role |
| User (Tutor account) | A signed-in tutor, security role `user` | Everything a Student can do, plus create and manage **one** tutor profile | Edit or delete another tutor's profile (403), own more than one profile (409), reach admin endpoints (403) |
| Group member | A user added to a group by its owner | Read the group, members and shared records; create, update or assign records only if the owner granted that permission; update the status of records assigned to them; leave the group | Rename or delete the group, add or remove members, change anyone's permissions (403), act without the needed permission (403) |
| Group owner | The user who created the group | All member permissions, plus rename/edit/delete the group, add members by email, set each member's three permissions, remove members, delete any record in the group | Leave their own group (403, they must delete it instead), have their owner role changed |
| Admin | Any Student or Tutor account whose security role is `admin` | View statistics; manage users (ban, unban, role change, session revocation, bulk actions); moderate records, groups and tutor profiles; read the audit log and the security view; export CSV | Change their own role (403), ban themself or another admin (403), act inside a group they are not a member of (404), have the role granted through signup |

### A3. Goals and Success Measures

**Table 3: Goals and success measures**

| ID | Goal | Measure (testable) |
|---|---|---|
| G1 | Students can find a suitable tutor quickly | The directory filters by text, subject, department and teaching mode on the server and returns a page of at most 100 results with an `X-Total-Count` header (yes/no: `test_server_side_search_and_filters` passes) |
| G2 | Group work has clear responsibility | Every shared record has a status (`todo`/`in_progress`/`done`) and at most one assignee, who must be a group member (yes/no: `test_assign_only_to_members` passes) |
| G3 (security) | No user can read another user's private data | 100 % of cross-user attempts on personal records, private groups and sessions return 404 (`test_personal_records_are_private`, `test_non_members_cannot_see_anything`, `test_cannot_revoke_another_users_session` pass) |
| G4 (security) | Sessions are short-lived and revocable | Access tokens live ≤ 15 minutes (capped in code); revoking a session, logging out, banning or changing a role makes the next request with the old token fail with 401/403 (`test_token_for_revoked_session_returns_401`, `test_banned_user_is_rejected_on_next_request`, `test_role_change_takes_effect_immediately` pass) |
| G5 (security) | Password guessing is impractical | The 6th wrong password within 15 minutes from the same IP for the same account gets HTTP 429 (`test_account_is_throttled_from_the_attacking_address` passes) |
| G6 | Administrators can see and act on what happened | Every ban, unban, role change, deletion, login (success and failure), logout, password change and export creates an audit row with actor, target, IP, user agent and UTC time (`test_ban_requires_reason_revokes_sessions_and_is_audited`, `test_exports_are_audited`, `test_login_events_record_ip_user_agent_and_time` pass) |

### A4. Scope and Non-Goals

**In scope (implemented):**

1. Authentication: signup (Student or Tutor), login, logout, session restore on reload, profile update, password change, active-session list and revocation, forgotten-password reset by email.
2. JWT access tokens and rotating refresh tokens with reuse detection.
3. RBAC: security role separated from account type, a central permission map, ownership checks, group-level permissions.
4. Tutor directory and tutor profiles (one per Tutor account, owner-only editing, private Student ID).
5. Study groups with per-member create/update/assign permissions, and shared and personal study records.
6. Student, Tutor and Admin dashboards.
7. Admin dashboard: overview, users, user detail, content moderation, activity log, security view, CSV exports, bulk actions.
8. Audit logging, brute-force and rate-limit protection, security headers and CSP.
9. Deployment configuration for Vercel with Supabase PostgreSQL.

**Out of scope (deliberately not built):**

| Item | Reason |
|---|---|
| Booking sessions, availability slots, payments | Planned in the original PRD, replaced by study groups and records because the final brief asks for groups with permissions |
| Chat, video calls, notifications | Need real-time infrastructure that does not fit serverless hosting or the time available |
| Study-material file uploads and real profile-picture storage | Need object storage. The `ImageUpload` component exists, but the upload is a disabled stub (`services/imageService.ts`) |
| Email verification at signup | Not required by the brief. Email delivery is used only for password reset |
| A "super admin" tier | Two roles are enough for the brief. See the admin rules in B4 |

**Assumptions and constraints:**

- Modern evergreen browsers (Chrome, Edge, Firefox, Safari, Brave). The frontend uses the Web Locks API when it is available and falls back to a single in-tab refresh when it is not.
- Hosting is Vercel serverless functions. There is no long-lived process, so throttling state is kept in the database, not in memory.
- The database is Supabase PostgreSQL reached through its connection pooler. Prepared statements are turned off for pooler compatibility (`database.py`).
- Python 3.11+ is required (`enum.StrEnum`). Development and testing used Python 3.14.4 and Node.js with the versions in C1.
- One developer, one semester. Submission deadline 28 November 2026.

### A5. User Stories

**Table 4: User stories**

| ID | Role | Story |
|---|---|---|
| US-01 | Visitor | As a visitor, I want to sign up as a Student or a Tutor so that I get the right experience without being able to make myself an admin. |
| US-02 | User | As a user, I want to stay signed in after reloading the page and to log out on a shared computer, so that my account is convenient and safe. |
| US-03 | User | As a user, I want to see my active sessions and revoke one, so that I can end a session on a device I lost. |
| US-04 | User | As a user, I want to change my password with my current password, and have my other devices signed out, so that a leaked password stops working everywhere. |
| US-05 | Visitor | As a visitor, I want to search tutors by subject, department and teaching mode so that I can find help for a specific course. |
| US-06 | Tutor | As a tutor, I want to publish and edit my own profile, and be sure nobody else can change it, so that my information stays correct. |
| US-07 | Group owner | As a group owner, I want to give each member create, update and assign permissions separately, so that I control who changes our shared work. |
| US-08 | Group member | As a member without update permission, I want to still move a task assigned to me to "done", so that I can report progress without editing others' work. |
| US-09 | User | As a user, I want my personal records and groups to be invisible to everyone else, so that my study notes stay private. |
| US-10 | Group member | As a group member, I want to leave a group I no longer need, so that it disappears from my dashboard. |
| US-11 | Admin | As an admin, I want to search and filter users and ban one with a reason, so that an abusive account is stopped on its next request. |
| US-12 | Admin | As an admin, I want to read the activity log with filters, so that I can see who did what and when. |
| US-13 | Admin | As an admin, I want to see failed logins grouped by IP and by account, so that I can spot a brute-force attempt. |
| US-14 | Admin | As an admin, I want to export users, records and the activity log as CSV using the filters on screen, so that I can report on the platform. |
| US-15 | Admin | As an admin, I want to bulk-delete inappropriate records or groups and see how many were deleted or skipped, so that moderation is fast and transparent. |

---

## Part B. Software Requirements (SRS)

### B1. Introduction

**Purpose.** This part specifies exactly what the Peerora system does, as implemented in the repository at commit `09873b3`. Each requirement has an ID that is reused in the tests (C11), the traceability matrix (B7) and the screenshots (Part D).

**Intended readers.** The course instructor and examiners, the developer (for the viva and future maintenance), and anyone who wants to deploy or extend the system.

**Definitions**

| Term | Meaning in Peerora |
|---|---|
| JWT | JSON Web Token (RFC 7519): a signed, base64url-encoded set of claims. Peerora signs with HS256. |
| Access token | Short-lived JWT (≤ 15 min) sent as `Authorization: Bearer <token>` on every protected request. Kept in JavaScript memory only. |
| Refresh token | Random 256-bit value (`secrets.token_urlsafe(32)`) sent only as the `HttpOnly` cookie `peerora_refresh`. The server stores only its SHA-256 hash. Exchanged at `/api/auth/refresh` for a new access token and a new refresh token (rotation). |
| Session | One signed-in device (`user_sessions` row). Its UUID is the `sid` claim in every access token, so revoking it ends access immediately. |
| RBAC | Role-based access control: permissions are attached to roles, and users get permissions through their role. |
| Role | The security role: `user` or `admin` (`users.role`). Separate from the account type (`student`/`tutor`). |
| Account type | `student` or `tutor`. Decides the application experience (dashboard, ability to own a tutor profile), not admin rights. |
| Permission | A named capability in the `Permission` enum (`core/permissions.py`), e.g. `user:ban`. |
| Group permission | One of three per-member booleans in `group_memberships`: `can_create_records`, `can_update_records`, `can_assign_records`. |
| Audit log | The append-only `audit_logs` table of security-relevant events, with actor, target, IP, user agent and time. |
| Pepper | Server-side secret (`PASSWORD_PEPPER`) mixed into every password with HMAC-SHA256 before Argon2id hashing. |

**References**

- RFC 7519, *JSON Web Token (JWT)*; RFC 8725, *JWT Best Current Practices*.
- RFC 9106, *Argon2 Memory-Hard Function*.
- OWASP Application Security Verification Standard (ASVS) 4.0: V2 Authentication, V3 Session Management, V4 Access Control.
- OWASP Cheat Sheets: Password Storage, Session Management, CSRF Prevention, CSV Injection.
- FastAPI documentation (security, dependencies), SQLAlchemy 2.0 documentation, Alembic documentation, Vercel and Supabase documentation.

### B2. Functional Requirements

**Table 5: Functional requirements: authentication (FR-AUTH)**

| ID | Requirement |
|---|---|
| FR-AUTH-01 | The system shall let a visitor sign up with full name, email, password and account type `student` or `tutor`, always assigning role `user` and rejecting any extra field such as `role` with 422 (`SignupIn`, `extra="forbid"`). |
| FR-AUTH-02 | The system shall enforce the password policy on the backend: 8–128 characters, at least one letter and one digit, and not equal to the email (`schemas/common.check_password_strength`). |
| FR-AUTH-03 | The system shall store passwords only as Argon2id hashes of `HMAC-SHA256(PASSWORD_PEPPER, password)` (`core/security.hash_password`). |
| FR-AUTH-04 | The system shall reply to every failed login with the same message, "Incorrect email or password." (401), and spend one hash check even for unknown emails (`burn_password_check_time`). |
| FR-AUTH-05 | The system shall issue an HS256 access token with the claims `sub`, `role`, `sid`, `type`, `iss`, `iat` and `exp`, valid for `ACCESS_TOKEN_MINUTES` (default 15), never more than 15 minutes (`config.get_access_token_minutes`). |
| FR-AUTH-06 | The system shall, on every protected request, verify the token signature, algorithm, issuer, required claims and expiry, that the user exists and is not banned, that the session is live and belongs to the user, and that the token role equals the database role (`core/dependencies.get_current_user`). |
| FR-AUTH-07 | The system shall set the refresh token only as the cookie `peerora_refresh` (`HttpOnly`, `Secure` in production, `SameSite=Strict`, `Path=/api/auth`, 7 days), and rotate it on every `/api/auth/refresh`. |
| FR-AUTH-08 | The system shall revoke the whole session and write `token_reuse_detected` when an already-used refresh token is presented again, except within 10 seconds of its rotation on a still-live session (concurrent tabs). |
| FR-AUTH-09 | The system shall, on logout, revoke the current session, write a `logout` audit event and delete the refresh cookie (204). |
| FR-AUTH-10 | The system shall require the header `X-Requested-With: peerora` on `/api/auth/refresh` and `/api/auth/logout`, returning 403 without it. |
| FR-AUTH-11 | The system shall list the user's own active sessions (IP, user agent, created, last used, expires, current flag) and let the user revoke one; another user's session id shall return 404. |
| FR-AUTH-12 | The system shall return 429 with `Retry-After` when, within 15 minutes, there are ≥ 5 wrong passwords for the (account, IP) pair, ≥ 20 from the IP, or ≥ 50 for the account. Throttled attempts shall not be counted as guesses. |
| FR-AUTH-13 | The system shall limit successful signups to 10 per IP per hour (429). |
| FR-AUTH-14 | The system shall let a user update their full name and email. An email change shall require the current password (400 otherwise) and be unique (409). Role and account type shall not be changeable (422). |
| FR-AUTH-15 | The system shall change the password only when the current password is correct (400 otherwise) and the new one differs, and shall revoke every other session of the user. |
| FR-AUTH-16 | The system shall offer a forgotten-password flow: a generic reply for every email, a hashed single-use token valid for 30 minutes, the link sent by email, the new password checked against the policy, all sessions ended on success, rate limits (5 requests per IP and 3 emails per account per hour), and 503 when no email backend is configured. |
| FR-AUTH-17 | The frontend shall restore the session on page load by calling `/api/auth/refresh`, and on a 401 response shall refresh once and retry the request, clearing the session if the refresh fails. |

**Table 6: Functional requirements: RBAC (FR-RBAC)**

| ID | Requirement |
|---|---|
| FR-RBAC-01 | The system shall define two security roles, `user` and `admin`, with permissions assigned only in `ROLE_PERMISSIONS` (`core/permissions.py`). Admins hold every permission. |
| FR-RBAC-02 | The system shall enforce every authorisation decision on the server. Frontend guards are for usability only. |
| FR-RBAC-03 | The system shall return 401 for every protected endpoint called without a valid token. |
| FR-RBAC-04 | The system shall return 403 for every `/api/admin/*` endpoint called by a non-admin. |
| FR-RBAC-05 | The system shall make personal study records visible only to their creator. Others shall receive 404. |
| FR-RBAC-06 | The system shall let only Tutor accounts create a tutor profile (403 otherwise), at most one per account (409), and let only the owner or an admin update or delete it (403 otherwise). |
| FR-RBAC-07 | The system shall return 404 for a study group, its members and its records to any user who is not a member, including admins. |
| FR-RBAC-08 | The system shall make the group creator the owner with all permissions. |
| FR-RBAC-09 | The system shall require `can_create_records` to create, `can_update_records` to edit and `can_assign_records` to set or change the assignee of a shared record (403 otherwise). |
| FR-RBAC-10 | The system shall always allow the assignee of a shared record to change only its status, even without `can_update_records`. |
| FR-RBAC-11 | The system shall let only the group owner rename/edit/delete the group, add members, change member permissions and remove other members. The owner's role shall not be changeable and the owner shall not be able to leave. |
| FR-RBAC-12 | The system shall prevent an admin from changing their own role and from banning themself or another admin (403). |
| FR-RBAC-13 | The system shall reject a banned user's next request with 403 and the header `X-Error-Code: account_suspended`, and shall refuse their login and refresh. |
| FR-RBAC-14 | The system shall refuse an access token whose `role` claim differs from the database role (401), so a role change takes effect on the next request. |
| FR-RBAC-15 | The system shall apply a change to a member's group permissions on that member's next request. |

**Table 7: Functional requirements: admin (FR-ADM)**

| ID | Requirement |
|---|---|
| FR-ADM-01 | The system shall show admins overview statistics: total, banned and admin users, records, groups, tutor profiles, and new users in the last 7 days. |
| FR-ADM-02 | The system shall list users with search on email or name (`q`), filters on role, account type and status (active/banned), and pagination (`page`, `page_size` ≤ 100). |
| FR-ADM-03 | The system shall show a user detail view with the user's tutor profile id, groups, records (up to 20, plus a count), active sessions and the 20 most recent audit events. |
| FR-ADM-04 | The system shall ban and unban a user only with a reason of 3–500 characters, store the ban reason, time and admin, revoke all sessions on ban, and audit both actions. A repeated ban or unban shall return 409. |
| FR-ADM-05 | The system shall let an admin change another user's role between `user` and `admin` and audit the change. |
| FR-ADM-06 | The system shall let an admin revoke one or all sessions of a user, audited. |
| FR-ADM-07 | The system shall bulk-ban and bulk-unban up to 100 users with one reason, returning a per-user result (`done`, `not_found`, `skipped_self`, `skipped_admin`, `already_done`) and the count `done`. |
| FR-ADM-08 | The system shall list all records (filters: `q` on title or creator email, `status`, `group_id`, `scope` personal/group) and all groups (`q` on name or owner email) with pagination, show a group's detail, and delete records or groups singly or in bulk (≤ 100) with per-item results, audited. |
| FR-ADM-09 | The system shall show the activity log, newest first, with filters on text (`q` matching action, IP, user agent, details, actor or target email), `action`, `user_id` (actor or target) and a date range, with pagination (default 25). |
| FR-ADM-10 | The system shall show failed logins in the last N hours (1–720, default 24) grouped by IP and by account (top 20 each), plus the 50 most recent failures. |
| FR-ADM-11 | The system shall export users, records and the activity log as CSV using the same filters as the matching list, cap exports at 10 000 rows, escape spreadsheet formula prefixes and audit each export with its filters and row count. |
| FR-ADM-12 | The system shall never store keys containing `password`, `token`, `secret`, `hash`, `pepper`, `cookie` or `authorization` in audit details (`audit_service.sanitize`). |
| FR-ADM-13 | The system shall let an admin link a tutor profile to a Tutor account or unlink it, refusing Student accounts (422) and accounts that already own a profile (409). |

**Table 8: Functional requirements: domain (FR-DOM)**

| ID | Requirement |
|---|---|
| FR-DOM-01 | The system shall publish a tutor directory, newest first, with server-side search (`q`), filters (subject, department, teaching mode) and `limit`/`offset` pagination, returning the total in `X-Total-Count`. |
| FR-DOM-02 | The system shall validate tutor profiles (7-character unique Student ID, department and subjects from fixed lists, semester 1–24, CGPA 0–4, etc.) and show the Student ID only to the owner and admins. |
| FR-DOM-03 | The system shall let any signed-in user create a study group (name 2–100 characters, optional description and subject) and list the groups they belong to. |
| FR-DOM-04 | The system shall let the owner add an existing, non-banned user by email with a preset (`editor` = all three permissions, `viewer` = none) and/or individual permissions, and shall derive the label `editor`, `viewer` or `member` from the booleans. |
| FR-DOM-05 | The system shall let permitted members create shared records (title, details, status, due date, assignee). An assignee must be a group member (422 otherwise). |
| FR-DOM-06 | The system shall let a user create, edit and delete personal records, assignable only to themself. |
| FR-DOM-07 | The system shall unassign a departing member's records when they leave or are removed, and cascade-delete a group's memberships and records when the group is deleted. |
| FR-DOM-08 | The system shall provide a dashboard summary: the user's groups, record counts by status, open records assigned to them, open personal records and their tutor profile id. |
| FR-DOM-09 | The frontend shall send users after login to `/admin` (admins), `/dashboard/tutor` or `/dashboard/student`. |

### B3. Non-Functional Requirements

**Table 9: Non-functional requirements**

| ID | Category | Requirement | How it is met / measured |
|---|---|---|---|
| NFR-01 | Security | All secrets come from environment variables. The API refuses to start if `JWT_SECRET_KEY` (< 32 chars) or `PASSWORD_PEPPER` (< 16 chars) is missing, without printing the value. | `config.validate_required_secrets`, `test_app_refuses_to_start_without_valid_secrets_and_never_shows_them` |
| NFR-02 | Security | Login errors are generic, and unknown and known emails take about the same time. | FR-AUTH-04, `test_wrong_password_and_unknown_email_look_the_same` |
| NFR-03 | Security | Responses never include a stack trace: unhandled errors return a generic 500. | `errors.unhandled_error_handler`, `test_unexpected_errors_return_a_generic_500` |
| NFR-04 | Security | Every API response carries `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Cache-Control: no-store` and a deny-all CSP (docs pages excepted). | `main.security_headers`, `test_security_headers_are_sent` |
| NFR-05 | Performance | List endpoints are paginated: admin lists `page_size` ≤ 100, tutor directory `limit` ≤ 100, CSV exports ≤ 10 000 rows, bulk actions ≤ 100 ids. | `routers/admin_filters.py`, `routers/tutors.py`, `export_service.MAX_EXPORT_ROWS` |
| NFR-06 | Performance | Typical API requests complete in under 1 second on the deployed site. | Partly met. Measured on 28 Nov 2026 from Bangladesh with `curl` (5 requests each, total time including TLS): `/api/health` median 0.65 s, `/api/docs` 0.71 s, `/api/openapi.json` 0.96 s, `/api/tutors?limit=20` 1.02 s (one cold-start outlier at 2.6 s) |
| NFR-07 | Usability | The UI is responsive (sidebar becomes a drawer, navbar collapses). Public pages were checked at 375, 768 and 1280 px. | `styles/layout.css`, `docs/PHASE3_E2E_TEST_REPORT.md` §2.3 |
| NFR-08 | Usability | Every data page shows loading, empty and error states, uses toasts for results and asks for confirmation before destructive actions. | `LoadingState`, `EmptyState`, `ErrorState`, `Toast`, `ConfirmDialog`, `PromptDialog` |
| NFR-09 | Usability | Forms are accessible: labels, `aria-invalid`, focus moves to the first error, unique ids (`useId`), and a show/hide toggle on every password field. | `FormField`, `PasswordInput`, `PasswordInput.test.tsx` |
| NFR-10 | Reliability | Data persists in PostgreSQL across restarts and serverless cold starts. Throttling state is stored in the database, not in memory. | `login_attempts` table, Supabase PostgreSQL |
| NFR-11 | Reliability | The database enforces integrity with CHECK, UNIQUE and FOREIGN KEY constraints and indexes. Migrations are additive and have a `downgrade()`. | `models/*`, `alembic/versions/*` |
| NFR-12 | Maintainability | Authorisation lives in one RBAC module (`core/permissions.py` + `core/dependencies.py`). Layers run router → service → model. | C3, C7 |
| NFR-13 | Maintainability | Automated tests cover the backend (199 tests + 170 subtests, 98 % line coverage) and the frontend (83 tests). | C11 |
| NFR-14 | Portability | All timestamps are stored and returned as timezone-aware UTC and shown in the viewer's timezone. | `models/helpers.UtcDateTime`, `test_timestamps_and_browser.py` |

### B4. Roles and Permission Matrix

The tables below match `core/permissions.py`, `core/dependencies.py`, `services/group_service.py`, `services/record_service.py`, `crud.can_manage` and `services/admin_service.py`.

**Table 10: Endpoint groups by role**

Legend: **yes** = allowed · **no** = refused (status code) · **own** = only the caller's own resource · **404** = hidden.

| Endpoint group | Visitor | User | Group member | Group owner | Admin |
|---|---|---|---|---|---|
| `POST /api/auth/signup`, `/login`, password reset | yes | yes | yes | yes | yes |
| `/api/auth/refresh`, `/logout` (cookie + CSRF header) | no 401 | yes | yes | yes | yes |
| `GET /api/health`, `/api/docs` | yes | yes | yes | yes | yes |
| `GET /api/tutors`, `GET /api/tutors/{id}` | yes (public view) | yes (public view; own: full) | yes | yes | yes (full view incl. Student ID) |
| `POST /api/tutors` | no 401 | Tutor accounts only (Student: 403); one each | — | — | only if account type is Tutor |
| `PUT`/`DELETE /api/tutors/{id}` | no 401 | own (403 otherwise) | — | — | yes (audited as moderation) |
| `/api/users/me` (profile, password, sessions) | no 401 | own | own | own | own |
| `GET/POST /api/records` (personal) | no 401 | own | own | own | own |
| `GET/PATCH/DELETE /api/records/{id}` (personal record) | no 401 | own (others 404) | own | own | own (others 404) |
| `POST /api/groups`, `GET /api/groups` | no 401 | yes (lists own groups) | yes | yes | yes |
| `GET /api/groups/{id}`, `/members`, `/records` | no 401 | 404 (not a member) | yes | yes | 404 unless a member |
| `POST /api/groups/{id}/records` | no 401 | 404 | needs `can_create_records` (403) | yes | 404 unless a member |
| `PATCH /api/records/{id}` (shared record) | no 401 | 404 | needs `can_update_records`; assignee needs it only for non-status fields | yes | 404 unless a member |
| `PATCH /api/groups/{id}`, `DELETE /api/groups/{id}` | no 401 | 404 | no 403 | yes | 404 unless a member (delete via moderation) |
| `POST/PATCH /api/groups/{id}/members[/{uid}]` | no 401 | 404 | no 403 | yes | 404 unless a member |
| `DELETE /api/groups/{id}/members/{uid}` | no 401 | 404 | own (leave) | yes (not self) | 404 unless a member |
| `GET /api/dashboard/summary` | no 401 | own | own | own | own |
| `/api/admin/*` (all admin and export endpoints) | no 401 | no 403 | no 403 | no 403 | yes |

**Table 11: Group permissions**

| Action | Owner | `can_create_records` | `can_update_records` | `can_assign_records` | Member with none (viewer) | Non-member |
|---|---|---|---|---|---|---|
| Read group, members, shared records | yes | yes | yes | yes | yes | 404 |
| Create a shared record (no assignee) | yes | **yes** | no 403 | no 403 | no 403 | 404 |
| Create a shared record with an assignee | yes | only together with assign | no 403 | needs create too | no 403 | 404 |
| Edit title, details, due date, status | yes | no 403 | **yes** | no 403 | no 403 | 404 |
| Change only the status of a record assigned to me | yes | yes | yes | yes | **yes** | 404 |
| Set or change the assignee | yes | no 403 | no 403 | **yes** | no 403 | 404 |
| Delete a record | any record | no 403 | only records they created | no 403 | no 403 | 404 |
| Rename/edit the group | **owner only** | no 403 | no 403 | no 403 | no 403 | 404 |
| Delete the group (cascades) | **owner only** | no 403 | no 403 | no 403 | no 403 | 404 |
| Add a member, change permissions, remove a member | **owner only** | no 403 | no 403 | no 403 | no 403 | 404 |
| Leave the group | no 403 (delete instead) | yes | yes | yes | yes | 404 |

The label in `group_memberships.group_role` is derived from the booleans (`group_service.derive_role`): all three = `editor`, none = `viewer`, any other mix = `member`. The owner has `owner`. The owner's row cannot be changed (403).

**Table 12: Admin rules**

| Rule | Enforcement | Result |
|---|---|---|
| An admin cannot change their own role | `admin_service.change_role` | 403 "You cannot change your own role." |
| An admin cannot ban themself | `admin_service._check_can_ban` | 403; bulk: `skipped_self` |
| An admin cannot ban another admin | `admin_service._check_can_ban` | 403 "Administrators cannot be banned. Change their role first."; bulk: `skipped_admin` |
| An admin **can** demote another admin to `user` | `admin_service.change_role` | Allowed and audited (`role_changed`). See the limitation in E3. |
| Ban/unban need a reason (3–500 chars) | `schemas/admin.BanIn`, `UnbanIn`, `BulkBanIn`, `BulkUnbanIn` | 422 otherwise |
| Banning revokes all sessions | `admin_service._apply_ban` | `sessions_revoked` count in the audit details |
| Admin rights inside a study group | `group_service.load_for_member` | **None.** An admin who is not a member gets 404 like anyone else. Admins can only view a group's detail and delete groups or records through `/api/admin/groups` and `/api/admin/records` (moderation, audited). |
| The admin role cannot be obtained through signup | `SignupIn` has no `role` field, `extra="forbid"` | 422. Admins are created with `scripts/create_admin.py` or promoted by another admin. |
| Every admin mutation is audited | `log_event` calls in `admin_service`, `routers/tutors.py`, `routers/admin_exports.py` | Rows in `audit_logs` |

### B5. Use Cases

**Figure 1: Use case diagram**

```mermaid
flowchart LR
  V(["Visitor"])
  U(["User"])
  M(["Group member"])
  O(["Group owner"])
  A(["Admin"])

  subgraph Peerora
    UC1["UC-01 Log in and refresh"]
    UC2["UC-02 Create a shared record"]
    UC3["UC-03 Change a member's permissions"]
    UC4["UC-04 Denied action"]
    UC5["UC-05 Ban a user"]
    UC6["UC-06 Read the audit log"]
    UC7["UC-07 Revoke a session"]
    UC8["Search tutors"]
  end

  V --> UC1
  V --> UC8
  U --> UC1
  U --> UC7
  M --> UC2
  M --> UC4
  O --> UC2
  O --> UC3
  A --> UC5
  A --> UC6
  A --> UC7
```

**Table 13: Use case descriptions**

**UC-01: Log in and refresh**

| Item | Description |
|---|---|
| Actor | Visitor / User |
| Preconditions | The account exists and is not banned. The login throttle limits are not reached. |
| Main flow | 1. The user submits email and password on `/login`. 2. The frontend sends `POST /api/auth/login`. 3. The server checks the throttle, verifies the peppered Argon2id hash, records a `login_attempts` row and a `login_success` audit event, creates a `user_sessions` row and a refresh token. 4. The server returns 200 with `access_token`, `expires_in` and `user`, and sets the `peerora_refresh` cookie. 5. The frontend stores the token in memory and redirects to the role-specific dashboard. 6. After the token expires, a request returns 401. 7. The frontend calls `POST /api/auth/refresh` (cookie + `X-Requested-With`), receives a new access token and a new cookie, and repeats the request once. |
| Alternative / error flows | 3a. Wrong email or password → 401 "Incorrect email or password.". 3b. Limit reached → 429 with `Retry-After`. 3c. Banned → 403 `account_suspended`. 7a. Refresh cookie missing, expired or revoked → 401, the cookie is cleared and the frontend becomes guest and redirects to `/login`. 7b. Old refresh token reused after the 10-s window → 401 and the whole session is revoked (`token_reuse_detected`). 7c. Missing CSRF header → 403. |
| Postconditions | A live session exists. An audit row and a login-attempt row are stored. |

**UC-02: Create a shared record**

| Item | Description |
|---|---|
| Actor | Group member with `can_create_records`, or the group owner |
| Preconditions | Signed in. Member of the group. |
| Main flow | 1. The member opens `/groups/:id` and clicks "New record". 2. The member fills title, details, status, due date and (if allowed) assignee. 3. The frontend sends `POST /api/groups/{id}/records`. 4. The server loads the group through the caller's membership, checks `can_create`, and checks `can_assign` and group membership of the assignee if one is set. 5. The server stores the record and returns 201 with `can_edit`, `can_assign` and `can_delete` flags. |
| Alternative / error flows | 4a. Not a member → 404. 4b. No create permission → 403. 4c. Assignee set without assign permission → 403. 4d. Assignee not a member → 422. 4e. Validation error (empty title, title > 200 chars) → 422. |
| Postconditions | The record is visible to all group members. |

**UC-03: Change a member's permissions**

| Item | Description |
|---|---|
| Actor | Group owner |
| Preconditions | Signed in. Owner of the group. The target is a non-owner member. |
| Main flow | 1. The owner opens the members panel and toggles Create, Update or Assign for a member. 2. The frontend sends `PATCH /api/groups/{id}/members/{user_id}` with a preset and/or individual booleans. 3. The server checks ownership, applies the preset then the overrides, derives the label and writes `member_permissions_changed` with before/after values. 4. The server returns 200 with the updated member. |
| Alternative / error flows | 3a. Caller is not the owner → 403. 3b. Caller is not a member → 404. 3c. Target is not a member → 404. 3d. Target is the owner → 403. 3e. Empty body → 422. |
| Postconditions | The member's next request uses the new permissions. |

**UC-04: A denied action**

| Item | Description |
|---|---|
| Actor | Group member without `can_update_records` |
| Preconditions | Signed in. Member of the group. Not the assignee of the record. |
| Main flow | 1. The member sends `PATCH /api/records/{id}` with a new title (for example through the API or a stale page). 2. `get_current_user` accepts the token. 3. `record_service.load_for_user` returns the record because the caller is a member. 4. `can_edit` is false and the change is not a status-only update by the assignee. 5. The server returns 403 "You do not have permission to edit this record.". 6. The frontend shows the message in a toast. The user stays signed in. |
| Alternative / error flows | 3a. Caller is not a member → 404, so the record's existence is not revealed. |
| Postconditions | Nothing is changed. |

**UC-05: Ban a user**

| Item | Description |
|---|---|
| Actor | Admin |
| Preconditions | Signed in as admin. The target is a non-admin and not the admin themself. |
| Main flow | 1. The admin opens `/admin/users/:id` and clicks "Ban". 2. A dialog asks for a reason (3–500 characters). 3. The frontend sends `POST /api/admin/users/{id}/ban`. 4. The server sets `is_banned`, `ban_reason`, `banned_at` and `banned_by_id`, revokes all the user's sessions and writes `user_banned` with the reason and the number of sessions revoked. 5. The server returns 200 with the updated user. 6. The banned user's next request gets 403 with `X-Error-Code: account_suspended`. Their browser clears the session, shows the reason and redirects to `/login`. |
| Alternative / error flows | 4a. Target is an admin or the caller → 403. 4b. Already banned → 409. 4c. User not found → 404. 2a. Reason missing or too short → 422. |
| Postconditions | The user cannot log in, refresh or call any endpoint until unbanned. |

**UC-06: Read the audit log**

| Item | Description |
|---|---|
| Actor | Admin |
| Preconditions | Signed in as admin. |
| Main flow | 1. The admin opens `/admin/audit`. 2. The page loads the action names (`GET /api/admin/audit-actions`) and the first page (`GET /api/admin/audit-logs?page=1&page_size=25`). 3. The admin filters by text, action, user id or date range. 4. The server returns the matching rows, newest first, with actor and target emails and `total`. 5. Optionally the admin clicks "Export CSV", which calls `GET /api/admin/exports/audit-logs.csv` with the same filters and writes an `export` audit event. |
| Alternative / error flows | 2a. Non-admin → 403 (the frontend guard sends them to `/forbidden` first). 2b. No token → 401. 3a. Invalid date or a `q` longer than 100 chars → 422. |
| Postconditions | Reading does not change data. An export adds one audit row. |

**UC-07: Revoke a session**

| Item | Description |
|---|---|
| Actor | User (own session) or Admin (any user's session) |
| Preconditions | Signed in. The session is active. |
| Main flow | 1. The user opens `/account` → Active sessions. 2. The user clicks "Revoke" on another device. 3. The frontend sends `DELETE /api/users/me/sessions/{session_id}`. 4. The server sets `revoked_at` and `revoked_reason='user_revoked'` and writes `session_revoked`. 5. The other device's next request gets 401, its refresh also fails, and it is signed out. |
| Alternative / error flows | 3a. Session id of another user or already revoked → 404. Admin variant: `DELETE /api/admin/users/{id}/sessions/{sid}` or `POST .../sessions/revoke-all`. |
| Postconditions | The session can no longer be used or refreshed. |

### B6. Acceptance Criteria

**Table 14: Acceptance criteria**

| ID | Requirement | Given | When | Then | Test |
|---|---|---|---|---|---|
| AC-01 | FR-AUTH-05/06 | an access token whose `exp` is in the past | it is sent to `GET /api/users/me` | the response is 401 with `WWW-Authenticate: Bearer` | `test_expired_token_returns_401` |
| AC-02 | FR-AUTH-06 | a valid token with one character of the payload changed | it is sent to a protected endpoint | the response is 401 | `test_tampered_token_returns_401` |
| AC-03 | FR-AUTH-06 | a token with `alg=none` or signed with another key | it is sent | the response is 401 | `test_unsigned_none_algorithm_token_returns_401`, `test_token_signed_with_another_key_returns_401` |
| AC-04 | FR-RBAC-05 | user A owns a personal record | user B requests `GET /api/records/{id}` | the response is 404 and the record is not revealed | `test_personal_records_are_private` |
| AC-05 | FR-RBAC-07 | a user who is not a member of group G | they request G, its members or records | each response is 404 | `test_non_members_cannot_see_anything` |
| AC-06 | FR-RBAC-09 | a member without `can_update_records` | they `PATCH` the title of a shared record | the response is 403 | `test_update_permission_alone`, `test_viewer_cannot_edit_but_assignee_can_update_status` |
| AC-07 | FR-RBAC-09 | a member with only `can_create_records` | they create a record with an assignee | the response is 403 | `test_create_permission_alone` |
| AC-08 | FR-RBAC-13 | a signed-in user with a valid token | an admin bans them and they send the next request | the response is 403 with `X-Error-Code: account_suspended` | `test_banned_user_is_rejected_on_next_request`, `test_suspended_responses_are_tagged_for_the_frontend` |
| AC-09 | FR-RBAC-12 | two admins | admin 1 calls `POST /api/admin/users/{admin2}/ban` | the response is 403 and admin 2 is not banned | `test_admin_cannot_ban_another_admin_or_themself` |
| AC-10 | FR-RBAC-12 | an admin | they call `PATCH /api/admin/users/{self}/role` | the response is 403 | `test_admin_cannot_change_own_role` |
| AC-11 | FR-RBAC-14 | a user whose role was changed by an admin | they reuse their old access token | the response is 401; after refresh the new token carries the new role | `test_token_with_outdated_role_returns_401`, `test_role_change_takes_effect_immediately` |
| AC-12 | FR-AUTH-08 | a refresh token that was rotated more than 10 s ago | it is presented again | the response is 401, the session is revoked and `token_reuse_detected` is logged | `test_reusing_a_rotated_token_revokes_the_whole_session` |
| AC-13 | FR-AUTH-12 | 5 wrong passwords for one account from one IP in 15 min | a 6th attempt is made from that IP | the response is 429, while the owner can still log in from another IP | `test_account_is_throttled_from_the_attacking_address`, `test_owner_can_still_log_in_from_another_network` |
| AC-14 | FR-AUTH-09 | a signed-in session | the user logs out | the response is 204, the cookie is cleared and the old access token gets 401 | `test_logout_revokes_the_session` |
| AC-15 | FR-ADM-07 | a selection containing the admin, another admin and two users | the admin bulk-bans them | the two users are banned, the others are `skipped_self` / `skipped_admin`, and `done` = 2 | `test_bulk_ban_skips_admins_and_self` |
| AC-16 | FR-ADM-11 | the users list filtered by `status=banned` | the admin exports users CSV with the same filter | the CSV contains only banned users and an `export` audit row stores the filters | `test_users_export_respects_filters`, `test_exports_are_audited` |
| AC-17 | FR-AUTH-01 | a visitor | they send `role: "admin"` in the signup body | the response is 422 and no account is created | `test_admin_cannot_be_chosen_at_signup` |

### B7. Traceability Matrix

**Table 15: Requirement → implementation → test → screenshot**

Backend test files are in `backend/tests/`; frontend tests are next to the code in `frontend/src/`.

| Requirement | Endpoint or screen | Automated test(s) | Screenshot |
|---|---|---|---|
| FR-AUTH-01 | `POST /api/auth/signup`; `/signup` | `test_auth.py::test_signup_creates_user_role_and_signs_in`, `test_tutor_signup`, `test_admin_cannot_be_chosen_at_signup` | S1 |
| FR-AUTH-02 | `POST /api/auth/signup`; `/signup` | `test_auth.py::test_password_rules_are_enforced_on_the_backend`; `authValidation.test.ts` | S1 |
| FR-AUTH-03 | `core/security.py` | `test_auth.py::test_password_is_hashed_with_argon2_and_pepper` | — |
| FR-AUTH-04 | `POST /api/auth/login`; `/login` | `test_auth.py::test_wrong_password_and_unknown_email_look_the_same`; `LoginPage.test.tsx` | S1 |
| FR-AUTH-05 | `core/security.create_access_token` | `test_tokens.py::test_token_contains_user_id_role_and_session`; `test_config.py::test_access_token_lifetime_is_capped_at_15_minutes` | S7 |
| FR-AUTH-06 | `core/dependencies.get_current_user` | `test_tokens.py` (all 11 tests) | S7 |
| FR-AUTH-07 | `POST /api/auth/refresh` | `test_sessions.py::test_refresh_rotates_the_token`, `test_new_token_works_and_old_token_is_rejected` | S8 |
| FR-AUTH-08 | `session_service.rotate` | `test_sessions.py::test_reusing_a_rotated_token_revokes_the_whole_session`, `test_concurrent_refresh_within_grace_window_keeps_the_session`, `test_grace_window_never_revives_a_logged_out_session` | — |
| FR-AUTH-09 | `POST /api/auth/logout` | `test_auth.py::test_logout_revokes_the_session` | — |
| FR-AUTH-10 | `/refresh`, `/logout` | `test_auth.py::test_logout_and_refresh_require_the_csrf_header` | — |
| FR-AUTH-11 | `GET/DELETE /api/users/me/sessions`; `/account` | `test_sessions.py::test_list_and_revoke_own_sessions`, `test_cannot_revoke_another_users_session` | S4 |
| FR-AUTH-12 | `auth_service.is_login_throttled` | `test_rate_limit.py` (first 6 tests) | S16 |
| FR-AUTH-13 | `auth_service._recent_signups` | `test_rate_limit.py::test_signups_are_limited_per_address`, `test_failed_signups_do_not_count` | — |
| FR-AUTH-14 | `PATCH /api/users/me`; `/account` | `test_auth.py::test_update_name_and_email`, `test_role_and_account_type_cannot_be_changed_by_the_user` | S3 |
| FR-AUTH-15 | `POST /api/users/me/password`; `/account` | `test_auth.py::test_change_password_requires_current_password`, `test_change_password_signs_out_other_sessions` | S3 |
| FR-AUTH-16 | `/api/auth/password-reset/*`; `/forgot-password`, `/reset-password` | `test_password_reset.py` (24 tests); `ForgotPasswordPage.test.tsx`, `ResetPasswordPage.test.tsx` | — |
| FR-AUTH-17 | `AuthContext.tsx`, `apiClient.ts` | `AuthContext.test.tsx` ("restores the session…", "refreshes an expired access token once and retries the request"); `apiClient.test.ts` | S8 |
| FR-RBAC-01 | `core/permissions.py` | `test_rbac.py::test_admins_hold_every_permission_users_hold_only_their_own` | — |
| FR-RBAC-02 | all routers | `test_rbac.py` (all); `guards.test.tsx` | S6 |
| FR-RBAC-03 | all protected routes | `test_rbac.py::test_every_protected_route_requires_a_token` | S7 |
| FR-RBAC-04 | `/api/admin/*` | `test_rbac.py::test_every_admin_route_is_forbidden_for_normal_users`, `test_admin_content.py::test_normal_user_cannot_moderate`, `test_exports.py::test_exports_are_admin_only` | S6 |
| FR-RBAC-05 | `/api/records/{id}`; `/records` | `test_records.py::test_personal_records_are_private` | S2 |
| FR-RBAC-06 | `/api/tutors`; `/tutors/:id/edit` | `test_tutor_ownership.py` (10 tests) | — |
| FR-RBAC-07 | `/api/groups/{id}/*` | `test_groups.py::test_non_members_cannot_see_anything`, `test_group_permissions.py::test_outsiders_still_see_nothing` | — |
| FR-RBAC-08 | `POST /api/groups` | `test_groups.py::test_creator_becomes_owner`, `test_group_permissions.py::test_owner_holds_every_permission` | S5 |
| FR-RBAC-09 | `POST /api/groups/{id}/records`, `PATCH /api/records/{id}`; `/groups/:id` | `test_group_permissions.py::test_create_permission_alone`, `test_update_permission_alone`, `test_assign_permission_alone`; `GroupDetailPage.test.tsx`; `RecordForm.test.tsx` | S5, S6 |
| FR-RBAC-10 | `PATCH /api/records/{id}` | `test_group_permissions.py::test_assignee_can_always_update_status_only`, `test_records.py::test_unassigned_viewer_cannot_change_status` | — |
| FR-RBAC-11 | `/api/groups/{id}`, `/members/*` | `test_groups.py::test_only_owner_can_rename_or_delete`, `test_only_owner_manages_membership`, `test_owner_role_cannot_be_changed_and_owner_cannot_leave`; `test_group_permissions.py::test_only_the_owner_can_change_permissions` | S5 |
| FR-RBAC-12 | `/api/admin/users/{id}/ban`, `/role`; `/admin/users/:id` | `test_admin_users.py::test_admin_cannot_ban_another_admin_or_themself`, `test_admin_cannot_change_own_role`; `AdminUserDetailPage.test.tsx` | S13 |
| FR-RBAC-13 | `get_current_user`, `session_service.rotate`, `auth_service.login` | `test_tokens.py::test_banned_user_is_rejected_on_next_request`, `test_sessions.py::test_banned_user_cannot_refresh`, `test_auth.py::test_banned_user_cannot_log_in`, `test_admin_users.py::test_suspended_responses_are_tagged_for_the_frontend`; `AuthContext.test.tsx` ("signs a suspended user out…") | S9 |
| FR-RBAC-14 | `get_current_user` | `test_tokens.py::test_token_with_outdated_role_returns_401`, `test_admin_users.py::test_role_change_takes_effect_immediately` | — |
| FR-RBAC-15 | `group_service` | `test_group_permissions.py::test_revoking_a_permission_takes_effect_immediately` | — |
| FR-ADM-01 | `GET /api/admin/overview`; `/admin` | `test_admin_users.py::test_overview_counts` | S10 |
| FR-ADM-02 | `GET /api/admin/users`; `/admin/users` | `test_admin_users.py::test_search_filters_and_pagination` | S11 |
| FR-ADM-03 | `GET /api/admin/users/{id}`; `/admin/users/:id` | `test_admin_users.py::test_user_detail_contains_sessions_and_activity` | S12 |
| FR-ADM-04 | `/ban`, `/unban` | `test_admin_users.py::test_ban_requires_reason_revokes_sessions_and_is_audited`, `test_unban_reason_is_required`; `PromptDialog.test.tsx` | S13 |
| FR-ADM-05 | `PATCH /api/admin/users/{id}/role` | `test_admin_users.py::test_role_change_takes_effect_immediately` | S12 |
| FR-ADM-06 | `/api/admin/users/{id}/sessions/*` | `test_admin_users.py::test_admin_session_revocation` | S12 |
| FR-ADM-07 | `/bulk-ban`, `/bulk-unban` | `test_admin_users.py::test_bulk_ban_skips_admins_and_self` | S11 |
| FR-ADM-08 | `/api/admin/records*`, `/api/admin/groups*`; `/admin/content` | `test_admin_content.py` (6 tests) | S14 |
| FR-ADM-09 | `GET /api/admin/audit-logs`; `/admin/audit` | `test_audit.py::test_login_events_record_ip_user_agent_and_time`, `test_search_and_user_filter`, `test_text_search_matches_user_emails_and_keeps_filters` | S15 |
| FR-ADM-10 | `GET /api/admin/security/failed-logins`; `/admin/security` | `test_audit.py::test_failed_login_report_groups_by_ip_and_account` | S16 |
| FR-ADM-11 | `/api/admin/exports/*.csv` | `test_exports.py` (5 tests) | S17 |
| FR-ADM-12 | `audit_service.sanitize` | `test_audit.py::test_sensitive_keys_are_never_stored`, `test_password_reset.py::test_tokens_are_never_logged_or_audited` | — |
| FR-ADM-13 | `PATCH /api/admin/tutors/{id}/owner` | `test_tutor_ownership.py::test_admin_cannot_link_profile_to_a_student_account`, `test_legacy_profiles_without_owner_are_admin_only` | — |
| FR-DOM-01 | `GET /api/tutors`; `/tutors` | `test_tutors_api.py::test_server_side_search_and_filters`, `test_list_is_a_plain_public_array_newest_first` | — |
| FR-DOM-02 | `/api/tutors/*`; `/tutors/new`, `/tutors/:id` | `test_tutors_api.py` (19 tests), `test_tutor_ownership.py::test_students_can_view_but_not_change_profiles` | — |
| FR-DOM-03 | `POST/GET /api/groups`; `/groups` | `test_groups.py::test_creator_becomes_owner`, `test_members_see_their_groups`, `test_group_validation` | S5 |
| FR-DOM-04 | `POST/PATCH /api/groups/{id}/members` | `test_group_permissions.py::test_add_member_with_individual_permissions`, `test_presets_and_derived_labels`; `test_groups.py::test_add_member_errors` | S5 |
| FR-DOM-05 | `POST /api/groups/{id}/records` | `test_records.py::test_assign_only_to_members`, `test_editor_and_owner_create_viewer_cannot` | S5 |
| FR-DOM-06 | `/api/records`; `/records` | `test_records.py::test_personal_records_are_private`, `test_personal_record_cannot_be_assigned_to_someone_else` | S2 |
| FR-DOM-07 | `DELETE /api/groups/{id}`, `/members/{uid}` | `test_records.py::test_removed_member_loses_assignment`, `test_deleting_group_deletes_its_records`; `test_groups.py::test_member_can_leave` | — |
| FR-DOM-08 | `GET /api/dashboard/summary`; `/dashboard/*` | `test_records.py::test_assigned_list_and_dashboard` | S2 |
| FR-DOM-09 | `dashboardPath.ts` | `dashboardPath.test.ts` | — |

---

## Part C. Technical Design (TDD)

### C1. Technology Stack

**Table 16: Technology stack**

Backend versions are the pins in `backend/requirements.txt`. Frontend versions are the ones installed from `frontend/package.json`.

| Component | Technology | Version | Reason for choosing it |
|---|---|---|---|
| Frontend framework | React | 18.3.1 | Component model taught in the course; large ecosystem |
| Language (frontend) | TypeScript | 5.6.3 | Static types for API shapes and props; `tsc` runs in `npm run build` |
| Build tool / dev server | Vite | 5.4.21 | Fast dev server with an `/api` proxy (`vite.config.ts`) so development is same-origin like production |
| Routing | React Router | 6.30.6 | Nested layouts and route guards |
| UI library | None: hand-written CSS (`src/styles/*.css`) with reusable components | — | Keeps the bundle small and avoids extra dependencies; accessible form components were already built for the MVP |
| Backend framework | FastAPI (`fastapi[standard]`) | 0.165.0 | Dependency injection fits authentication/RBAC checks; automatic OpenAPI docs at `/api/docs` |
| Validation | Pydantic (bundled with FastAPI) | v2 | Request schemas with `extra="forbid"` stop over-posting |
| Database | Supabase PostgreSQL | managed by Supabase | Hosted PostgreSQL already used by the MVP; works with Vercel serverless through the pooler |
| ORM | SQLAlchemy | 2.1.9 | Typed `Mapped[...]` models; parameterised queries |
| DB driver | psycopg (binary) | 3.3.9 | PostgreSQL driver for SQLAlchemy; prepared statements disabled for the pooler |
| Migrations | Alembic | 1.20.1 | Versioned, reversible schema changes (revisions `3f8a1c2d9b7e`, `0002`–`0008`) |
| Password hashing | argon2-cffi (Argon2id) | 25.1.0 | Memory-hard hash recommended by OWASP; plus an HMAC-SHA256 pepper |
| JWT library | PyJWT | 2.15.1 | Small, well-maintained; supports algorithm allow-lists and required claims |
| Backend tests | pytest + pytest-cov (unittest-style tests with FastAPI `TestClient`) | 9.2.0 / 7.1.0 | Runs the real app on in-memory SQLite per test |
| Frontend tests | Vitest + Testing Library + jsdom | 2.1.9 / 16.x / 25.x | Same config as Vite; component tests close to how users interact |
| Python runtime | CPython | ≥ 3.11 required (tested on 3.14.4) | `enum.StrEnum` |
| Hosting | Vercel (`vercel.json` with `backend` and `frontend` services) | — | Required by the course; one origin for the SPA and `/api` |

### C2. System Architecture

**Figure 2: System architecture**

```mermaid
flowchart LR
  subgraph Browser
    SPA["React SPA<br/>pages → services/*.ts → apiClient.ts<br/>access token in memory"]
    CK[("peerora_refresh cookie<br/>HttpOnly, SameSite=Strict<br/>Path=/api/auth")]
  end

  subgraph Vercel["Vercel (one origin)"]
    FE["frontend service<br/>Vite build in frontend/dist<br/>rewrite /(.*) → /index.html"]
    API["backend service<br/>FastAPI main:app<br/>routers → services → models"]
  end

  DB[("Supabase PostgreSQL<br/>users, sessions, groups, records ...")]
  AUD[("audit_logs and<br/>login_attempts tables")]

  SPA -->|"1. GET / and static assets"| FE
  SPA -->|"2. /api/* with Authorization: Bearer"| API
  CK -->|"3. sent only to /api/auth/refresh and /logout<br/>with X-Requested-With: peerora"| API
  API -->|"4. Set-Cookie on login and refresh"| CK
  API -->|"5. SQL via SQLAlchemy + psycopg 3<br/>transaction pooler"| DB
  API -->|"6. log_event() in the same transaction"| AUD
  AUD -.-|"same database"| DB
```

1. **Browser → frontend service.** The browser loads `index.html` and the hashed JS/CSS bundle from the Vercel frontend service. Every non-`/api` path is rewritten to `index.html`, so React Router handles deep links such as `/groups/3`.
2. **Browser → API (access token).** Every service module calls `apiClient.sendRequest`, which adds `Authorization: Bearer <access token>` from a module variable. The token is never written to `localStorage`. The request goes to `/api/...` on the same origin, and the root rewrite in `vercel.json` routes it to the backend service.
3. **Refresh cookie → API.** The browser sends `peerora_refresh` automatically, but only to paths under `/api/auth` (cookie `Path`) and only on same-site requests (`SameSite=Strict`). The frontend adds `X-Requested-With: peerora`, which cross-site forms cannot set, so the endpoints are protected against CSRF.
4. **API → cookie.** Login, signup and refresh set a new `peerora_refresh` cookie (`HttpOnly`, so JavaScript cannot read it). Logout and failed refreshes delete it.
5. **API → database.** The FastAPI handlers open one SQLAlchemy session per request (`database.get_db`) and query through ORM statements. The engine uses a small pool with `pool_pre_ping`, and `prepare_threshold=None` so it works behind Supabase's transaction pooler.
6. **API → audit log.** Services call `audit_service.log_event()` before `db.commit()`. The audit row is therefore saved in the same transaction as the change it describes: either both are stored or neither is.

### C3. Backend and Frontend Structure

**Backend (two levels, `backend/`)**

```text
backend/
├── main.py                 # FastAPI app: CORS, security headers, error handlers, routers
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/           # 3f8a1c2d9b7e, 0002 … 0008 migrations
├── peerora/
│   ├── config.py           # env settings, secret checks, token lifetimes, cookie flags
│   ├── constants.py        # roles, account types, limits, throttle thresholds
│   ├── database.py         # engine, SessionLocal, get_db
│   ├── errors.py           # readable 422 messages, generic 500
│   ├── crud.py             # tutor data access + can_manage ownership rule
│   ├── core/               # security.py, permissions.py, dependencies.py, request_info.py, timeutils.py
│   ├── models/             # user, session, audit, group, record, tutor, password_reset, helpers
│   ├── schemas/            # Pydantic request/response models (auth, user, group, record, admin, tutor)
│   ├── services/           # auth, session, group, record, admin, audit, export, email, password_reset
│   └── routers/            # auth, users, tutors, groups, records, dashboard, admin_* (5 files)
├── scripts/                # create_admin.py, seed_demo.py, dev_setup.py
├── tests/                  # 17 test modules + base.py + live_smoke_test.py
├── requirements.txt
└── requirements-dev.txt
```

| Concern | Location |
|---|---|
| Routes (HTTP layer, no SQL) | `peerora/routers/*.py` |
| Services (business rules, audit calls) | `peerora/services/*.py` |
| Data access / repositories | SQLAlchemy queries inside the services; `peerora/crud.py` for tutors (kept from the MVP) |
| Models | `peerora/models/*.py` |
| Authentication code | `core/security.py` (hashing, JWT), `services/auth_service.py`, `services/session_service.py`, `routers/auth.py` |
| RBAC module | `core/permissions.py` (roles → permissions) + `core/dependencies.py` (`get_current_user`, `require_permission`, `require_account_type`) |
| Group / ownership rules | `services/group_service.py`, `services/record_service.py`, `crud.can_manage` |
| Admin code | `routers/admin_users.py`, `admin_content.py`, `admin_audit.py`, `admin_exports.py`, `admin_filters.py`; `services/admin_service.py`, `services/export_service.py` |

**Frontend (two levels, `frontend/`)**

```text
frontend/
├── index.html
├── csp.ts                  # build-time Content-Security-Policy <meta> plugin
├── vite.config.ts          # /api dev proxy, Vitest config
├── package.json
└── src/
    ├── main.tsx, App.tsx   # providers and the route table
    ├── auth/               # AuthContext.tsx, guards.tsx, dashboardPath.ts
    ├── services/           # apiClient.ts, authService.ts, adminService.ts, groupService.ts, …
    ├── pages/              # public, auth/, account/, dashboard/, groups/, records/, admin/
    ├── layouts/            # PublicLayout.tsx, AppLayout.tsx (role-based sidebar)
    ├── components/         # FormField, PasswordInput, Pagination, Toast, PromptDialog, RecordForm, …
    ├── hooks/              # useAsync.ts
    ├── types/              # auth, admin, group, tutor
    ├── utils/              # validation, authValidation, format, messages
    ├── constants/          # tutorOptions.ts
    ├── styles/             # global, layout, components, pages
    └── test/               # setup and render helpers
```

| Concern | Location |
|---|---|
| Pages | `src/pages/**` (admin pages in `src/pages/admin/`) |
| Components | `src/components/` |
| API client | `src/services/apiClient.ts` (Bearer header, 401 → refresh → retry, error parsing, CSV download) |
| Authentication context | `src/auth/AuthContext.tsx` (`restoring` / `authenticated` / `guest`; session restore; suspended handling) |
| Route guards | `src/auth/guards.tsx`: `RequireAuth`, `RequireAdmin`, `RequireAccountType`, `GuestOnly`, `DashboardRedirect` |

### C4. Data Model

**Figure 3: Entity-relationship diagram**

```mermaid
erDiagram
  users ||--o| tutors : "owns at most one"
  users ||--o{ user_sessions : "signs in on"
  user_sessions ||--o{ refresh_tokens : "rotates"
  users ||--o{ password_reset_tokens : "requests"
  users ||--o{ login_attempts : "attempts"
  users ||--o{ study_groups : "owns"
  study_groups ||--o{ group_memberships : "has"
  users ||--o{ group_memberships : "is member"
  study_groups ||--o{ study_records : "contains"
  users ||--o{ study_records : "creates"
  users |o--o{ study_records : "is assigned"
  users |o--o{ audit_logs : "acts or is target"

  users {
    int id PK
    string email UK
    string full_name
    string password_hash
    string account_type
    string role
    bool is_banned
    string ban_reason
    datetime banned_at
    int banned_by_id FK
    datetime last_login_at
  }
  tutors {
    int id PK
    int user_id FK,UK
    string student_id UK
    string department
    json subjects
    string teaching_mode
  }
  user_sessions {
    string id PK "UUID = sid claim"
    int user_id FK
    datetime expires_at
    datetime revoked_at
    string revoked_reason
  }
  refresh_tokens {
    int id PK
    string session_id FK
    string token_hash UK
    datetime expires_at
    datetime used_at
  }
  password_reset_tokens {
    int id PK
    int user_id FK
    string token_hash UK
    datetime expires_at
    datetime used_at
  }
  login_attempts {
    int id PK
    string email
    int user_id FK
    string ip_address
    bool success
    string failure_reason
  }
  audit_logs {
    bigint id PK
    int actor_id FK
    int target_user_id FK
    string action
    string target_type
    string target_id
    json details
  }
  study_groups {
    int id PK
    string name
    int owner_id FK
  }
  group_memberships {
    int id PK
    int group_id FK
    int user_id FK
    string group_role
    bool can_create_records
    bool can_update_records
    bool can_assign_records
    int added_by_id FK
  }
  study_records {
    int id PK
    int created_by_id FK
    int group_id FK "NULL = personal"
    int assigned_to_id FK
    string title
    string status
    date due_date
  }
```

All timestamp columns use the `UtcDateTime` type (`models/helpers.py`). It stores UTC and always returns timezone-aware values. All tables have Row Level Security enabled on Supabase, so Supabase's public data API cannot read them. The backend connects as the table owner, which RLS does not restrict (migrations `0002`–`0008`).

**Table 17: `users`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `email` | VARCHAR(254) | UNIQUE `uq_users_email`, stored lowercase |
| `full_name` | VARCHAR(100) | NOT NULL |
| `password_hash` | VARCHAR(255) | Argon2id hash of the peppered password; never returned by the API |
| `account_type` | VARCHAR(10) | CHECK in (`student`, `tutor`) |
| `role` | VARCHAR(10) | CHECK in (`user`, `admin`), default `user`; index `ix_users_role` |
| `is_banned` | BOOLEAN | default false; index `ix_users_is_banned` |
| `ban_reason` | VARCHAR(500) | CHECK `NOT is_banned OR ban_reason IS NOT NULL` |
| `banned_at` | TIMESTAMPTZ | nullable |
| `banned_by_id` | INTEGER | FK → `users.id` ON DELETE SET NULL |
| `last_login_at` | TIMESTAMPTZ | nullable |
| `created_at`, `updated_at` | TIMESTAMPTZ | defaults `now()`; index on `created_at` |

**Table 18: `tutors`** (from the MVP, plus `user_id`)

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `user_id` | INTEGER | FK → `users.id` ON DELETE SET NULL; UNIQUE `uq_tutors_user_id` (one profile per account) |
| `full_name` | VARCHAR(100) | CHECK on length |
| `student_id` | VARCHAR(7) | UNIQUE `uq_tutors_student_id`; private |
| `department` | VARCHAR(100) | CHECK on allowed list |
| `semester` | INTEGER | CHECK 1–24 |
| `cgpa` | NUMERIC(4,2) | CHECK 0–4 |
| `headline`, `bio` | VARCHAR(100), VARCHAR(500) | CHECK on length |
| `subjects` | JSONB | list of allowed subjects (non-empty, checked in `TutorIn`) |
| `teaching_mode` | VARCHAR(20) | CHECK in (`online`, `in_person`, `both`) |
| `hourly_rate` | NUMERIC(12,2) | nullable, CHECK ≥ 0 |
| `tutoring_experience` | VARCHAR(20) | CHECK on allowed list |
| `profile_image_url` | VARCHAR(500) | nullable |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Table 19: `user_sessions`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | VARCHAR(36) | PK, UUID4; the JWT `sid` claim |
| `user_id` | INTEGER | FK → `users.id` ON DELETE CASCADE; index (`user_id`, `revoked_at`) |
| `ip_address` | VARCHAR(45) | nullable (IPv6-safe length) |
| `user_agent` | VARCHAR(255) | nullable |
| `created_at`, `last_used_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ | sliding: extended on every refresh |
| `revoked_at` | TIMESTAMPTZ | NULL = active |
| `revoked_reason` | VARCHAR(30) | `logout`, `user_revoked`, `admin_revoked`, `password_changed`, `banned`, `token_reuse` (`password_reset` from the reset flow) |

**Table 20: `refresh_tokens`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `session_id` | VARCHAR(36) | FK → `user_sessions.id` ON DELETE CASCADE; indexed |
| `token_hash` | VARCHAR(64) | UNIQUE; SHA-256 hex of the raw token |
| `expires_at` | TIMESTAMPTZ | |
| `used_at` | TIMESTAMPTZ | set when rotated; a used token is never valid again |
| `created_at` | TIMESTAMPTZ | |

**Table 21: `login_attempts`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `email` | VARCHAR(254) | index (`email`, `created_at`) |
| `user_id` | INTEGER | FK → `users.id` ON DELETE SET NULL |
| `ip_address` | VARCHAR(45) | index (`ip_address`, `created_at`) |
| `user_agent` | VARCHAR(255) | |
| `success` | BOOLEAN | |
| `failure_reason` | VARCHAR(30) | `bad_credentials`, `banned`, `throttled`, NULL on success |
| `created_at` | TIMESTAMPTZ | |

**Table 22: `audit_logs`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | BIGINT (INTEGER on SQLite) | PK |
| `actor_id` | INTEGER | FK → `users.id` ON DELETE SET NULL; indexed |
| `target_user_id` | INTEGER | FK → `users.id` ON DELETE SET NULL; indexed |
| `action` | VARCHAR(40) | one of the 22 `AuditAction` values; indexed |
| `target_type` | VARCHAR(30) | `user`, `session`, `group`, `record`, `tutor`, `export` |
| `target_id` | VARCHAR(40) | |
| `details` | JSONB | sanitised (no secret-like keys) |
| `ip_address`, `user_agent` | VARCHAR(45), VARCHAR(255) | |
| `created_at` | TIMESTAMPTZ | indexed |

**Table 23: `study_groups`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(100) | CHECK `length(name) >= 2`; indexed |
| `description` | VARCHAR(1000) | nullable |
| `subject` | VARCHAR(100) | nullable |
| `owner_id` | INTEGER | FK → `users.id` ON DELETE CASCADE; indexed; the authoritative owner |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Table 24: `group_memberships`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `group_id` | INTEGER | FK → `study_groups.id` ON DELETE CASCADE |
| `user_id` | INTEGER | FK → `users.id` ON DELETE CASCADE; indexed |
| — | — | UNIQUE (`group_id`, `user_id`) |
| `group_role` | VARCHAR(10) | CHECK in (`owner`, `editor`, `viewer`, `member`) |
| `can_create_records`, `can_update_records`, `can_assign_records` | BOOLEAN | default false |
| `added_by_id` | INTEGER | FK → `users.id` ON DELETE SET NULL |
| `joined_at` | TIMESTAMPTZ | |

**Table 25: `study_records`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `created_by_id` | INTEGER | FK → `users.id` ON DELETE CASCADE; indexed |
| `group_id` | INTEGER | FK → `study_groups.id` ON DELETE CASCADE; NULL = personal; indexed |
| `title` | VARCHAR(200) | CHECK `length(title) >= 1` |
| `content` | VARCHAR(2000) | nullable |
| `status` | VARCHAR(15) | CHECK in (`todo`, `in_progress`, `done`), default `todo`; indexed |
| `due_date` | DATE | nullable |
| `assigned_to_id` | INTEGER | FK → `users.id` ON DELETE SET NULL; indexed |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Table 26: `password_reset_tokens`**

| Column | Type | Key / constraint |
|---|---|---|
| `id` | INTEGER | PK |
| `user_id` | INTEGER | FK → `users.id` ON DELETE CASCADE; index (`user_id`, `created_at`) |
| `token_hash` | VARCHAR(64) | UNIQUE; SHA-256 |
| `created_at`, `expires_at`, `used_at` | TIMESTAMPTZ | valid for 30 minutes, single use |
| `requested_ip` | VARCHAR(45) | |

**How the security concepts are stored**

- **Roles.** `users.role` (`user`/`admin`), restricted by a CHECK constraint. It is separate from `users.account_type`. The permissions of each role are **not** stored in the database. They are defined in code (`ROLE_PERMISSIONS`), so the permission logic is versioned with the code and covered by tests.
- **Bans.** `users.is_banned`, `ban_reason`, `banned_at` and `banned_by_id`. A CHECK constraint guarantees that a banned row always has a reason. The unban reason and the previous ban reason are stored in the `user_unbanned` audit event.
- **Sessions and refresh tokens.** One `user_sessions` row per device. Its UUID is the `sid` claim. Each refresh adds a `refresh_tokens` row and marks the previous one `used_at`. Only SHA-256 hashes are stored, so a database leak does not reveal usable tokens.
- **Group membership with permissions.** One `group_memberships` row per (group, user), holding three booleans and a derived label. The owner has a membership row with `group_role='owner'` and all three set. `study_groups.owner_id` is the authoritative owner.
- **Activity log.** `audit_logs` stores who acted (`actor_id`), who was affected (`target_user_id`), what (`action`, `target_type`, `target_id`, `details`), where (`ip_address`, `user_agent`) and when (`created_at`). Login history is stored separately in `login_attempts` because the throttle queries it on every login.

**Migrations.** `3f8a1c2d9b7e` (MVP `tutors`) → `0002_create_users` → `0003_link_tutors_to_users` (nullable `user_id`; existing rows untouched) → `0004_sessions_and_security` → `0005_study_groups_and_records` → `0006_group_member_permissions` (adds the three booleans and backfills them from the old role labels) → `0007_password_reset_tokens` → `0008_secure_alembic_version` (RLS on `alembic_version` and privileges revoked from the Supabase API roles). Each migration has a `downgrade()`.

### C5. API Design

- **Version prefix.** All endpoints are under `/api` with no version segment. The OpenAPI document reports API version `2.0.0` (`main.py`). A `/v1` segment was not added, to keep the MVP's `/api/tutors` contract and tests working.
- **Error format.** Errors use FastAPI's shape: `{"detail": "<message>"}`. Validation errors (422) use `{"detail": [{"loc": [...], "msg": "<readable message naming the field>", "type": "<pydantic type>"}]}` (`errors.validation_error_handler`). Unexpected errors return 500 `{"detail": "An unexpected error occurred. Please try again later."}`. A 401 includes `WWW-Authenticate: Bearer`. A 403 caused by a ban includes `X-Error-Code: account_suspended`. A 429 includes `Retry-After`.
- **Status codes used.** 200, 201 (created), 202 (reset requested), 204 (deleted / no content), 400 (wrong current password), 401, 403, 404 (not found *or* not visible to the caller), 409 (duplicate or state conflict), 422, 429, 500, 503 (password reset without an email backend).
- **Pagination.** Admin lists return `{"items": [...], "total": n, "page": p, "page_size": s}` (`schemas/common.Page`). The tutor directory returns a plain array with `X-Total-Count`.

**Table 27: API endpoint list**

"Auth" = needs `Authorization: Bearer`. "Cookie" = needs the refresh cookie and `X-Requested-With: peerora`. Every authenticated endpoint can also return 401 (missing/invalid/expired token, ended session, outdated role) and 403 `account_suspended`.

| Method and path | Auth | Role / permission | Request body | Success | Error statuses |
|---|---|---|---|---|---|
| GET `/api/health` | none | — | — | 200 `{"status":"ok"}` | — |
| POST `/api/auth/signup` | none | — | `full_name, email, password, account_type` | 201 `TokenOut` + cookie | 409, 422, 429 |
| POST `/api/auth/login` | none | — | `email, password` | 200 `TokenOut` + cookie | 401, 403 (banned), 422, 429 |
| POST `/api/auth/refresh` | Cookie | — | — | 200 `TokenOut` + new cookie | 401 (cookie cleared), 403 (no CSRF header / banned) |
| POST `/api/auth/logout` | Cookie | — | — | 204, cookie cleared | 403 (no CSRF header) |
| GET `/api/auth/password-reset/availability` | none | — | — | 200 `{available, token_minutes}` | — |
| POST `/api/auth/password-reset/request` | none | — | `email` | 202 generic message | 422, 429, 503 |
| POST `/api/auth/password-reset/confirm` | none | — | `token, new_password` | 200 | 400 (invalid, used, expired token or suspended account), 422 |
| GET `/api/users/me` | Auth | any user | — | 200 `UserOut` | 401 |
| PATCH `/api/users/me` | Auth | `profile:manage_own` (own) | `full_name?, email?, current_password?` | 200 `UserOut` | 400, 409, 422 |
| POST `/api/users/me/password` | Auth | own | `current_password, new_password` | 204 | 400, 422 |
| GET `/api/users/me/sessions` | Auth | own | — | 200 `SessionOut[]` (with `is_current`) | 401 |
| DELETE `/api/users/me/sessions/{session_id}` | Auth | own | — | 204 | 404 |
| GET `/api/tutors` | none | — | query `q, subject, department, teaching_mode, limit≤100, offset` | 200 `TutorPublicOut[]` + `X-Total-Count` | 422 |
| GET `/api/tutors/me` | Auth | account type `tutor` | — | 200 `TutorOut` | 403, 404 |
| GET `/api/tutors/{tutor_id}` | optional | full view for owner/admin | — | 200 `TutorOut` or `TutorPublicOut` | 404, 422 |
| POST `/api/tutors` | Auth | account type `tutor`; one per account | `TutorIn` | 201 `TutorOut` | 403, 409, 422 |
| PUT `/api/tutors/{tutor_id}` | Auth | owner or `content:moderate` | `TutorIn` (full replace) | 200 `TutorOut` | 403, 404, 409, 422 |
| DELETE `/api/tutors/{tutor_id}` | Auth | owner or `content:moderate` | — | 204 | 403, 404 |
| GET `/api/groups` | Auth | any user (own memberships) | — | 200 `GroupOut[]` | 401 |
| POST `/api/groups` | Auth | `group:create` | `name, description?, subject?` | 201 `GroupOut` | 422 |
| GET `/api/groups/{group_id}` | Auth | member | — | 200 `GroupOut` (with `my_role`, `my_permissions`) | 404 |
| PATCH `/api/groups/{group_id}` | Auth | owner | `name?, description?, subject?` | 200 `GroupOut` | 403, 404, 422 |
| DELETE `/api/groups/{group_id}` | Auth | owner | — | 204 | 403, 404 |
| GET `/api/groups/{group_id}/members` | Auth | member | — | 200 `MemberOut[]` | 404 |
| POST `/api/groups/{group_id}/members` | Auth | owner | `email, group_role (editor/viewer), can_*?` | 201 `MemberOut` | 403, 404, 409, 422 |
| PATCH `/api/groups/{group_id}/members/{user_id}` | Auth | owner | `group_role?, can_create_records?, can_update_records?, can_assign_records?` | 200 `MemberOut` | 403, 404, 422 |
| DELETE `/api/groups/{group_id}/members/{user_id}` | Auth | owner, or the member themself (leave) | — | 204 | 403, 404 |
| GET `/api/groups/{group_id}/records` | Auth | member | — | 200 `RecordOut[]` | 404 |
| POST `/api/groups/{group_id}/records` | Auth | `can_create_records` (+ `can_assign_records` if assignee) | `title, content?, status?, due_date?, assigned_to_id?` | 201 `RecordOut` | 403, 404, 422 |
| GET `/api/records?scope=personal\|assigned` | Auth | `record:manage_own` | — | 200 `RecordOut[]` | 422 |
| POST `/api/records` | Auth | `record:manage_own` | `RecordIn` | 201 `RecordOut` | 422 |
| GET `/api/records/{record_id}` | Auth | creator (personal) or member (shared) | — | 200 `RecordOut` | 404 |
| PATCH `/api/records/{record_id}` | Auth | creator / `can_update_records` / `can_assign_records` / assignee (status only) | `RecordUpdate` (partial) | 200 `RecordOut` | 403, 404, 422 |
| DELETE `/api/records/{record_id}` | Auth | creator (personal); owner, or creator with `can_update_records` (shared) | — | 204 | 403, 404 |
| GET `/api/dashboard/summary` | Auth | any user | — | 200 `DashboardSummary` | 401 |
| GET `/api/admin/overview` | Auth | `admin:access` | — | 200 `OverviewOut` | 403 |
| GET `/api/admin/users` | Auth | `user:manage` | query `q, role, account_type, status, page, page_size` | 200 `Page[AdminUserOut]` | 403, 422 |
| GET `/api/admin/users/{user_id}` | Auth | `user:manage` | — | 200 `AdminUserDetail` | 403, 404 |
| POST `/api/admin/users/{user_id}/ban` | Auth | `user:ban` | `reason` (3–500) | 200 `AdminUserOut` | 403 (self/admin), 404, 409, 422 |
| POST `/api/admin/users/{user_id}/unban` | Auth | `user:ban` | `reason` (3–500) | 200 `AdminUserOut` | 404, 409, 422 |
| POST `/api/admin/users/bulk-ban` | Auth | `user:ban` | `user_ids` (1–100), `reason` | 200 `BulkResult` | 403, 422 |
| POST `/api/admin/users/bulk-unban` | Auth | `user:ban` | `user_ids` (1–100), `reason` | 200 `BulkResult` | 403, 422 |
| PATCH `/api/admin/users/{user_id}/role` | Auth | `role:change` | `role` (`user`/`admin`) | 200 `AdminUserOut` | 403 (self), 404, 422 |
| DELETE `/api/admin/users/{user_id}/sessions/{session_id}` | Auth | `session:revoke_any` | — | 204 | 403, 404 |
| POST `/api/admin/users/{user_id}/sessions/revoke-all` | Auth | `session:revoke_any` | — | 200 `{"revoked": n}` | 403, 404 |
| PATCH `/api/admin/tutors/{tutor_id}/owner` | Auth | `content:moderate` | `user_id` (or null) | 200 `TutorOut` | 403, 404, 409, 422 |
| GET `/api/admin/records` | Auth | `content:moderate` | query `q, status, group_id, scope, page, page_size` | 200 `Page[AdminRecordOut]` | 403, 422 |
| DELETE `/api/admin/records/{record_id}` | Auth | `content:moderate` | — | 200 `BulkResult` | 403 |
| POST `/api/admin/records/bulk-delete` | Auth | `content:moderate` | `ids` (1–100) | 200 `BulkResult` | 403, 422 |
| GET `/api/admin/groups` | Auth | `content:moderate` | query `q, page, page_size` | 200 `Page[AdminGroupOut]` | 403, 422 |
| GET `/api/admin/groups/{group_id}` | Auth | `content:moderate` | — | 200 `AdminGroupDetail` | 403, 404 |
| DELETE `/api/admin/groups/{group_id}` | Auth | `content:moderate` | — | 200 `BulkResult` | 403 |
| POST `/api/admin/groups/bulk-delete` | Auth | `content:moderate` | `ids` (1–100) | 200 `BulkResult` | 403, 422 |
| GET `/api/admin/audit-logs` | Auth | `audit:read` | query `q, action, user_id, date_from, date_to, page, page_size` | 200 `Page[AuditLogOut]` | 403, 422 |
| GET `/api/admin/audit-actions` | Auth | `audit:read` | — | 200 `string[]` | 403 |
| GET `/api/admin/security/failed-logins?hours=1..720` | Auth | `audit:read` | — | 200 `SecurityReport` | 403, 422 |
| GET `/api/admin/exports/users.csv` | Auth | `data:export` | same query as users list | 200 `text/csv` attachment | 403, 422 |
| GET `/api/admin/exports/records.csv` | Auth | `data:export` | same query as records list | 200 `text/csv` | 403, 422 |
| GET `/api/admin/exports/audit-logs.csv` | Auth | `data:export` | same query as audit list | 200 `text/csv` | 403, 422 |
| GET `/api/docs`, `/api/redoc`, `/api/openapi.json` | none | — | — | 200 | — |

### C6. JWT Authentication Design

**Figure 4: JWT lifecycle sequence diagram**

```mermaid
sequenceDiagram
  autonumber
  participant B as Browser (React)
  participant A as FastAPI
  participant D as PostgreSQL

  Note over B,A: Login
  B->>A: POST /api/auth/login {email, password}
  A->>D: count recent failures (throttle), load user
  A->>A: verify Argon2id(HMAC(pepper, password))
  A->>D: INSERT login_attempts, audit login_success,<br/>user_sessions, refresh_tokens(hash)
  A-->>B: 200 {access_token, expires_in, user}<br/>Set-Cookie peerora_refresh (HttpOnly)

  Note over B,A: Protected request
  B->>A: GET /api/groups (Authorization: Bearer access)
  A->>A: decode: HS256, iss, exp, required claims
  A->>D: load user (exists, not banned), session (live), role matches
  A-->>B: 200 data

  Note over B,A: Expiry and refresh
  B->>A: GET /api/groups (expired access token)
  A-->>B: 401 "invalid or has expired"
  B->>A: POST /api/auth/refresh (cookie + X-Requested-With)
  A->>D: find token by SHA-256, mark used_at, insert new token,<br/>extend session
  A-->>B: 200 new access_token + new cookie
  B->>A: retry GET /api/groups (new token)
  A-->>B: 200 data

  Note over B,A: Reuse of an old refresh token (after 10 s)
  B->>A: POST /api/auth/refresh (old, used cookie)
  A->>D: revoke session (token_reuse), audit token_reuse_detected
  A-->>B: 401 + cookie cleared

  Note over B,A: Logout
  B->>A: POST /api/auth/logout (cookie + X-Requested-With)
  A->>D: revoke session (logout), audit logout
  A-->>B: 204 + cookie cleared
  B->>A: GET /api/groups (old access token)
  A-->>B: 401 "This session has ended"
```

**Table 28: Access token claims** (`core/security.create_access_token`)

| Claim | Example | Meaning |
|---|---|---|
| `sub` | `"42"` | User id (string of digits; checked with `isdigit()`) |
| `role` | `"user"` | Security role at issue time; compared with the DB on every request |
| `sid` | `"a1b2…-uuid"` | Session id (`user_sessions.id`); lets one session be revoked instantly |
| `type` | `"access"` | Prevents other token types being used as access tokens |
| `iss` | `"peerora"` | Issuer; verified on decode |
| `iat` | `1764300000` | Issued at (Unix seconds, UTC) |
| `exp` | `1764300900` | Expiry: `iat` + `ACCESS_TOKEN_MINUTES` × 60 |

**Signing.** HS256 (HMAC-SHA256). The key is `JWT_SECRET_KEY` from the environment, at least 32 characters; the app refuses to start without it. Decoding passes `algorithms=["HS256"]`, so `alg=none` and algorithm-confusion tokens are rejected, and `options={"require": [...]}` rejects tokens missing any claim.

**Lifetimes.**

| Token | Lifetime | Why |
|---|---|---|
| Access token | 15 minutes by default (`ACCESS_TOKEN_MINUTES`), clamped to 1–15 in `config.get_access_token_minutes` | A stolen access token is useful for at most 15 minutes. Revocation is immediate anyway through the `sid` check. |
| Refresh token / session | 7 days (`REFRESH_TOKEN_DAYS`), sliding: each refresh extends the session | A student is not asked to log in every day, but a device unused for a week must log in again. |
| Reuse grace window | 10 seconds (`REFRESH_REUSE_GRACE_SECONDS`) | Two tabs or a retried request can present the same token at once. This must not sign the user out. |

**Storage in the browser and its risks.**

| Token | Where | Risk | Mitigation |
|---|---|---|---|
| Access token | JavaScript memory only (`apiClient.ts` module variable); lost on reload | XSS could read it while the page is open | React escapes output; no `dangerouslySetInnerHTML`; strict CSP `script-src 'self'` in production (`frontend/csp.ts`); short lifetime |
| Refresh token | `HttpOnly` cookie `peerora_refresh`, `Secure` (production), `SameSite=Strict`, `Path=/api/auth` | CSRF: the browser sends the cookie automatically | `SameSite=Strict`; the cookie is sent only to `/api/auth/*`; `/refresh` and `/logout` also require `X-Requested-With: peerora`, which a cross-site form cannot set; CORS allows only listed origins (no `*`) |

Because the access token lives in memory, a reload loses it. `AuthContext` therefore calls `/api/auth/refresh` on start (status `restoring`) to get a new one from the cookie.

**What the server checks on every request** (`get_current_user`, in this order):

1. An `Authorization: Bearer` header is present (401 otherwise).
2. The signature, algorithm, issuer, expiry, required claims and `type=access` are valid (401).
3. The user with id `sub` exists (401).
4. The user is not banned (403 `account_suspended`).
5. The session `sid` exists, belongs to the user, is not revoked and has not expired (401).
6. The token `role` equals `users.role` (401 "Your permissions changed").

**What the frontend does on a 401** (`apiClient.sendRequest` and `AuthContext.refreshSession`):

1. It calls the shared refresh handler **once**. One refresh promise is shared within a tab, and the Web Locks API (`navigator.locks`, lock `peerora-token-refresh`) serialises refreshes across tabs (`authService.ts`).
2. If the refresh succeeds, it stores the new token and repeats the original request once.
3. If the refresh returns an error, it clears the session (status `guest`), and `RequireAuth` redirects to `/login?next=...`. The auth endpoints themselves never trigger a refresh (`retryOnUnauthorized: false`), so it cannot loop.
4. A 403 with `X-Error-Code: account_suspended` clears the session, shows the reason in a toast and redirects to `/login`. An ordinary 403 leaves the user signed in.

### C7. RBAC Design

**Figure 5: Authorisation flow for one request** (`PATCH /api/records/{id}` on a shared record)

```mermaid
flowchart TD
  R["Request with Bearer token"] --> T{"1. Token valid?<br/>signature, exp, iss, claims"}
  T -- no --> E401["401"]
  T -- yes --> U{"2. User exists?"}
  U -- no --> E401
  U -- yes --> BAN{"Banned?"}
  BAN -- yes --> E403S["403 account_suspended"]
  BAN -- no --> S{"Session live and<br/>token role = DB role?"}
  S -- no --> E401
  S -- yes --> P{"3. Role check<br/>require_permission (if declared)"}
  P -- no --> E403["403"]
  P -- yes --> O{"4. Ownership / membership<br/>load_for_user"}
  O -- "not creator / not member" --> E404["404"]
  O -- found --> G{"5. Group permission<br/>can_edit / can_assign<br/>or assignee status-only"}
  G -- no --> E403
  G -- yes --> H["6. Handler updates the record → 200"]
```

**Roles and permission constants** (`core/permissions.py`)

| Permission | Value | `user` | `admin` |
|---|---|---|---|
| `PROFILE_MANAGE_OWN` | `profile:manage_own` | ✓ | ✓ |
| `TUTOR_PROFILE_MANAGE_OWN` | `tutor_profile:manage_own` | ✓ | ✓ |
| `GROUP_CREATE` | `group:create` | ✓ | ✓ |
| `RECORD_MANAGE_OWN` | `record:manage_own` | ✓ | ✓ |
| `ADMIN_ACCESS` | `admin:access` | ✗ | ✓ |
| `USER_MANAGE` | `user:manage` | ✗ | ✓ |
| `USER_BAN` | `user:ban` | ✗ | ✓ |
| `ROLE_CHANGE` | `role:change` | ✗ | ✓ |
| `SESSION_REVOKE_ANY` | `session:revoke_any` | ✗ | ✓ |
| `CONTENT_MODERATE` | `content:moderate` | ✗ | ✓ |
| `AUDIT_READ` | `audit:read` | ✗ | ✓ |
| `DATA_EXPORT` | `data:export` | ✗ | ✓ |

Account-type capabilities are separate from roles: `require_account_type("tutor")` guards tutor-profile creation and `/api/tutors/me`.

**The reusable check** (`backend/peerora/core/dependencies.py` and `core/permissions.py`):

```python
ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    ROLE_USER: _USER_PERMISSIONS,
    ROLE_ADMIN: frozenset(Permission),  # admins hold every permission
}

def has_permission(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())

def require_permission(permission: Permission) -> Callable[[User], User]:
    def checker(user: CurrentUser) -> User:      # CurrentUser = Depends(get_current_user)
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user
    return checker

# Usage in a router (routers/admin_users.py):
UserBanner = Annotated[User, Depends(require_permission(Permission.USER_BAN))]
```

Because `checker` depends on `get_current_user`, every route that declares a permission is authenticated first (steps 1–2 of Figure 5).

**Ownership in queries.** Ownership is part of the query, not checked afterwards on a list:

- Personal records: `select(StudyRecord).where(StudyRecord.group_id.is_(None), StudyRecord.created_by_id == user.id)` (`record_service.list_personal`).
- My groups: a join on `GroupMembership.user_id == user.id` (`group_service.list_my_groups`).
- Dashboard: `visible_records_query(user)` limits results to own personal records and groups the user is a member of.
- Single-resource reads (`load_for_user`, `load_for_member`, `revoke_session`) load by id **and** compare the owner or membership before returning. A mismatch returns the same 404 as a missing row, so ids cannot be probed (no IDOR).

**Adding a new role or permission.**

1. Permission: add a member to the `Permission` enum, add it to the right set in `ROLE_PERMISSIONS`, and declare `Depends(require_permission(Permission.NEW))` on the route. `test_rbac.py` checks the map and that every admin route is refused to users.
2. Role (e.g. `moderator`): add a constant to `constants.py` and to `ROLES`, add a `ROLE_PERMISSIONS` entry, write an Alembic migration that updates the CHECK constraint `ck_users_role_allowed`, and extend `RoleChangeIn.role` and the frontend `Role` type.

**Special rules.**

- **Admins** pass every `require_permission` check, but `admin_service` adds the self-protection rules in Table 12. Group endpoints do not use role permissions for membership, so admins have no implicit access inside groups.
- **Banned users** are refused in `get_current_user` (403) before any permission is evaluated, refused at login (`auth_service.login`) and at refresh (`session_service.rotate`, which also revokes the session). Banning revokes all sessions as well.

### C8. Admin Dashboard Design

**Figure 6: Admin pages and the endpoints they call**

```mermaid
flowchart LR
  OV["/admin<br/>Overview"] --> E1["GET /api/admin/overview"]
  US["/admin/users<br/>Users"] --> E2["GET /api/admin/users"]
  US --> E3["POST /api/admin/users/bulk-ban<br/>POST /api/admin/users/bulk-unban"]
  US --> X1["GET /api/admin/exports/users.csv"]
  UD["/admin/users/:id<br/>User detail"] --> E4["GET /api/admin/users/{id}"]
  UD --> E5["POST .../ban, .../unban<br/>PATCH .../role"]
  UD --> E6["DELETE .../sessions/{sid}<br/>POST .../sessions/revoke-all"]
  CO["/admin/content<br/>Records and groups"] --> E7["GET /api/admin/records<br/>GET /api/admin/groups/{id}"]
  CO --> E8["POST /api/admin/records/bulk-delete<br/>POST /api/admin/groups/bulk-delete"]
  CO --> X2["GET /api/admin/exports/records.csv"]
  AU["/admin/audit<br/>Activity log"] --> E9["GET /api/admin/audit-logs<br/>GET /api/admin/audit-actions"]
  AU --> X3["GET /api/admin/exports/audit-logs.csv"]
  SE["/admin/security<br/>Security"] --> E10["GET /api/admin/security/failed-logins"]
```

**Table 29: Admin pages**

| Page (file) | Endpoints | Filters and pagination | Actions | Audit events written |
|---|---|---|---|---|
| Overview `/admin` (`AdminOverviewPage.tsx`) | `GET /api/admin/overview` | — | Links to the other pages | — (read only) |
| Users `/admin/users` (`AdminUsersPage.tsx`) | `GET /api/admin/users`, `POST /bulk-ban`, `POST /bulk-unban`, `GET /exports/users.csv` | `q` (email/name), role, account type, status; `page`, `page_size` | Select rows → bulk ban / bulk unban with one reason; export CSV | `user_banned` / `user_unbanned` per affected user; `export` |
| User detail `/admin/users/:id` (`AdminUserDetailPage.tsx`) | `GET /api/admin/users/{id}`, `POST /ban`, `POST /unban`, `PATCH /role`, `DELETE /sessions/{sid}`, `POST /sessions/revoke-all` | — (shows 20 records and 20 recent events, link to the audit log filtered by user) | Ban/unban with reason (`PromptDialog`); change role; revoke one or all sessions. The UI hides ban for admins and role change for self, and the backend enforces both. | `user_banned`, `user_unbanned`, `role_changed`, `session_revoked` |
| Content `/admin/content` (`AdminContentPage.tsx`) | `GET /api/admin/records`, `GET /api/admin/groups`, `GET /api/admin/groups/{id}`, `POST /records/bulk-delete`, `POST /groups/bulk-delete`, `GET /exports/records.csv` | Records: `q`, status, scope, `group_id`; groups: `q`; both paginated | View group detail with members; delete one or many records/groups; export records CSV | `record_deleted` / `group_deleted` with `by_admin`; `export` |
| Activity log `/admin/audit` (`AdminAuditPage.tsx`) | `GET /api/admin/audit-logs`, `GET /api/admin/audit-actions`, `GET /exports/audit-logs.csv` | `q`, action, `user_id`, `date_from`, `date_to`; `page_size` 25 | Export CSV; times shown in the viewer's timezone | `export` |
| Security `/admin/security` (`AdminSecurityPage.tsx`) | `GET /api/admin/security/failed-logins?hours=` | Time window `hours` (1–720) | — | — (read only) |

**Bulk results.** Each bulk endpoint de-duplicates the ids (`dict.fromkeys`), processes each one, and returns `{"results": [{"id": 5, "result": "done"}, {"id": 1, "result": "skipped_admin"}, …], "done": n}`. The results are `done`, `not_found`, `skipped_self`, `skipped_admin` and `already_done`. The Users page shows "N user(s) banned, M skipped (administrators, yourself or no change needed)"; the Content page shows "N record(s)/group(s) deleted". All changes are committed in one transaction at the end, and each affected item gets its own audit row.

**CSV exports follow the filters.** The list endpoints and the export endpoints use the same FastAPI dependencies (`routers/admin_filters.py`: `UserFilterParams`, `RecordFilterParams`, `AuditFilterParams`) and the same query builders (`admin_service.user_query`, `record_query`, `audit_query`). The frontend's `exportCsv(kind, query)` sends the page's current filter values without `page`/`page_size`. An export therefore contains exactly the rows the filtered list shows, up to 10 000 rows. `export_service.safe_cell` prefixes cells starting with `=`, `+`, `-`, `@`, tab or CR with `'` to stop formula injection. Each export writes an `export` audit row with the kind, the filters used and the row count.

### C9. Security Design and Threats

**Table 30: Threats, defences and code locations**

| Threat | Defence | File or module |
|---|---|---|
| Password database leak | Argon2id (memory-hard) over `HMAC-SHA256(pepper, password)`. The pepper is only in the environment, so the DB alone is not enough to start guessing. Refresh and reset tokens are stored only as SHA-256 hashes. Hashes are rehashed when parameters change. | `core/security.py`, `models/session.py`, `models/password_reset.py` |
| Stolen access token | 15-minute lifetime; kept in memory, not `localStorage`; the `sid` check makes logout, revocation, password change and ban effective immediately; the role is compared with the DB | `config.py`, `core/dependencies.get_current_user`, `apiClient.ts` |
| Stolen refresh token | `HttpOnly` (not readable by JS), `Secure`, `SameSite=Strict`, `Path=/api/auth`; rotation on every use; reuse after the 10-s window revokes the whole session and is audited | `routers/auth.py`, `services/session_service.rotate` |
| Brute-force login | DB-backed throttle per (account, IP) 5, per IP 20, per account 50 in 15 minutes → 429 with `Retry-After`; throttled attempts not counted; generic error; constant-ish timing for unknown emails; signup 10/IP/hour; reset 5/IP/hour and 3 emails/account/hour | `services/auth_service.py`, `constants.py`, `services/password_reset_service.py` |
| Privilege escalation | No `role` in `SignupIn` (`extra="forbid"`); role read from the DB, never from the client; central `ROLE_PERMISSIONS`; admins cannot change their own role; only `create_admin.py` or an existing admin grants admin | `schemas/auth.py`, `core/permissions.py`, `core/dependencies.py`, `services/admin_service.py`, `scripts/create_admin.py` |
| Access to another user's record (IDOR) | Ownership/membership inside queries; 404 for records, groups and sessions that are not the caller's; tutor edits limited by `crud.can_manage` | `services/record_service.py`, `services/group_service.py`, `routers/users.py`, `crud.py` |
| Cross-site scripting (XSS) | React escapes all output; production CSP `<meta>` (`script-src 'self'`, limited `connect-src`, `img-src` https); API responses have `default-src 'none'` and `nosniff` | `frontend/csp.ts`, `main.py` |
| Cross-site request forgery (CSRF) | Bearer tokens are not sent automatically by browsers; the cookie endpoints need `SameSite=Strict` and the `X-Requested-With: peerora` header | `routers/auth._require_csrf_header`, `config.py` |
| CORS misuse | Explicit origin list from `CORS_ORIGINS`; `*` is refused at startup; limited methods and headers; in production the SPA and API share one origin | `config.get_cors_origins`, `main.py` |
| Secrets in the repository | `.env` and `.env.*` git-ignored (except `.env.example`); secrets read from env only; error messages name the variable but never show its value; audit details strip secret-like keys | `.gitignore`, `config.py`, `services/audit_service.sanitize` |
| SQL injection | SQLAlchemy ORM with bound parameters throughout; `LIKE` search input escapes `%`, `_` and `\` | `services/admin_service._like`, `crud.py` |
| Over-posting of fields | Every request schema sets `extra="forbid"`; `ProfileUpdateIn` has no `role`/`account_type`; owner ids come from the token, not the body | `schemas/*.py` |
| CSV / formula injection | Cells beginning with `= + - @ \t \r` are prefixed with `'` | `services/export_service.safe_cell` |
| Information leakage in errors | Generic 500 handler; no stack traces; generic replies for login and password reset | `errors.py`, `auth_service.py`, `password_reset_service.py` |
| Clickjacking | `X-Frame-Options: DENY` and `frame-ancestors 'none'` on API responses | `main.security_headers` |
| Reset-token leakage | The token travels in the URL fragment (`#token=`), which is not sent to servers; the frontend removes it from the address bar; it is single-use, valid for 30 min and never logged | `password_reset_service.py`, `ResetPasswordPage.tsx` |

### C10. Deployment on Vercel

**Figure 7: Deployment layout**

```mermaid
flowchart TB
  GH["GitHub repository<br/>Mushfika491/Peerora (main)"] -->|"push / redeploy"| V
  subgraph V["Vercel project (vercel.json services)"]
    direction LR
    RW{{"rewrites<br/>/api/(.*) → backend<br/>/(.*) → frontend"}}
    FES["frontend service<br/>root: frontend, framework: vite<br/>SPA rewrite → /index.html"]
    BES["backend service<br/>root: backend, framework: fastapi<br/>entrypoint main:app<br/>installs requirements.txt"]
    RW --> FES
    RW --> BES
  end
  BES -->|"DATABASE_URL<br/>transaction pooler :6543"| SB[("Supabase PostgreSQL<br/>RLS enabled")]
  ENV[["Environment variables<br/>(Vercel → Settings)"]] -.-> BES
```

**Projects and build settings.** `vercel.json` defines two **services** in one Vercel project:

- `frontend`: root `frontend`, framework `vite` (build `tsc && vite build`, output `dist`), with a rewrite of `/(.*)` to `/index.html` for client-side routing. The CSP `<meta>` is injected at build time.
- `backend`: root `backend`, framework `fastapi`, entrypoint `main:app`. Vercel installs `backend/requirements.txt`.

The top-level rewrites send `/api/(.*)` to the backend and everything else to the frontend. Both services are deployed as **one Vercel project** and share one origin, <https://peerora-uni.vercel.app/>: the SPA is served at `/` and the API at `/api` (checked on 28 November 2026; see S18/S19).

**How the frontend finds the API.** `VITE_API_BASE_URL` is left **unset** on Vercel, so `apiClient.ts` calls `/api/...` on the same origin. Because they share an origin, the `SameSite=Strict` cookie works and CORS is not needed. In development, Vite proxies `/api` to `http://localhost:8000` (`VITE_DEV_API_TARGET`).

**Hosted database.** Supabase PostgreSQL, reached through the transaction pooler (port 6543). The schema is created by Alembic (`alembic upgrade head`). The production database was migrated to the head revision `0008_secure_alembic_version` on 24 November 2026, after a `pg_dump` backup was taken.

**Table 31: Environment variables** (names only; values are never committed)

| Variable | Service | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | Supabase PostgreSQL connection string (`postgresql://…`, rewritten to `postgresql+psycopg://`) |
| `JWT_SECRET_KEY` | backend | HS256 signing key, ≥ 32 characters (required) |
| `PASSWORD_PEPPER` | backend | Password pepper, ≥ 16 characters (required; must never change after users exist) |
| `ACCESS_TOKEN_MINUTES` | backend | Access-token lifetime, default 15, capped at 15 |
| `REFRESH_TOKEN_DAYS` | backend | Session/refresh lifetime, default 7 |
| `COOKIE_SECURE` | backend | `Secure` cookie flag, default `true`; set `false` only for local http |
| `TRUST_PROXY_HEADERS` | backend | Read the client IP from `X-Forwarded-For`; on automatically when `VERCEL=1` |
| `CORS_ORIGINS` | backend | Comma-separated allowed origins (no `*`) |
| `EMAIL_BACKEND` | backend | `smtp` (production), `outbox` (local only) or unset (reset unavailable) |
| `PUBLIC_APP_URL` | backend | Frontend base URL used in reset links (required in production for reset email) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_STARTTLS`, `SMTP_SSL`, `EMAIL_FROM` | backend | SMTP delivery for password-reset email |
| `EMAIL_OUTBOX_DIR`, `EMAIL_OUTBOX_ALLOW_REMOTE_DB` | backend (local only) | Development outbox settings; refused on Vercel |
| `VERCEL` | backend | Set by the platform (`1`); enables proxy trust and forbids the outbox |
| `VITE_API_BASE_URL` | frontend (build) | Leave unset on Vercel (same origin) |
| `VITE_DEV_API_TARGET` | frontend (dev only) | Where the Vite dev proxy forwards `/api` |

The production Vercel project sets exactly three variables: `DATABASE_URL`, `JWT_SECRET_KEY` and `PASSWORD_PEPPER`, all for the Production environment (S19, values hidden). Every other variable uses its default. Token lifetimes are 15 minutes and 7 days, `COOKIE_SECURE` is `true`, and proxy headers are trusted because Vercel sets `VERCEL=1`. CORS is not needed on the same origin. `EMAIL_BACKEND` and `PUBLIC_APP_URL` are not set, so password-reset email is switched off on the live site: `GET /api/auth/password-reset/availability` returns `{"available": false}` (see E3).

**How to redeploy.**

1. Back up the database before any schema change.
2. If there are new migrations, run `alembic upgrade head` from `backend/` against the production `DATABASE_URL` (review with `alembic upgrade head --sql` first).
3. Push or merge to the production branch, or click **Redeploy** in the Vercel dashboard. Vercel rebuilds both services.
4. Check `/api/health`, `/api/docs` and a login. `backend/tests/live_smoke_test.py` runs read-only checks plus a login → refresh → logout cycle against a deployment.

### C11. Testing

**Strategy.**

- **Automated API tests (backend).** 17 modules under `backend/tests/`. Each test runs the real FastAPI app with `TestClient` on a **fresh in-memory SQLite database** with foreign keys enabled (`tests/base.py`). Test-only secrets are set before import, and Supabase is never touched.
- **Automated component tests (frontend).** Vitest + Testing Library in jsdom: route guards, auth context (restore, refresh-and-retry, suspended sign-out), group permission UI, record form, admin user detail restrictions, password reset pages, validation and the CSP helper.
- **Manual end-to-end tests.** `docs/MANUAL_TEST_CHECKLIST.md`, executed on 24 November 2026 and reported in `docs/PHASE3_E2E_TEST_REPORT.md`. That run used a local frontend and backend connected to the Supabase database, in isolated headless Chrome profiles. On 28 November 2026 the main flows were also run by hand on the **live Vercel site** and recorded as screenshots S1–S17 (Part D): signup validation, records, password change, session revoke, group permissions, RBAC 403, token expiry 401, refresh and cookie, ban → `account_suspended`, admin pages, bulk delete, failed-login view and CSV export. Every result matched the expected behaviour.
- **Live smoke test.** `backend/tests/live_smoke_test.py` against a running deployment. Run against <https://peerora-uni.vercel.app> on 28 November 2026: all 8 public checks passed (health, `/api/docs`, tutor list hides Student IDs, `X-Total-Count`, protected and admin routes return 401 without a token, forged token returns 401). The optional login → refresh → logout cycle was not part of this run.

**How to run.**

```bash
# Backend (from backend/, virtual environment active)
pip install -r requirements-dev.txt
python -m pytest tests                 # or: python -m pytest tests --cov=peerora

# Frontend (from frontend/)
npm install
npm run test                           # Vitest
npm run build                          # type-check + production build
```

**Results** (run on 28 November 2026, Python 3.14.4, pinned dependencies):

- Backend: **199 passed, 170 subtests passed** in about 32 s. Line coverage of `peerora/`: **98 %** (2300 statements, 53 missed).
- Frontend: **83 tests passed in 21 files**.

**Table 32: Automated test results (selected tests by requirement)**

| Test | Requirement | Result |
|---|---|---|
| `test_tokens.py::test_expired_token_returns_401` | FR-AUTH-05/06 (expiry) | Pass |
| `test_tokens.py::test_tampered_token_returns_401` | FR-AUTH-06 (tampering) | Pass |
| `test_tokens.py::test_token_signed_with_another_key_returns_401` | FR-AUTH-06 | Pass |
| `test_tokens.py::test_unsigned_none_algorithm_token_returns_401` | FR-AUTH-06 | Pass |
| `test_tokens.py::test_token_for_revoked_session_returns_401` | FR-AUTH-06/11 | Pass |
| `test_tokens.py::test_token_with_outdated_role_returns_401` | FR-RBAC-14 | Pass |
| `test_tokens.py::test_banned_user_is_rejected_on_next_request` | FR-RBAC-13 | Pass |
| `test_config.py::test_access_token_lifetime_is_capped_at_15_minutes` | FR-AUTH-05 | Pass |
| `test_sessions.py::test_refresh_rotates_the_token` | FR-AUTH-07 | Pass |
| `test_sessions.py::test_reusing_a_rotated_token_revokes_the_whole_session` | FR-AUTH-08 | Pass |
| `test_sessions.py::test_concurrent_refresh_within_grace_window_keeps_the_session` | FR-AUTH-08 | Pass |
| `test_sessions.py::test_cannot_revoke_another_users_session` | FR-AUTH-11 (ownership) | Pass |
| `test_auth.py::test_admin_cannot_be_chosen_at_signup` | FR-AUTH-01 | Pass |
| `test_auth.py::test_password_is_hashed_with_argon2_and_pepper` | FR-AUTH-03 | Pass |
| `test_auth.py::test_wrong_password_and_unknown_email_look_the_same` | FR-AUTH-04 | Pass |
| `test_auth.py::test_logout_and_refresh_require_the_csrf_header` | FR-AUTH-10 | Pass |
| `test_auth.py::test_change_password_signs_out_other_sessions` | FR-AUTH-15 | Pass |
| `test_rate_limit.py::test_account_is_throttled_from_the_attacking_address` | FR-AUTH-12 (lockout) | Pass |
| `test_rate_limit.py::test_owner_can_still_log_in_from_another_network` | FR-AUTH-12 | Pass |
| `test_rate_limit.py::test_hammering_while_throttled_does_not_build_a_global_lockout` | FR-AUTH-12 | Pass |
| `test_rate_limit.py::test_signups_are_limited_per_address` | FR-AUTH-13 | Pass |
| `test_rbac.py::test_every_protected_route_requires_a_token` | FR-RBAC-03 | Pass |
| `test_rbac.py::test_every_admin_route_is_forbidden_for_normal_users` | FR-RBAC-04 | Pass |
| `test_records.py::test_personal_records_are_private` | FR-RBAC-05 (ownership) | Pass |
| `test_groups.py::test_non_members_cannot_see_anything` | FR-RBAC-07 | Pass |
| `test_group_permissions.py::test_create_permission_alone` | FR-RBAC-09 (matrix) | Pass |
| `test_group_permissions.py::test_update_permission_alone` | FR-RBAC-09 (matrix) | Pass |
| `test_group_permissions.py::test_assign_permission_alone` | FR-RBAC-09 (matrix) | Pass |
| `test_group_permissions.py::test_assignee_can_always_update_status_only` | FR-RBAC-10 | Pass |
| `test_group_permissions.py::test_only_the_owner_can_change_permissions` | FR-RBAC-11 | Pass |
| `test_group_permissions.py::test_revoking_a_permission_takes_effect_immediately` | FR-RBAC-15 | Pass |
| `test_tutor_ownership.py::test_another_tutor_cannot_edit_or_delete` | FR-RBAC-06 | Pass |
| `test_admin_users.py::test_admin_cannot_ban_another_admin_or_themself` | FR-RBAC-12 (admin rules) | Pass |
| `test_admin_users.py::test_admin_cannot_change_own_role` | FR-RBAC-12 (admin rules) | Pass |
| `test_admin_users.py::test_ban_requires_reason_revokes_sessions_and_is_audited` | FR-ADM-04 | Pass |
| `test_admin_users.py::test_bulk_ban_skips_admins_and_self` | FR-ADM-07 | Pass |
| `test_admin_users.py::test_search_filters_and_pagination` | FR-ADM-02 | Pass |
| `test_admin_content.py::test_delete_single_and_bulk_records` | FR-ADM-08 | Pass |
| `test_audit.py::test_text_search_matches_user_emails_and_keeps_filters` | FR-ADM-09 | Pass |
| `test_audit.py::test_failed_login_report_groups_by_ip_and_account` | FR-ADM-10 | Pass |
| `test_audit.py::test_sensitive_keys_are_never_stored` | FR-ADM-12 | Pass |
| `test_exports.py::test_users_export_respects_filters` | FR-ADM-11 | Pass |
| `test_exports.py::test_formula_cells_are_escaped` | FR-ADM-11 | Pass |
| `test_password_reset.py::test_token_cannot_be_reused` | FR-AUTH-16 | Pass |
| `AuthContext.test.tsx` › refreshes an expired access token once and retries the request | FR-AUTH-17 | Pass |
| `AuthContext.test.tsx` › signs a suspended user out and redirects to the login page | FR-RBAC-13 | Pass |
| `AuthContext.test.tsx` › does NOT sign the user out for an ordinary permission error | FR-RBAC-13 | Pass |
| `GroupDetailPage.test.tsx` › owner can toggle each member permission independently | FR-RBAC-09/11 | Pass |
| `AdminUserDetailPage.test.tsx` › cannot ban another administrator | FR-RBAC-12 | Pass |

Test files and counts: `test_password_reset` 24, `test_tutors_api` 19, `test_auth` 16, `test_config` 14, `test_records` 14, `test_group_permissions` 13, `test_timestamps_and_browser` 13, `test_admin_users` 11, `test_groups` 11, `test_tokens` 11, `test_sessions` 10, `test_tutor_ownership` 10, `test_rbac` 9, `test_rate_limit` 8, `test_admin_content` 6, `test_audit` 5, `test_exports` 5 (total 199).

---

## Part D. Evidence: Screenshots of the Running Application

All screenshots were taken on 28 November 2026 on the deployed site <https://peerora-uni.vercel.app/>, using demo accounts (admin1 and Student1). They were captured with Google Chrome 156 in headless mode, so the strip above each page shows the page URL rather than Chrome's own address bar. The Network and Application panels are the real Chrome DevTools, attached to the same tab. Access tokens, refresh-cookie values and the `Authorization` header are covered with **MASKED** boxes. The image files are in `docs/screenshots/`.

### D1. User Side

> **S1: Signup and login with a validation error.**
>
> ![S1](screenshots/S01-signup-validation.png)
>
> *Shows:* `/signup` (Student/Tutor choice only, no admin option) rejecting a 3-character password with "Password must be at least 8 characters." · *Requirements:* FR-AUTH-01, FR-AUTH-02, FR-AUTH-04

> **S2: A logged-in user's own records.**
>
> ![S2](screenshots/S02-own-records.png)
>
> *Shows:* `/records` of Student1 listing only that user's two personal records; the user's name is in the sidebar. · *Requirements:* FR-RBAC-05, FR-DOM-06, FR-DOM-08

> **S3: Profile and change password, wrong current password rejected.**
>
> ![S3](screenshots/S03-change-password-rejected.png)
>
> *Shows:* `/account` → Password: the change is refused with "Current password is incorrect." · *Requirements:* FR-AUTH-14, FR-AUTH-15

> **S4: Sessions list with revoke.**
>
> ![S4](screenshots/S04-sessions-revoke.png)
>
> *Shows:* `/account` → Active sessions with three devices, the "This device" marker and Revoke; after confirming, the other device's session is ended. · *Requirements:* FR-AUTH-11

> **S5: Group page with members and permissions.**
>
> ![S5](screenshots/S05-group-members-permissions.png)
>
> *Shows:* `/groups/3` as the owner: members with their Create / Update / Assign toggles and derived labels (Owner, Member, Editor). · *Requirements:* FR-RBAC-08, FR-RBAC-09, FR-RBAC-11, FR-DOM-04

> **S6: An action denied by RBAC.**
>
> ![S6](screenshots/S06-rbac-denied-403.png)
>
> *Shows:* A student opening `/admin` gets the in-app "You do not have access to this page" screen. The admin API, called with that student's own token, answers **403 Forbidden** `{"detail": "You do not have permission to perform this action."}` in the Network tab. · *Requirements:* FR-RBAC-02, FR-RBAC-04, FR-RBAC-09

### D2. Security Behaviour

> **S7: Authorization header and expired token returning 401.**
>
> ![S7](screenshots/S07-bearer-and-expired-401.png)
>
> *Shows:* The request carries `Authorization: Bearer …` (masked). The same access token, used again after its 15-minute lifetime, is answered with **401** `Your session token is invalid or has expired.` and `WWW-Authenticate: Bearer`. The `X-Vercel-Id` timestamps put the two requests at 12:28:08 and 12:43:23 UTC. Vercel's `Date` header is cached per function instance, so it is not a reliable clock here. · *Requirements:* FR-AUTH-05, FR-AUTH-06, FR-RBAC-03

> **S8: Refresh returning a new access token, and the HttpOnly cookie.**
>
> ![S8](screenshots/S08-refresh-and-httponly-cookie.png)
>
> *Shows:* `POST /api/auth/refresh` → 200 with a new `access_token` (masked, `expires_in: 900`) and a rotated `Set-Cookie`. DevTools → Application → Cookies shows `peerora_refresh` with HttpOnly ✓, Secure ✓, SameSite Strict, Path `/api/auth` (value masked). · *Requirements:* FR-AUTH-07, FR-AUTH-17

> **S9: A banned user rejected on the next request.**
>
> ![S9](screenshots/S09-banned-user-rejected.png)
>
> *Shows:* After the admin bans Student1, the student's next request returns **403** with `X-Error-Code: account_suspended`, and the app returns to `/login` with the suspension message. · *Requirements:* FR-RBAC-13

### D3. Admin Dashboard

> **S10: Overview statistics.**
>
> ![S10](screenshots/S10-admin-overview.png)
>
> *Shows:* `/admin` stat cards: users, banned users, new users in 7 days, records, groups, tutor profiles, administrators. · *Requirements:* FR-ADM-01

> **S11: Users list with search, filters and pagination.**
>
> ![S11](screenshots/S11-admin-users-filters.png)
>
> *Shows:* `/admin/users` searched for "student", filtered to Role = User and Status = Active, with two rows selected (bulk Ban / Unban bar) and the pagination control. · *Requirements:* FR-ADM-02, FR-ADM-07

> **S12: User detail with sessions and recent activity.**
>
> ![S12](screenshots/S12-admin-user-detail.png)
>
> *Shows:* `/admin/users/8`: actions (ban, promote, revoke all), account facts, groups, active sessions with Revoke, records and recent activity with IP and time. · *Requirements:* FR-ADM-03, FR-ADM-05, FR-ADM-06

> **S13: Ban dialog with a reason, then the banned state.**
>
> ![S13](screenshots/S13-ban-dialog-and-banned.png)
>
> *Shows:* The ban dialog asking for a reason, then the user shown as **Banned** with the reason and date. · *Requirements:* FR-ADM-04, FR-RBAC-12

> **S14: Records and groups moderation with filters and a bulk action.**
>
> ![S14](screenshots/S14-content-moderation-bulk.png)
>
> *Shows:* `/admin/content` filtered by search, status (To do) and type (Personal); two records selected and bulk-deleted, with the result toast "2 record(s) deleted." · *Requirements:* FR-ADM-08

> **S15: Activity log with filters, showing the events from the steps above.**
>
> ![S15](screenshots/S15-activity-log-filtered.png)
>
> *Shows:* `/admin/audit?user_id=2` (admin1 as actor or target), showing the events from S13, S14 and S17 (`user banned` with `sessions_revoked`, `user unbanned`, `export` with its filters and row count, `record deleted`) with IP, browser and time. · *Requirements:* FR-ADM-09

> **S16: Security view with failed logins by IP and by account.**
>
> ![S16](screenshots/S16-security-failed-logins.png)
>
> *Shows:* `/admin/security`, last 7 days: failed logins by IP address and by account, and the most recent failures with reason, IP and browser. · *Requirements:* FR-ADM-10, FR-AUTH-12

> **S17: A CSV export downloaded and opened.**
>
> ![S17](screenshots/S17-csv-export.png)
>
> *Shows:* The filtered users list exported as `peerora-users-20261128-123310.csv`. The downloaded file holds the same 6 rows. LibreOffice Calc is not installed on the capture machine, so the file is shown in a simple grid view. · *Requirements:* FR-ADM-11

### D4. Deployment

> **S18: Vercel frontend project with the production deployment and domain.**
>
> ![S18](screenshots/S18-vercel-project.png)
>
> *Shows:* the `peerora` Vercel project's Production Deployment: status **Ready**, domain `peerora-uni.vercel.app`, source branch `main`, commit `14a8921` "fix: handle missing and invalid API URL in CSP generation", created 25 Nov by Mushfika491. The frontend and API are one project (C10). · *Requirements:* C10

> **S19: Vercel API project with environment variable names (values hidden).**
>
> ![S19](screenshots/S19-vercel-env-vars.png)
>
> *Shows:* Settings → Environment Variables of the same project: `DATABASE_URL`, `JWT_SECRET_KEY` and `PASSWORD_PEPPER` for Production, values hidden (lock icons). No secret is in the repository. · *Requirements:* C10, NFR-01

> **S20: Live API documentation page.**
>
> ![S20](screenshots/S20-api-docs.png)
>
> *Shows:* <https://peerora-uni.vercel.app/api/docs>: Swagger UI for Peerora API 2.0.0 (OAS 3.1) with the endpoint groups. · *Requirements:* C5

### D5. Tests

> **S21: Test run output.**
>
> ![S21](screenshots/S21-test-results.png)
>
> *Shows:* `python -m pytest tests`: **199 passed**. `npm run test`: **21 test files, 83 tests passed**. Both run on 28 November 2026. · *Requirements:* C11, NFR-13

---

## Part E. Project Management and Conclusion

### E1. How to Run and Test

**Prerequisites:** Git, Python 3.11 or newer, Node.js (LTS) with npm, and a PostgreSQL database (the project uses a Supabase project; any PostgreSQL works for local development).

**1. Clone**

```bash
git clone https://github.com/Mushfika491/Peerora.git
cd Peerora
```

**2. Backend environment file.** Copy `backend/.env.example` to `backend/.env` (git-ignored) and fill in values. Example placeholders (never commit real values):

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
JWT_SECRET_KEY=<at least 32 random characters>
PASSWORD_PEPPER=<at least 16 random characters>
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=7
COOKIE_SECURE=false            # local http only
CORS_ORIGINS=http://localhost:5173
# EMAIL_BACKEND=outbox         # optional, local password-reset testing
```

Generate a secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

**3. Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head                   # creates/updates the schema
python -m scripts.create_admin --email <admin email> --name "<name>" --account-type student
python -m scripts.seed_demo            # optional demo data; asks for passwords at hidden prompts
fastapi dev main.py                    # API on http://localhost:8000, docs at /api/docs
```

**4. Frontend** (second terminal)

```bash
cd frontend
cp .env.example .env                   # leave VITE_API_BASE_URL empty
npm install
npm run dev                            # http://localhost:5173 (proxies /api to :8000)
```

**5. Tests**

```bash
cd backend && python -m pytest tests   # in-memory SQLite; never touches the real database
cd frontend && npm run test && npm run build
```

**6. Logging in with the test accounts.** Use one **admin** account (opens the Administration area at `/admin`) and one **user** account (Student or Tutor; opens `/dashboard/student` or `/dashboard/tutor`). The test account user IDs and passwords are in the PDF report (Appendix), never in this file.

### E2. GitHub Work

**Table 33: Pull requests and what they delivered** (from the repository's merge commits)

| Issue | Pull request | Title / branch | What it delivered |
|---|---|---|---|
| [#2](https://github.com/Mushfika491/Peerora/issues/2) | [#3](https://github.com/Mushfika491/Peerora/pull/3) | `docs/2-mvp-for-peerora-app-docs` | PRD, SRS and TDD planning documents (`docs/01-prd.md`, `02-srs.md`, `03-tdd.md`) |
| [#4](https://github.com/Mushfika491/Peerora/issues/4) | [#5](https://github.com/Mushfika491/Peerora/pull/5) | `feature/mvp-tutor-profile-management` | Mid-assessment MVP: tutor profile CRUD (FastAPI + Supabase) and the React tutor pages |
| [#6](https://github.com/Mushfika491/Peerora/issues/6) | [#7](https://github.com/Mushfika491/Peerora/pull/7) | `feature/complete-auth-rbac-admin-group-management` | Final features: JWT auth and sessions, RBAC, study groups and records, admin dashboard, audit log, exports, password reset, migrations 0002–0008, tests |
| — | direct commits on `main` | `dc5424b`, `db8c9e3`, `1735c92`, `09873b3` | Vercel SPA routing, API path fix, API docs routes, CSP handling of a missing/invalid API URL |

Each pull request closes its issue (`Closes #2`, `Closes #4`, `Closes #6` in the PR descriptions). JWT authentication, RBAC and the admin dashboard were delivered together under issue #6, "feat: implement authentication, RBAC, admin, and group collaboration", and PR #7 (merged 25 November 2026).

**Authorship and timeline.** All 15 commits in the repository are by the author (Git names `Mushfika` and `Mushfika491`). The work over time:

| Period | Work |
|---|---|
| 3 Oct 2026 | Repository created |
| 12–13 Oct 2026 | Planning documents (PR #3) |
| 1–6 Nov 2026 | MVP tutor CRUD, Vercel routing and API fixes (PR #5 and follow-up commits) |
| up to 25 Nov 2026 | Authentication, RBAC, groups/records, admin dashboard, audit, exports, password reset and tests, committed as `b06d321` and merged in PR #7 |
| 25 Nov 2026 | README/TDD database documentation, CSP fix `09873b3` |

### E3. Limitations

1. **Limited testing on the live site.** The deployment at <https://peerora-uni.vercel.app/> passes the public live smoke test. However, the full manual E2E run (`docs/PHASE3_E2E_TEST_REPORT.md`) used a local frontend and backend against the hosted database, not the Vercel site. On the live site, the remaining checks are covered only by the Part D screenshots. Response times are about 1 second and can be slower on a serverless cold start (NFR-06).
2. **Refresh-reuse grace window.** A refresh token stolen and replayed within 10 seconds of a legitimate rotation receives a fresh token instead of revoking the session. This is a deliberate trade-off so that two tabs do not log each other out.
3. **Throttle limits.** Login throttling is stored in the database. It adds a few `COUNT` queries per login. An attacker who controls 10 or more IP addresses can reach the per-account limit of 50 and lock that account for 15 minutes.
4. **Admins can demote other admins.** Admins cannot ban another admin, but any admin can change another admin's role to `user` and then ban them. Both steps are audited. There is no super-admin tier and no "last admin" protection.
5. **The frontend CSP is a `<meta>` tag.** It cannot set `frame-ancestors`, so the SPA itself relies on Vercel's defaults for framing protection. The API sends `X-Frame-Options: DENY`.
6. **Pepper rotation is not supported.** Changing `PASSWORD_PEPPER` invalidates every stored password.
7. **Password-reset email is not configured on the live site.** The reset flow is built and tested (`test_password_reset.py`), but production sets no `EMAIL_BACKEND`/SMTP or `PUBLIC_APP_URL`, so the availability endpoint reports `available: false` and users cannot reset a forgotten password there.
8. **Not built:** real image upload (the stub is disabled), email verification at signup, notifications and real-time updates, and bookings.
9. **Manual checks not run** (from the E2E report): signup through the UI, the live 5-attempt lockout, two tabs refreshing at once, and the sidebar drawer at narrow widths. These behaviours are covered by automated tests only.
10. **Only basic performance figures.** Response times were sampled with `curl` once (about 0.65–1.0 s typical, with a cold-start outlier of 2.6 s; NFR-06). No load test was run.
11. **Admin CSV exports are capped** at 10 000 rows without telling the admin that the result was truncated.

### E4. Future Work

1. **Configure password-reset email in production** (`EMAIL_BACKEND=smtp`, SMTP settings, `PUBLIC_APP_URL`): users on the live site can't recover a forgotten password yet.
2. **Protect the last administrator and require a reason for role changes**: this closes the admin-demotes-admin gap in E3.4.
3. **Send the SPA's security headers from Vercel** (`frame-ancestors`, HSTS) through `vercel.json` headers: the `<meta>` CSP has limits.
4. **Report export truncation** with a header or row count when the 10 000-row cap is hit: admins should know when data is missing.
5. **Email verification at signup**: it confirms that users own their university email.
6. **Real profile-picture storage** (e.g. Supabase Storage with signed uploads): completes the disabled upload stub.
7. **Move the login throttle to a shared cache with sliding windows** (e.g. Redis/Upstash): reduces database load per login.
8. **Notifications for new assignments and permission changes**: group members learn about changes without reloading.
9. **Add a simple load test on Vercel** and reduce cold starts: turns the one-off NFR-06 sample into a repeatable measurement.

### E5. Sources, Libraries and Tools

**Table 34: Sources, libraries and tools**

| Name | Version or link | Used for |
|---|---|---|
| FastAPI (`fastapi[standard]`) | 0.165.0 · <https://fastapi.tiangolo.com> | Backend framework, dependency-based auth, OpenAPI docs |
| Pydantic | v2 (with FastAPI) · <https://docs.pydantic.dev> | Request/response validation |
| SQLAlchemy | 2.1.9 · <https://docs.sqlalchemy.org> | ORM and queries |
| psycopg | 3.3.9 · <https://www.psycopg.org/psycopg3/> | PostgreSQL driver |
| Alembic | 1.20.1 · <https://alembic.sqlalchemy.org> | Database migrations |
| PyJWT | 2.15.1 · <https://pyjwt.readthedocs.io> | Access-token signing and verification |
| argon2-cffi | 25.1.0 · <https://argon2-cffi.readthedocs.io> | Argon2id password hashing |
| pytest, pytest-cov | 9.2.0, 7.1.0 | Backend tests and coverage |
| React, React DOM | 18.3.1 · <https://react.dev> | Frontend UI |
| React Router | 6.30.6 · <https://reactrouter.com> | Routing and guards |
| TypeScript | 5.6.3 | Static typing |
| Vite, @vitejs/plugin-react | 5.4.21, ^4.3.4 · <https://vite.dev> | Dev server, build, CSP plugin |
| Vitest, Testing Library, jsdom | 2.1.9, ^16.1.0 / ^10.4.0, ^25.0.1 | Frontend tests |
| Supabase (PostgreSQL) | <https://supabase.com/docs> | Hosted database |
| Vercel | <https://vercel.com/docs> | Hosting of the SPA and the FastAPI service |
| RFC 7519 / RFC 8725 | <https://www.rfc-editor.org/rfc/rfc7519> | JWT format and best practices |
| OWASP ASVS 4.0 and Cheat Sheets | <https://owasp.org/www-project-application-security-verification-standard/> | Password storage, session management, CSRF, CSV injection guidance |
| MDN Web Docs | <https://developer.mozilla.org> | Cookies (`SameSite`, `HttpOnly`), Web Locks API, CSP |
| Git, GitHub | <https://github.com/Mushfika491/Peerora> | Version control, pull requests |
| VS Code | — | Editor |
| Google Chrome / Brave DevTools | — | Network and Application tab inspection, manual testing |
| AI assistant: Claude Code (Anthropic) | `[NEEDS INPUT]`: confirm which parts | `[NEEDS INPUT]` State which parts AI helped with (for example code generation, test writing, documentation, and drafting this report from the source code) and what you reviewed, tested or changed yourself. This report was drafted with Claude Code from the repository source and test runs, then reviewed by the author `[NEEDS VERIFICATION]`. |
