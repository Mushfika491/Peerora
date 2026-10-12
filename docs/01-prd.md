# Product Requirements Document (PRD) — Peerora

| Field        | Value                                                                                                |
|:-------------|:-----------------------------------------------------------------------------------------------------|
| Product      | Peerora                                                                                              |
| Tagline      | A Peer Learning and Tutoring Platform                                                                |
| Version      | MVP + Beta                                                                                           |
| Releases     | MVP — Mid-term, Beta — Final                                                                         |
| Status       | Draft                                                                                                |
| Related docs | [Software Requirements Specification (SRS)](02-srs.md), [Technical Design Document (TDD)](03-tdd.md) |

This document describes both planned releases. Every goal, feature, and
user story identifies whether it belongs to the **MVP** or **Beta**, so
the scope for the mid-term and final demonstrations remains clear.

## Documents in this set

| Short form | Full form                           | Purpose                                                                               | File                   |
|:-----------|:------------------------------------|:--------------------------------------------------------------------------------------|:-----------------------|
| PRD        | Product Requirements Document       | What we build and why                                                                 | [01-prd.md](01-prd.md) |
| SRS        | Software Requirements Specification | Detailed functional/non-functional requirements, permissions, and acceptance criteria | [02-srs.md](02-srs.md) |
| TDD        | Technical Design Document           | Architecture, data model, API design, and technical decisions                         | [03-tdd.md](03-tdd.md) |

## 0. Release plan

| Release  | When     | Focus                                                                                                                                                                |
|:---------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **MVP**  | Mid-term | Core tutoring workflow through REST APIs and CRUD, plus a small study-material sharing feature; runnable locally                                                     |
| **Beta** | Final    | Authentication, role-based access control (RBAC), user profiles and dashboards, permission checks/security scopes, safer booking and material access, and deployment |

The tutoring workflow is the primary feature. Material sharing is a
supporting feature and should remain simple.

``` mermaid
flowchart LR
    subgraph MVP["MVP — Mid-term"]
        M1[Define models and database] --> M2[Tutor and availability CRUD]
        M2 --> M3[Booking CRUD API]
        M3 --> M4[Basic study-material sharing]
        M4 --> M5[Mid-term demo]
    end
    subgraph Beta["Beta — Final"]
        B1[Authentication and profiles] --> B2[RBAC and permission checks]
        B2 --> B3[Booking and material access rules]
        B3 --> B4[Dashboard and security testing]
        B4 --> B5[Final demo and deployment]
    end
    M5 --> B1
```

## 1. Purpose

Peerora is a peer-learning platform where students can find fellow
students who offer help in particular subjects and request tutoring
sessions. It also provides a small area for sharing useful study
materials, such as notes and PDFs.

The project will be developed in two steps:

1.  **MVP (mid-term):** Build the core tutoring and basic
    material-sharing workflows as a working React + TypeScript frontend
    connected to a FastAPI REST API and database. The application must
    run locally and demonstrate core CRUD operations.
2.  **Beta (final):** Add account authentication, role and permission
    checks, user profiles and dashboards, stronger booking and
    file-access rules, and deployment.

## 2. Problem statement

Students sometimes struggle to find classmates or other students who can
explain a subject, arrange a suitable time for help, or locate useful
notes in one place. Informal arrangements can be difficult to track, and
shared study files may be scattered across different chats or folders.

Peerora aims to provide one straightforward place to discover peer
tutors, view their available time slots, request and manage tutoring
sessions, and access a small collection of shared study materials. It is
a course project, so the first version will focus on a limited set of
practical features rather than trying to become a complete
learning-management system.

## 3. Goals

| ID   | Goal                                                                                                          | Release |
|:-----|:--------------------------------------------------------------------------------------------------------------|:--------|
| G-1  | Provide REST endpoints for creating, viewing, updating, and deleting tutor profiles and availability records. | MVP     |
| G-2  | Let a student create, view, update, and cancel a tutoring booking through the API.                            | MVP     |
| G-3  | Provide a simple way to list and share study-material records, with basic file access where supported.        | MVP     |
| G-4  | Connect the React + TypeScript frontend to the FastAPI backend and database.                                  | MVP     |
| G-5  | Provide clear validation and error responses and interactive API documentation.                               | MVP     |
| G-6  | Allow users to sign up, log in, log out, and manage a basic profile.                                          | Beta    |
| G-7  | Enforce role-based permissions and ensure users can only manage records they are allowed to access.           | Beta    |
| G-8  | Provide simple dashboards for a student’s bookings and a tutor’s upcoming sessions.                           | Beta    |
| G-9  | Apply booking rules, including preventing conflicting bookings for the same tutor and time slot.              | Beta    |
| G-10 | Protect study-material upload, download, and deletion according to ownership and permissions.                 | Beta    |
| G-11 | Deploy the application and verify the main workflows in the deployed environment.                             | Beta    |

## 4. Target users

| User                    | Need                                                                           | Release |
|:------------------------|:-------------------------------------------------------------------------------|:--------|
| Student / learner       | Browse tutor profiles and request a tutoring session.                          | MVP     |
| Peer tutor              | Publish subjects and available time slots for tutoring.                        | MVP     |
| Student using materials | Browse and access relevant shared notes or PDFs.                               | MVP     |
| Frontend developer      | Use clear REST endpoints and documented request/response formats.              | MVP     |
| Instructor / reviewer   | Run the application locally and inspect its API and core workflows.            | MVP     |
| Registered user         | Sign in and maintain a basic profile.                                          | Beta    |
| Learner                 | View and manage their own tutoring requests and see booking status.            | Beta    |
| Tutor                   | View incoming requests and manage their own availability and session requests. | Beta    |
| Admin                   | Manage user roles and moderate inappropriate or unwanted records when needed.  | Beta    |

## 5. Scope

### In scope — MVP (mid-term)

- Create, list, view, update, and delete tutor profile records.
- Add, list, view, update, and remove tutor availability slots.
- Create, list, view, update, and cancel tutoring booking records.
- Store basic booking information, including learner, tutor, subject,
  requested time, and status.
- List study-material records with title, subject, description, uploader
  name or identifier, and file reference.
- Provide a basic material upload/download flow if file storage is
  available in the local development setup; otherwise, demonstrate
  material CRUD using a file reference.
- Connect the frontend to the backend REST API.
- Validate inputs and return understandable error responses.
- Provide a health-check endpoint and interactive API documentation.
- Run the core application locally for the mid-term demonstration.

### In scope — Beta (final)

- **Authentication:** sign up, log in, and log out.
- **User profile:** view and update basic profile details.
- **Roles and permissions:** learner/student, tutor, and admin roles,
  with permission checks on protected endpoints. A user may act as both
  learner and tutor if the implementation supports a single account with
  both capabilities.
- **Ownership checks:** users can manage only their own profile, tutor
  availability, bookings, and uploaded materials, except where an
  explicitly authorized admin action is allowed.
- **Learner dashboard:** view upcoming/past bookings and booking
  statuses.
- **Tutor dashboard:** view incoming booking requests and upcoming
  sessions; accept or reject requests and manage availability.
- **Booking rules:** validate booking status transitions and prevent
  overlapping confirmed bookings for a tutor.
- **Material access rules:** validate file type and size, restrict
  upload/delete actions to authorized users, and avoid exposing private
  storage paths.
- **Security:** hash passwords, keep secrets in environment variables,
  validate inputs, and check permissions on the server.
- **Deployment:** deploy the frontend and backend with a configured
  database and verify the main user journeys.

### Out of scope for this semester

- Live video calls or built-in voice calling.
- Real-time chat or messaging.
- Online payments, tutor payouts, or paid subscriptions.
- AI-based tutor recommendations or AI-generated study content.
- Complex ratings, reviews, badges, or leaderboards.
- Calendar integrations, automated reminders, and push notifications.
- Advanced document previewing, collaborative editing, or annotation.
- Large-scale moderation tools or advanced analytics.
- Social login, email verification, and a full password-reset workflow
  unless time remains after the required Beta features.

## 6. Features and priority (MoSCoW)

Priorities apply to the stated release. A Beta “Must” is required for
the final demonstration, not the mid-term demonstration.

| ID   | Feature                                                                   | Release | Priority |
|:-----|:--------------------------------------------------------------------------|:--------|:---------|
| F-1  | Create and manage tutor profile records                                   | MVP     | Must     |
| F-2  | List and view tutor profiles                                              | MVP     | Must     |
| F-3  | Create and manage tutor availability slots                                | MVP     | Must     |
| F-4  | Create a tutoring booking                                                 | MVP     | Must     |
| F-5  | List, view, update, and cancel bookings                                   | MVP     | Must     |
| F-6  | Create, list, view, update, and delete study-material metadata            | MVP     | Must     |
| F-7  | Basic material file reference or local upload/download flow               | MVP     | Should   |
| F-8  | Frontend-to-backend REST API integration                                  | MVP     | Must     |
| F-9  | Input validation, consistent errors, health endpoint, and API docs        | MVP     | Must     |
| F-10 | Sign up, log in, and log out                                              | Beta    | Must     |
| F-11 | View and update user profile                                              | Beta    | Must     |
| F-12 | Roles and server-side permission checks                                   | Beta    | Must     |
| F-13 | Ownership rules for tutor profiles, availability, bookings, and materials | Beta    | Must     |
| F-14 | Learner dashboard showing bookings and statuses                           | Beta    | Must     |
| F-15 | Tutor dashboard showing requests and upcoming sessions                    | Beta    | Must     |
| F-16 | Accept/reject booking requests and validate status changes                | Beta    | Must     |
| F-17 | Prevent overlapping confirmed bookings for a tutor                        | Beta    | Should   |
| F-18 | Secure material upload/download/delete permissions and file validation    | Beta    | Must     |
| F-19 | Admin ability to manage roles and remove inappropriate records            | Beta    | Should   |
| F-20 | Deploy the application and verify core workflows                          | Beta    | Must     |

## 7. User stories

### MVP

| ID    | Story                                                                                                                                 | Feature  |
|:------|:--------------------------------------------------------------------------------------------------------------------------------------|:---------|
| US-01 | As a learner, I want to view available peer tutors so I can find someone who can help with a subject.                                 | F-1, F-2 |
| US-02 | As a tutor, I want to publish my subjects and basic profile information so learners can understand what I teach.                      | F-1      |
| US-03 | As a tutor, I want to add and update available time slots so learners can see when I may be available.                                | F-3      |
| US-04 | As a learner, I want to create a booking request with a tutor, subject, and time so I can request help.                               | F-4      |
| US-05 | As a user, I want to view a booking and its status so I can track the request.                                                        | F-5      |
| US-06 | As a user, I want to update or cancel a booking record so changes can be reflected in the system.                                     | F-5      |
| US-07 | As a student, I want to browse study-material records by subject so I can find relevant notes.                                        | F-6      |
| US-08 | As a student, I want to add a study-material record and file reference so useful resources can be shared.                             | F-6, F-7 |
| US-09 | As a frontend developer, I want consistent API responses and validation errors so the interface can handle success and failure cases. | F-8, F-9 |
| US-10 | As an instructor, I want to run the application locally and inspect the API documentation so I can evaluate the core workflows.       | F-8, F-9 |

### Beta

| ID    | Story                                                                                                                                             | Feature                |
|:------|:--------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------|
| US-11 | As a visitor, I want to register for an account so I can use the platform with my own identity.                                                   | F-10                   |
| US-12 | As a registered user, I want to log in and log out so my account is protected.                                                                    | F-10                   |
| US-13 | As a user, I want to view and update my profile so my account information stays current.                                                          | F-11                   |
| US-14 | As a learner, I want to see only the bookings I am allowed to access so my information remains private.                                           | F-12, F-13, F-14       |
| US-15 | As a tutor, I want to see booking requests for my tutoring sessions and accept or reject them.                                                    | F-12, F-13, F-15, F-16 |
| US-16 | As a tutor, I want to manage only my own availability slots so other users cannot change my schedule.                                             | F-12, F-13             |
| US-17 | As a learner, I want to see my booking statuses in a dashboard so I can track upcoming sessions.                                                  | F-14                   |
| US-18 | As a tutor, I want the system to prevent overlapping confirmed bookings so two learners are not assigned the same time slot.                      | F-17                   |
| US-19 | As a material uploader, I want only authorized users to upload or delete my material so shared resources are not changed without permission.      | F-18                   |
| US-20 | As an admin, I want to manage user roles and remove inappropriate records so the platform can be moderated.                                       | F-19                   |
| US-21 | As an instructor, I want the deployed application to support the main tutoring and material-sharing workflows so I can evaluate the Beta release. | F-20                   |

## 8. Success metrics

### MVP

- Tutor profile and availability CRUD endpoints work through the FastAPI
  REST API.
- A user can create, view, update, and cancel a tutoring booking through
  the API.
- Study-material records can be created and listed; the chosen basic
  file-reference or upload/download approach can be demonstrated.
- The React + TypeScript frontend successfully calls the backend for the
  core workflows.
- Data persists in the configured database after restarting the
  application.
- API request/response schemas and endpoints are visible in the
  interactive API documentation.
- The project can be run locally for the mid-term demonstration.

### Beta

- Users can register, log in, and log out.
- Protected endpoints reject unauthenticated requests.
- The server checks roles, ownership, and permissions before allowing
  protected actions.
- Learners and tutors can view the bookings appropriate to their
  accounts.
- Tutors can manage their own availability and booking requests, but
  cannot modify another tutor’s records.
- Confirmed bookings cannot overlap for the same tutor and time period.
- Unauthorized users cannot upload or delete another user’s materials.
- Passwords are never stored or returned in plain text.
- The deployed application supports the primary tutoring workflow and
  the supporting material-sharing workflow.

## 9. Assumptions and constraints

- Frontend: React.js with TypeScript.
- Backend: Python with FastAPI.
- Communication: REST APIs.
- A database will store users, tutor profiles, availability, bookings,
  and material metadata.
- The project must demonstrate frontend-backend integration.
- Authentication, authorization, RBAC, security scopes/permissions, and
  a user profile dashboard are required Beta concerns.
- The application will be developed by a student project team with
  limited time; tutoring is the primary workflow and material sharing
  must remain small.
- Actual material files should be stored using a suitable file-storage
  location; the database should store metadata and a file reference
  rather than the file contents when practical.
- Any deployment platform or database provider will be finalized in the
  TDD.
- During the MVP, demo records may be used without full account
  authentication. The Beta will add user identity and ownership rules.
- No AI/LLM integration is required.

## 10. Milestones

### MVP — Mid-term

| Milestone                 | Deliverable                                                                                            |
|:--------------------------|:-------------------------------------------------------------------------------------------------------|
| M1 — Documentation        | PRD, SRS, and TDD describe both releases                                                               |
| M2 — Data layer           | Database connection and models for tutor profiles, availability, bookings, and material metadata       |
| M3 — Tutoring API         | CRUD endpoints for tutor profiles, availability, and bookings, with validation                         |
| M4 — Supporting feature   | Basic study-material listing and record creation; file reference or simple upload/download if feasible |
| M5 — Frontend integration | React + TypeScript pages call the FastAPI endpoints                                                    |
| M6 — Mid-term demo        | Main tutoring workflow and basic material sharing run locally                                          |

### Beta — Final

| Milestone                         | Deliverable                                                                                     |
|:----------------------------------|:------------------------------------------------------------------------------------------------|
| B1 — Authentication and profile   | Registration, login, logout, and basic profile management                                       |
| B2 — RBAC and permissions         | Learner, tutor, and admin roles with server-side authorization and ownership checks             |
| B3 — Dashboards and booking rules | Learner/tutor booking dashboards, request status actions, and conflict validation               |
| B4 — Material access and security | Protected material operations, file validation, password hashing, and environment-based secrets |
| B5 — Final demo                   | Deployed application with the main tutoring workflow and supporting material sharing working    |

## 11. Release dependencies

- The Beta builds on the MVP data model and REST API; it adds
  authentication and ownership/permission checks to the existing
  workflows rather than replacing them.
- Tutoring remains the core workflow throughout both releases. Material
  sharing should not delay completion of the booking workflow.
- The MVP may use demonstration data without full authentication. The
  Beta associates records with users and enforces ownership and role
  permissions.
- The TDD will define the exact database schema, API paths,
  authentication approach, file-storage choice, and deployment setup.
- If time becomes limited, prioritize the complete tutoring workflow
  first, then finish the small material-sharing feature, and finally
  implement the required Beta security and account features.