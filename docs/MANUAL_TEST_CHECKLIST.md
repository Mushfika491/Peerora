# Peerora: manual verification checklist

Run the checks with the backend and frontend dev servers (or against the
deployment) and the demo accounts from `scripts/seed_demo.py`. Mark each item
✅ or ❌ and note the date and environment.

## 1. Public pages (logged out)
- [ ] `/` shows the navbar (Home, Find Tutors, About, Login, Sign Up), the hero with calls to action, How Peerora Works, Featured Tutors, Study Groups, Why Peerora, and the footer
- [ ] `/tutors`: search, the subject, department and mode filters, and pagination work; the URL keeps the filters
- [ ] A tutor detail page does **not** show the Student ID, and Edit/Delete are hidden
- [ ] `/about` loads; an unknown URL shows the 404 page
- [ ] Opening `/dashboard`, `/groups` or `/admin` redirects to `/login?next=...`

## 2. Authentication
- [ ] Signup offers only Student and Tutor (no admin option)
- [ ] Signup validation: short password, mismatched confirmation, invalid email
- [ ] A Student signs up and lands on the Student dashboard; a Tutor lands on the tutor profile setup
- [ ] A wrong password shows "Incorrect email or password."; 5 wrong attempts then show the throttle message (use a spare account)
- [ ] After that lockout, the same account can still log in from a **different network** (for example a phone on mobile data)
- [ ] With two tabs open, both stay signed in after their access tokens expire (silent refresh in both)
- [ ] Reloading the page keeps the user signed in, with no flash of the login page
- [ ] Logout returns to `/`; Back/Refresh does not restore the session
- [ ] With `ACCESS_TOKEN_MINUTES=1` locally, after waiting more than 1 minute the next action still works (silent refresh)
- [ ] Account → Password: a wrong current password is rejected; after a change, other browsers are signed out
- [ ] Every password field has an eye button on the right: the password is hidden by default, Tab reaches the button, and Enter/Space toggles show/hide
- [ ] Login page shows **Forgot password?** next to the Password label
- [ ] Without `EMAIL_BACKEND`, `/forgot-password` says reset by email is not available
- [ ] With `EMAIL_BACKEND=outbox`, requesting a reset for a demo account shows the generic message, and a `.eml` file appears in `backend/dev-outbox/`. An unknown email shows the same message and writes no file.
- [ ] Opening the link from the `.eml` loads `/reset-password` and the `#token=` part disappears from the address bar. A mismatched confirmation or a weak password is refused.
- [ ] After the reset: a toast appears, you land on `/login`, the new password works, the old one doesn't, and another browser that was signed in is signed out
- [ ] Opening the same link again shows "invalid or has expired"
- [ ] Account → Sessions: two browsers are listed; revoking the other signs it out on its next action

## 3. Dashboards and navigation
- [ ] Student sidebar: Dashboard, Find tutors, Study groups, My records, Account settings
- [ ] Tutor sidebar also has "My tutor profile"
- [ ] Admin lands on `/admin`; the sidebar has the Administration section plus "My dashboard"
- [ ] A Student opening `/admin` or `/dashboard/tutor` sees the "no access" page
- [ ] At 375px, 768px and 1280px widths, the sidebar becomes a drawer, the navbar collapses, and tables scroll

## 4. Tutor profiles
- [ ] A Tutor creates a profile (name pre-filled); a second attempt redirects to the existing profile
- [ ] The owner sees their Student ID and the Edit/Delete buttons; another tutor does not
- [ ] Editing works with success toasts and validation messages; delete asks for confirmation
- [ ] An admin can edit and delete any profile; the activity log shows the moderation

## 5. Study groups and records (demo group "CSE309 Project Group")
- [ ] Owner (student1): adds a member by email, removes a member, renames the group, and deletes a test group
- [ ] Owner, Members tab: each member has **Create / Update / Assign** checkboxes plus *All* / *None*; the role badge changes to editor / viewer / member
- [ ] Give student2 **only Create**. As student2: *New record* is shown and there is no *Assigned to* field; records have no *Edit* button
- [ ] Give student2 **only Update**. As student2: *Edit* is shown on records, but *New record* is not, and the edit form has no assignee field
- [ ] Give student2 **only Assign**. As student2: the assignee can be changed (via the API or after also granting Update); the title cannot be edited
- [ ] Editor (tutor1): creates, edits and assigns records; cannot see the Settings tab or change permissions
- [ ] Viewer (student2, set back to *None*): read only; can change the status of a record assigned to them; can leave the group
- [ ] Outsider (tutor2): opening the group URL shows "Group not found"
- [ ] Personal records under My records are not visible to other users

## 6. Admin dashboard
- [ ] Overview numbers match the database
- [ ] Users: search, role, type and status filters, pagination, select-all
- [ ] Bulk ban (a reason is required) skips admins; bulk unban **also requires a reason** (empty or under 3 characters is refused)
- [ ] User detail shows groups, records, sessions and recent activity; Ban/Unban, each with a required reason; role change; revoke one or all sessions
- [ ] Activity log: the unban entry shows the reason you typed
- [ ] An admin cannot ban themself or another admin, or change their own role (buttons disabled, API refuses)
- [ ] A banned user (signed in in another browser) is **signed out automatically** on their next click, lands on the login page with a "suspended" message, and cannot log in
- [ ] A normal "no permission" error (for example a member without Update trying to edit) shows an error but does **not** sign the user out
- [ ] Content: search and filter records and groups; single and bulk delete with confirmation
- [ ] Activity log: filter by action, user and date; search by a user's email; shows IP and browser; never shows passwords or tokens
- [ ] Activity-log times match your clock (UTC+6 in Bangladesh); the page names your timezone; the exported CSV shows the same moments in UTC (`+00:00`)
- [ ] Log in once from Brave and once from Chrome: the new entries show "Brave on …" and "Chrome on …" respectively
- [ ] Security page: failed logins grouped by IP and by account
- [ ] CSV exports (users, records, activity log) download and follow the active filters; each export appears in the activity log

## 7. Integration and deployment
- [ ] `/api/docs` loads
- [ ] The browser console has no errors on the main pages, including **no Content-Security-Policy violations** in the production build (`npm run build && npm run preview`, or on Vercel)
- [ ] In the devtools Network tab, API calls go to `/api/...` on the same origin (no `localhost` in production)
- [ ] The refresh cookie is `HttpOnly; Secure; SameSite=Strict; Path=/api/auth` in production
- [ ] `python backend/tests/live_smoke_test.py https://<deployment>` passes
