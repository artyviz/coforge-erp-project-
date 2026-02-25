# University ERP — Frontend Documentation

> **Scope:** This document covers the FastAPI-based web frontend only (`web_app/`).
> For the full system (Rust API + database), see the root `README.md` and `DEMO.md`.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [How to Run](#4-how-to-run)
5. [All Pages](#5-all-pages)
6. [How Frontend Connects to Backend](#6-how-frontend-connects-to-backend)
7. [All API Endpoints Used by the Frontend](#7-all-api-endpoints-used-by-the-frontend)
8. [Bugs Fixed During Development](#8-bugs-fixed-during-development)
9. [Known Issues](#9-known-issues)
10. [How to Add New Pages](#10-how-to-add-new-pages)

---

## 1. Overview

The frontend is a **server-rendered web application** built with FastAPI and Jinja2 templates.
It acts as a thin middle layer between the browser and the Rust/Axum REST API:

- It **never touches the database directly**.
- Every data operation goes through an HTTP call to the Rust API on port 3000.
- The server renders fully-formed HTML using Jinja2 templates and returns it to the browser.
- Authentication is cookie-based: a JWT token (`erp_token`) and serialized user info
  (`erp_user`) are stored in HTTP-only cookies after login.

---

## 2. Tech Stack

| Layer | Technology | How it's loaded |
|---|---|---|
| Web framework | **FastAPI** (Python) | `pip` / `requirements.txt` |
| Async HTTP client | **httpx** | `pip` / `requirements.txt` |
| Template engine | **Jinja2** | Built into FastAPI |
| CSS framework | **Tailwind CSS v3** | CDN (`https://cdn.tailwindcss.com`) |
| UI interactivity | **Alpine.js v3** | CDN |
| Charts | **Chart.js v4** | CDN |
| Custom styles | `static/style.css` | Served by FastAPI StaticFiles |

No build step is required for the frontend. Tailwind, Alpine.js, and Chart.js are all
loaded from CDN at page load time.

---

## 3. Project Structure

```
web_app/
├── app.py                  # FastAPI application — all routes and API proxy logic
├── Dockerfile              # Container definition for the web_app service
├── requirements.txt        # Python dependencies (fastapi, uvicorn, httpx, jinja2)
├── FRONTEND_README.md      # This file
│
├── static/
│   └── style.css           # Small custom stylesheet (scrollbar, transitions, etc.)
│                           # Tailwind handles all other styling via CDN utility classes.
│
└── templates/
    ├── base.html           # Master layout — sidebar, navbar, CDN script tags,
    │                       # Alpine.js toast notification system
    ├── login.html          # Split-screen login page
    ├── register.html       # Registration card page
    ├── dashboard.html      # Stats cards + Chart.js dual-bar chart + quick actions
    ├── students.html       # Students table with search, Add modal, Delete confirm
    ├── courses.html        # Courses table with Add modal
    ├── departments.html    # Color-coded department cards with faculty/course counts
    ├── faculty.html        # Faculty table with rank badges and rank legend
    └── enrollments.html    # Enrollments table with Enroll/Drop modals
```

### `app.py` — key sections

| Lines | What it does |
|---|---|
| `API = ...` | Reads `RUST_API_URL` env var, defaults to `http://localhost:3000` |
| `get_token()` | Reads `erp_token` JWT cookie |
| `get_user()` | Reads and JSON-decodes `erp_user` cookie |
| `api_get()` | Async GET to Rust API with Bearer auth |
| `api_post()` | Async POST to Rust API with Bearer auth |
| `api_delete()` | Async DELETE to Rust API with Bearer auth |
| `require_login()` | Auth guard — returns 302 redirect to `/login` if not logged in |
| Route handlers | One per page; each calls the API, then renders a template |

---

## 4. How to Run

### Start the full stack (recommended)

```bash
# From the project root (not web_app/)
docker compose up --build
```

Docker Compose starts three services:

| Service | Container | Port |
|---|---|---|
| PostgreSQL 16 | `erp_postgres` | 5432 |
| Rust/Axum API | `erp_rust_api` | 3000 |
| FastAPI frontend | `erp_web_app` | **8000** |

Wait for all services to be healthy (first build takes 2–5 minutes for Rust compilation).

### Access the app

| URL | Page |
|---|---|
| http://localhost:8000 | Dashboard (auto-redirects to login if not authenticated) |
| http://localhost:8000/login | Login page |
| http://localhost:8000/register | Registration page |

### Stop the stack

```bash
docker compose down          # Stop, keep database data
docker compose down -v       # Stop AND wipe all data (fresh start)
```

### First-time login

The seeded `admin` account has a placeholder password hash that cannot be verified.
Go to `/register` and create a new account with role `admin`.

---

## 5. All Pages

### Login — `/login`

Split-screen layout. University branding on the left, sign-in form on the right.

- Submits `POST /login` → proxies to `POST /api/auth/login` on the Rust API.
- On success: sets `erp_token` (JWT, httpOnly) and `erp_user` (JSON) cookies, redirects to `/`.
- On failure: re-renders the form with the error message from the API.
- If already logged in: auto-redirects to `/`.

---

### Register — `/register`

Card-style registration form. Fields: Full name, Username, Email, Password, Role.

- Role choices: `student`, `faculty`, `admin`.
- Submits `POST /register` → proxies to `POST /api/auth/register`.
- On success: logs the user in immediately (same cookie-setting as login).

---

### Dashboard — `/`

Real-time overview of the university. Requires login (all roles).

**Stat cards (top row)**

| Card | API field |
|---|---|
| Total Students | `stats.total_students` |
| Active Students | `stats.active_students` |
| Total Courses | `stats.total_courses` |
| Departments | `stats.total_departments` |
| Average GPA | `stats.average_gpa` |

**Department chart** — Chart.js dual-bar chart:
- Left Y-axis (indigo bars): student count per department
- Right Y-axis (emerald bars): average GPA per department

**Department summary list** — right panel, with GPA color badges:
- Emerald: avg GPA ≥ 3.5
- Sky: avg GPA 2.0–3.49
- Rose: avg GPA < 2.0

**Quick action tiles** — shortcuts to: Add Student, Add Course, Enroll Student, Departments.

---

### Students — `/students`

Paginated table of all students. Requires login (all roles can view).

**Table columns:** Avatar (initials), Full name, Email, GPA badge, Status badge, Remove link.

**GPA badge colors:** Emerald ≥ 3.5 · Sky ≥ 2.0 · Rose < 2.0

**Status badge colors:** Active (emerald) · Graduated (sky) · On leave (amber) · Suspended (rose)

**Search:** Text box + Search button — uses `GET /api/students/search/{query}`.
Clear button resets to full list.

**Add Student modal** (admin/faculty only): First name, Last name, Email, Date of birth.
Submits `POST /students/add` → `POST /api/students`.

**Delete** (admin/faculty only): `confirm()` dialog → `GET /students/{id}/delete` → `DELETE /api/students/{id}`.

---

### Courses — `/courses`

Table of all courses. Requires login (all roles can view).

**Table columns:** Course code (monospace badge), Title, Credits pill, Capacity, Semester, Status badge.

**Status:** Active (emerald) · Inactive (slate).

**Add Course modal** (admin/faculty only): Course code (e.g. `CS401`), Title, Credits (1–6), Capacity.
Submits `POST /courses/add` → `POST /api/courses`.

---

### Departments — `/departments`

Color-coded cards in a responsive grid (1 → 2 → 3 columns). Requires login (all roles).

Each card shows: department name, code, description (if any), faculty count, course count, budget.

Colors cycle across 6 palette options: indigo, violet, sky, emerald, amber, rose.

Faculty count and course count are computed by `app.py` by cross-referencing the
`/api/faculty` and `/api/courses` responses — the `/api/departments` endpoint does not
include those counts directly.

Budget is formatted as `$2,400k`.

---

### Faculty — `/faculty`

Table of all faculty members. Requires login (all roles).

**Table columns:** Avatar (color by rank), Full name, Email, Specialisation, Rank badge, Status.

**Rank badge colors:**

| Rank | Color |
|---|---|
| `distinguished_professor` | Purple |
| `professor` | Violet |
| `associate_professor` | Indigo |
| `assistant_professor` | Sky |
| `lecturer` | Slate |

A rank legend is displayed below the table.

---

### Enrollments — `/enrollments`

Role-aware enrollment management. Requires login (all roles).

**Student view:** Only shows the current student's own enrollments
(via `GET /api/enrollments/student/{user.id}`).

**Admin/Faculty view:** Shows all enrollment records with a Student column.
Each active enrollment has a red **Drop** button.

**Table columns:** Student (admin only), Course code, Course title, Credits, Semester, Status badge, Grade badge, Drop button.

**Status badge colors:** Registered (indigo) · In progress (sky, animated pulse) · Completed (emerald) · Withdrawn/Failed (slate/rose).

**Grade badge colors:** A/A− (emerald) · B+/B/B− (sky) · C (amber) · Other (rose).

**Enroll Student modal** (admin/faculty only): Student dropdown, Course dropdown (code + title), Semester text.
Submits `POST /enrollments/enroll` → `POST /api/enrollments/enroll`.

**Drop:** `confirm()` dialog → `GET /enrollments/{id}/drop` → `DELETE /api/enrollments/{id}/drop`.

---

## 6. How Frontend Connects to Backend

```
┌────────────────────────────────────────────────────────────┐
│  Browser  (http://localhost:8000)                          │
│                                                            │
│  Sends: HTML form POSTs, anchor-link GETs                  │
│  Stores: erp_token (JWT cookie), erp_user (JSON cookie)    │
└──────────────────────┬─────────────────────────────────────┘
                       │  HTTP  GET / POST  (HTML pages)
                       ▼
┌────────────────────────────────────────────────────────────┐
│  FastAPI  (erp_web_app, port 8000)   [web_app/app.py]      │
│                                                            │
│  1. Reads erp_token cookie for Bearer auth                 │
│  2. Reads erp_user cookie for role / display name          │
│  3. Makes async JSON calls to Rust API via httpx           │
│  4. Renders Jinja2 template with API data                  │
│  5. Returns fully-formed HTML to browser                   │
└──────────────────────┬─────────────────────────────────────┘
                       │  HTTP JSON  (internal Docker network)
                       │  http://rust_api:3000
                       ▼
┌────────────────────────────────────────────────────────────┐
│  Rust / Axum REST API  (erp_rust_api, port 3000)           │
│                                                            │
│  1. Validates Bearer JWT (HS256, 24 h expiry)              │
│  2. Executes SQL via SQLx async connection pool            │
│  3. Returns JSON response                                  │
└──────────────────────┬─────────────────────────────────────┘
                       │  TCP  (internal Docker network)
                       │  postgres:5432
                       ▼
┌────────────────────────────────────────────────────────────┐
│  PostgreSQL 16  (erp_postgres, port 5432)                  │
│                                                            │
│  Tables: users, departments, faculty, students,            │
│          courses, enrollments, etl_runs                    │
└────────────────────────────────────────────────────────────┘

Login flow:
  Browser ──POST /login──────────► FastAPI
                                   FastAPI ──POST /api/auth/login──► Rust API
                                   Rust API ──{token, user}──────────► FastAPI
  Browser ◄──HTML + cookies (302)── FastAPI

Subsequent page requests:
  Browser ──GET /students (cookie: erp_token)──────────────► FastAPI
           FastAPI ──GET /api/students (Bearer token)──────► Rust API
           Rust API ──JSON──────────────────────────────────► FastAPI
  Browser ◄──rendered HTML──────────────────────────────── FastAPI
```

---

## 7. All API Endpoints Used by the Frontend

| FastAPI route | Rust API call | Purpose |
|---|---|---|
| `POST /login` | `POST /api/auth/login` | Authenticate user, get JWT |
| `POST /register` | `POST /api/auth/register` | Create new account |
| `GET /logout` | _(no API call)_ | Clear cookies, redirect |
| `GET /` | `GET /api/analytics/dashboard` + `GET /api/analytics/departments` | Dashboard stats + chart data |
| `GET /students` | `GET /api/students` | List all students |
| `GET /students?search=q` | `GET /api/students/search/{q}` | Search students by name/email |
| `POST /students/add` | `POST /api/students` | Create new student |
| `GET /students/{id}/delete` | `DELETE /api/students/{id}` | Delete student |
| `GET /courses` | `GET /api/courses` | List all courses |
| `POST /courses/add` | `POST /api/courses` | Create new course |
| `GET /departments` | `GET /api/departments` + `GET /api/faculty` + `GET /api/courses` | List departments with computed counts |
| `GET /faculty` | `GET /api/faculty` | List all faculty |
| `GET /enrollments` (admin) | `GET /api/enrollments` | All enrollment records |
| `GET /enrollments` (student) | `GET /api/enrollments/student/{id}` | Current student's enrollments |
| `POST /enrollments/enroll` | `POST /api/enrollments/enroll` | Enroll a student in a course |
| `GET /enrollments/{id}/drop` | `DELETE /api/enrollments/{id}/drop` | Drop an enrollment |

---

## 8. Bugs Fixed During Development

The following bugs were identified and fixed while building the frontend:

**Bug 1 — Cookie serialization: `erp_user` not persisting between requests**
The user object (role, name, id) needed to be JSON-encoded before being stored in a cookie
and JSON-decoded when read back. Without this, `get_user()` returned `None` on every request,
breaking role-based UI rendering and the student enrollment filter.
_Fix:_ `json.dumps(result["user"])` on set, `json.loads(raw)` on read (app.py lines 97–100, 31–39).

**Bug 2 — Student search endpoint returns a list, not `{data, total}`**
The main students endpoint returns `{"data": [...], "total": N}` but the search endpoint
`/api/students/search/{q}` returns a plain list. Using `.get("data", [])` on the search
result always returned an empty list.
_Fix:_ Separate handling for search vs. list responses (app.py lines 175–181).

**Bug 3 — Departments page: faculty and course counts always 0**
The `/api/departments` endpoint returns only `name`, `code`, `budget` — it does not include
`faculty_ids` or `course_ids` arrays. The template showed 0 for both counts.
_Fix:_ `app.py` now fetches `/api/faculty` and `/api/courses` alongside departments, then
computes `faculty_count` and `course_count` per `department_id` before passing to the
template (app.py lines 259–280).

**Bug 4 — Courses page `AttributeError` when API returned a non-dict**
On error or unexpected API response, `result.get("data", [])` crashed with `AttributeError`
because `result` was a list or empty dict.
_Fix:_ Added `isinstance(result, dict)` guard before calling `.get()` (app.py line 224).

**Bug 5 — Enrollments: students could see all enrollment records**
When a user with role `student` visited `/enrollments`, they saw every student's enrollments
instead of only their own.
_Fix:_ Role check in the handler routes students to `GET /api/enrollments/student/{user.id}`,
while admin/faculty use `GET /api/enrollments` (app.py lines 319–324).

**Bug 6 — Login: cookies not set when redirect was issued first**
The redirect response was being constructed before cookies were attached, causing the browser
to receive a 302 with no cookies, then hitting the dashboard unauthenticated.
_Fix:_ Cookies are set on the `RedirectResponse` object directly before returning it
(app.py lines 98–101 and 132–135).

**Bug 7 — Dashboard crash when `/api/analytics/departments` returned non-list**
During startup (before Rust API was fully ready), the analytics endpoint could return `{}`
or an error object. Passing this directly to the template caused a Jinja2 `for` loop crash.
_Fix:_ Added `isinstance(dept_summary, list)` guard in the dashboard route, defaulting to
`[]` on non-list responses (app.py line 160).

---

## 9. Known Issues

### `POST /api/students` returns HTTP 500 but data saves correctly

**Symptom:** When adding a new student via the Add Student modal, the Rust API responds with
a 500 Internal Server Error. However, the student record is created successfully in the
database and appears in the student list after the page reloads.

**Root cause:** The Rust handler inserts the student row successfully but then fails to
serialize the response (likely a mismatch between the Rust struct and the newly inserted
row's fields, e.g. a `NULL` field that isn't `Option<T>`). The insert transaction commits
before the serialization error is raised.

**Impact:** Low. Data is saved correctly. The frontend ignores the error and redirects back
to `/students`, where the new student appears normally.

**Fix location:** This is a backend issue in `rust_api/src/`. The Rust `Student` response
struct needs to handle optional fields with `Option<T>` to avoid serialization panics.

---

## 10. How to Add New Pages

Follow these steps to add a new page (e.g. a **Grades** page at `/grades`).

### Step 1 — Add the route to `app.py`

```python
# web_app/app.py

@app.get("/grades", response_class=HTMLResponse)
async def grades_list(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)

    # Fetch data from the Rust API
    result = await api_get("/api/grades", token)
    grades = result.get("data", []) if isinstance(result, dict) else []

    return templates.TemplateResponse("grades.html", {
        "request": request,
        "grades": grades,
        "page": "grades",    # used by base.html to highlight the active sidebar link
        "user": user,
    })
```

### Step 2 — Add the sidebar link in `base.html`

Find the sidebar `<nav>` block and add a new `<a>` entry:

```html
<a href="/grades"
   class="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors
          {% if page == 'grades' %}bg-indigo-600 text-white{% else %}text-slate-300 hover:bg-slate-800 hover:text-white{% endif %}">
    <!-- Replace with an appropriate SVG icon -->
    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
    Grades
</a>
```

### Step 3 — Create the template `templates/grades.html`

```html
{% extends "base.html" %}
{% block title %}Grades — University ERP{% endblock %}

{% block content %}
<div class="p-8">

    <!-- Page header -->
    <div class="flex items-start justify-between mb-6">
        <div>
            <h1 class="text-2xl font-bold text-slate-900">Grades</h1>
            <p class="text-slate-500 text-sm mt-1">{{ grades | length }} record{{ 's' if grades | length != 1 else '' }}</p>
        </div>
    </div>

    <!-- Table -->
    {% if grades %}
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <table class="w-full text-sm">
            <thead class="bg-slate-50 border-b border-slate-200">
                <tr>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Student</th>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Course</th>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Grade</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
                {% for g in grades %}
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-6 py-4">{{ g.student_name }}</td>
                    <td class="px-6 py-4">{{ g.course_title }}</td>
                    <td class="px-6 py-4">{{ g.grade | default('—') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col items-center justify-center py-20 text-slate-400">
        <p class="text-base font-semibold text-slate-500">No grades found</p>
    </div>
    {% endif %}

</div>
{% endblock %}
```

### Step 4 — (Optional) Add a POST route for form submissions

```python
@app.post("/grades/add")
async def grade_add(request: Request,
                    student_id: str = Form(...),
                    course_id: str = Form(...),
                    grade: str = Form(...)):
    token = get_token(request)
    await api_post("/api/grades", {
        "student_id": student_id,
        "course_id": course_id,
        "grade": grade,
    }, token)
    return RedirectResponse(url="/grades", status_code=303)
```

### Step 5 — (Optional) Restrict the page or actions by role

Use the `user` dict passed to every template:

```html
{% if user and user.role in ['admin', 'faculty'] %}
    <!-- Show add/edit/delete buttons only to admin and faculty -->
{% endif %}
```

In `app.py`, you can also guard at the route level:

```python
if user and user.get("role") not in ["admin", "faculty"]:
    return RedirectResponse(url="/", status_code=302)
```

### Checklist for a new page

- [ ] Route handler added to `app.py` with `require_login()` guard
- [ ] Template created in `web_app/templates/` extending `base.html`
- [ ] `page` variable passed to template (used for sidebar active state)
- [ ] `user` variable passed to template (used for role-based UI)
- [ ] Sidebar link added to `base.html` with `{% if page == '...' %}` active class
- [ ] `isinstance(result, dict)` guard used before calling `.get()` on API responses

---

*University ERP — Frontend by FastAPI + Jinja2 + Tailwind CSS + Alpine.js + Chart.js*
