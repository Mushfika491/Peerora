# Peerora: Phase 3 manual end-to-end test report

**Date:** 24 November 2026 (UTC times unless stated; local time is UTC+6)
**Guide:** `docs/MANUAL_TEST_CHECKLIST.md`
**Environment:** local frontend `http://localhost:5173` (Vite) and backend `http://localhost:8000` (FastAPI), connected to the **existing Supabase PostgreSQL production database** (Alembic `0008_secure_alembic_version`). No SQLite was used for application operations.
**Method:** isolated headless Chrome profiles (not a personal browser) driven through the DevTools protocol, using the six demo accounts. Every database-writing step was approved before it ran, and each result was checked against Supabase with read-only queries.

## 1. Overall result

**No functional defects were found in Peerora.** Every tested checklist item passes. All failures seen during testing were traced to the test environment (an unstable network, or test-script timing and selectors) and were re-run successfully. Existing users and tutor profiles were preserved.

| Workflow | Checks | Result |
|---|---|---|
| Public pages (logged out) | 26 / 27 | ✅ (the one failure is the missing favicon, see §4) |
| Logged-in role access, all 6 demo accounts | 60 / 66, then the rest verified | ✅ |
| W1: revoke a leftover session (Account → Active sessions) | 4 / 4 | ✅ |
| W3a: password change (two browsers) | 14 / 14 | ✅ |
| W3b: password reset (outbox email) | 16 / 16 | ✅ |
| W3c: live session revocation (two browsers) | 8 / 8 | ✅ |
| W4: tutor profiles (redirect, validation, owner edit, admin moderation) | 20 / 20 | ✅ |
| W5: study groups, permissions, records (steps 5a–5g) | 84 / 86 | ✅ (2 misses were a database connection timeout) |
| W6: admin workflows (steps 6a–6g) | 87 / 87 | ✅ |

## 2. Checklist coverage

### 1. Public pages
- ✅ Home page: navbar (Home, Find Tutors, About, Login, Sign Up), all four sections, footer
- ✅ `/tutors`: search, subject, department and mode filters, filters kept in the URL
- ✅ Tutor detail as a guest: no Student ID, no Edit/Delete
- ✅ `/about` loads; unknown URLs show the 404 page
- ✅ `/dashboard`, `/groups` and `/admin` redirect to `/login?next=...`

### 2. Authentication
- ✅ Signup offers only Student and Tutor (no admin option)
- ✅ Reloading keeps the user signed in (all 6 accounts)
- ✅ Logout returns to `/`; Back and Refresh do not restore the session (all 6 accounts)
- ✅ Account → Password:
  - empty current password, weak new password and mismatched confirmation are refused
  - a wrong current password is rejected by the server ("Current password is incorrect.") with no write
  - after a change, the other browser is signed out on its next click; the old password fails and the new one works
- ✅ Password fields are hidden by default and have an eye toggle (keyboard toggling not exercised)
- ✅ The login page shows "Forgot password?"
- ✅ Reset request for an unknown email: same generic message, no email file written
- ✅ Reset request for a demo account: generic message, and exactly one `.eml` file in `backend/dev-outbox/` with a 30-minute link
- ✅ Opening the reset link: `#token=` disappears from the address bar; mismatched and weak passwords are refused
- ✅ After the reset: success toast, redirect to `/login`, new password works, old one fails, the other browser is signed out
- ✅ Opening the same reset link again: "invalid or has expired"
- ✅ Account → Active sessions: two browsers are listed; Revoke signs the other one out on its next click; "Sign out here" ends the current one
- ⚪ Not tested: signup flow and validation (would create accounts), the 5-attempt lockout, lockout from a different network, two tabs refreshing at once, `ACCESS_TOKEN_MINUTES=1`. Not applicable: the "without `EMAIL_BACKEND`" message (the outbox backend was active)

### 3. Dashboards and navigation
- ✅ Student and tutor sidebars match the checklist; tutors also have "My tutor profile"
- ✅ Admins land on `/admin` with the Administration section and "My dashboard"
- ✅ Students and tutors get the "no access" page for `/admin`, `/admin/users`, the other dashboard and `/tutors/new` (students)
- ✅ Public layout at 375, 768 and 1280 px: no horizontal overflow, menu button at narrow widths
- ⚪ Not tested: the logged-in sidebar drawer at narrow widths

### 4. Tutor profiles (demo profiles #7 and #8 only)
- ✅ A tutor who already has a profile opening `/tutors/new` is sent to the existing profile
- ✅ Owners see their Student ID and Edit/Delete; another tutor sees neither, and opening the other tutor's `/edit` URL is refused
- ✅ Edit validation ("Headline is required.", "CGPA must be between 0.00 and 4.00."), success toast, and delete confirmation (cancelled)
- ✅ An admin can edit any profile, and the Activity log shows "tutor profile moderated"
- All edits were reverted; both demo profiles match their original content checksums
- ⚪ Not tested: creating a profile (no demo tutor without one), image upload

### 5. Study groups and records (demo group "CSE309 Project Group")
- ✅ Owner adds members by email
- ✅ Members tab: Create/Update/Assign checkboxes, All/None buttons, and role badges
- ✅ Create only: "New record", no "Assigned to" field, no Edit button
- ✅ Update only: Edit, no "New record", no assignee field in the edit form
- ✅ Assign only: no Edit, so the title can't be changed
- ✅ Editor: creates, edits and assigns records; no Settings tab; can't change permissions
- ✅ Viewer: read-only, but can change the status of a record assigned to them
- ✅ Outsider: "Group not found"
- ✅ Personal records are private: the API returns 404 for another user's personal record
- ✅ Rename (then rename back), add then remove a member, create then delete a throwaway group
- ⚪ Not run, at the owner's choice: a member leaving the group

### 6. Admin dashboard
- ✅ Overview numbers match the database
- ✅ Users: search, role/type/status filters (kept in the URL), pagination, select-all
- ✅ Bulk ban requires a reason and skips admins; **bulk unban also requires a reason**
- ✅ User detail: groups, records, sessions, activity; ban and unban each need a reason (≥ 3 characters); role change (promote, then back); revoke one session and all sessions
- ✅ The Activity log shows the unban reason
- ✅ Admins can't ban themselves or another admin, or change their own role (UI disabled; API returns **403**)
- ✅ A banned user who is signed in is signed out on their next click, sees "Your account has been suspended…", and can't log in; after the unban they can log in again
- ✅ A normal "no permission" 403 doesn't sign the user out
- ✅ Content: search and scope/status filters; single and bulk delete with confirmation (throwaway records only)
- ✅ Activity log: filter by action, search by email, IP and browser columns, no passwords or tokens shown, timezone named ("Asia/Dhaka"; CSV in UTC)
- ✅ Security page: failed logins grouped by IP and by account
- ✅ CSV exports for users, records and the activity log follow the active filters; the activity-log CSV uses UTC (`+00:00`); each export appears in the Activity log
- ⚪ Not tested: the Brave versus Chrome browser names in log entries. *Update (25 Nov):* the Brave half is confirmed from real entries (#137–#141 show "Brave on Linux", see §4); a login from desktop Chrome is still needed to finish this item.

### 7. Integration and deployment
- ✅ `/api/docs` loads; API calls go to `/api/...` on the same origin
- ✅ Console: no application errors (only Vite dev-server noise and the expected 401s)
- ⚪ Production only, not tested: CSP check on the production build, refresh-cookie flags in production, `live_smoke_test.py` against a deployment

**Not part of the app:** booking and study-material workflows; the app has no such features.

## 3. Environment problems found during testing (not Peerora defects)
1. **Intermittent DNS failures for the Supabase pooler hostname** on the local Wi-Fi (other domains resolved fine). This caused HTTP 500s, failed logins and 30-second timeouts during the first runs.
   - **Workaround, applied to the running backend process only (no file changes):** a pinned connection address (libpq `hostaddr`) and a 30-second connect timeout.
2. **Slow connection to Supabase (about 1–5 s per request).** Some first-run checks read the page before it finished updating. They were re-run with explicit waits and passed.

## 4. Findings and recommendations
| # | Severity | Finding | Recommendation |
|---|---|---|---|
| 1 | Low | No favicon: `/favicon.ico` returns 404 (no icon link in `index.html`, no `public/` folder) | Add a favicon |
| 2 | Medium (observation) | A lost response during a token refresh can trigger "token reuse detected", which signs the user out (seen during the DNS outage) | Consider a short grace period for the previous refresh token |
| 3 | Product decision | A banned tutor's profile stays visible in Find Tutors | Decide whether banned tutors should be hidden |
| 4 | Config caution | `EMAIL_BACKEND=outbox` is active while the local backend points at production, so reset requests create real reset tokens | Use a separate database for local testing, or unset the email backend |
| 5 | Low | The UI shows "Unknown browser on Linux" for HeadlessChrome sessions (normal browsers unaffected) | Optional: recognise HeadlessChrome |
| 6 | Low | An admin deleting their own record through Content moderation is logged as `by_admin: true` | Optional: set `by_admin` only when the record belongs to someone else |
| 7 | Low | React Router v7 future-flag warnings in development and tests | Add the two `future` flags to the routers |
| 8 | Minor | No dedicated response when the database is unreachable (generic 500) | Optional: return 503 for database connection errors |

**Security observation:** two failed logins for `admin1@peerora.demo` came from a Brave browser on the local machine, at 05:20 (before the account existed) and 05:59. The account owner confirmed the 05:59 attempt was not theirs. Both audit entries were preserved; the attempts came from the local machine, not from the internet.

**Follow-up (25 November 2026):** five more failed logins were recorded after testing ended (audit entries #137–#141, login attempts #54–#58, 24 November 09:30–09:33 UTC / 15:30–15:33 local, IP `127.0.0.1`): three for `admin1@peerora.demo`, one for the string `n`, and one for an email that has no account. **The account owner confirmed these were their own attempts, made in Brave.** Every entry stores the user agent `… Chrome/158.0.0.0 Safari/537.36 Brave/158`, which the activity log shows as "Brave on Linux", so the browser was detected correctly. (An earlier verbal summary of this check called it "Chrome" because the user agent was cut off before the `Brave/158` token; that was a reporting error, not an application error.) The entries were left unchanged. The audit log now has 141 entries.

**Browser detection limitation:** Brave deliberately sends Chrome's exact User-Agent, so the User-Agent alone cannot tell them apart. Peerora adds a `Brave/<version>` token from the `Sec-CH-UA` client hint, or a plain `Brave` token from the frontend's `navigator.brave.isBrave()` check (sent as `X-Client-Brand`); see `backend/peerora/core/request_info.py` and `frontend/src/utils/format.ts`. When neither signal arrives (for example, calls made straight to the API by scripts or `curl`, or a browser setting that hides both), Brave is shown as "Chrome". It is never shown the other way round: Chrome is never labelled Brave. The `X-Client-Brand` header comes from the client, so it is a display hint only and is not used for any security decision.

## 5. Supabase changes made during testing
- **Created (kept as demo data):**
  - study group "CSE309 Project Group" (student1 owner, student2 viewer, tutor1 editor)
  - 4 study records: 2 group records and 2 personal notes
- **Created and then deleted:** one throwaway group and three throwaway records
- **Reverted:** tutor-profile edits, the group rename, bans and unbans, the role change, and the temporary member addition
- **Changed:** student2's password (twice: password change, then reset). The current demo passwords are kept in a private local file outside Git (mode 600)
- **Normal application records:** login attempts, sessions (all ended; **0 open sessions** at the end), refresh tokens, 1 used password-reset token, `last_login_at` updates on the demo accounts, and audit-log entries (**136 in total** at the end)
- **No migrations, no schema changes**

## 6. Existing records preserved
- **Users:** 7 (1 pre-existing account plus the 6 demo accounts), all active, roles unchanged (2 admins, 5 users)
- **Tutor profiles:** 4. The two pre-existing profiles (#5, #6) were never touched and their checksum is unchanged. The two demo profiles (#7, #8) match their original content
- **Audit entries** for the failed admin1 logins: preserved
- **Alembic:** still at `0008_secure_alembic_version`

Nothing was committed, pushed or deployed during testing.
