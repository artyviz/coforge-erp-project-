# University ERP — Demo Guide

A complete walkthrough for running, accessing, and testing every feature of the
University ERP system built with Rust (Axum) + FastAPI (Python) + PostgreSQL.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Open the App](#open-the-app)
4. [First-time Setup (Create an Account)](#first-time-setup)
5. [Page Walkthrough](#page-walkthrough)
   - [Login / Register](#login--register)
   - [Dashboard](#dashboard)
   - [Students](#students)
   - [Courses](#courses)
   - [Departments](#departments)
   - [Faculty](#faculty)
   - [Enrollments](#enrollments)
6. [Request Flow](#request-flow)
7. [Seeded Sample Data](#seeded-sample-data)
8. [Testing Each Feature](#testing-each-feature)
9. [Stopping the Stack](#stopping-the-stack)

---

## Prerequisites

| Requirement | Minimum version |
|---|---|
| Docker Desktop | 24.x or newer |
| Available ports | 5432, 3000, 8000 |

Make sure Docker Desktop is **running** before continuing.

---

## Quick Start

```bash
# Clone / navigate to the project root
cd coforge-erp-project-

# Build and start all three services
docker compose up --build
```

Docker will build and start:

| Container | Service | Port |
|---|---|---|
| `erp_postgres` | PostgreSQL 16 | 5432 |
| `erp_rust_api` | Rust/Axum REST API | 3000 |
| `erp_web_app` | FastAPI + Jinja2 frontend | **8000** |

The first build takes 2–5 minutes (Rust compilation). Subsequent starts are fast.

**Wait for all services to be healthy.** You will see log lines like:

```
erp_rust_api  | INFO university_erp_api: listening on 0.0.0.0:3000
erp_web_app   | INFO:     Uvicorn running on http://0.0.0.0:8000
erp_postgres  | database system is ready to accept connections
```

---

## Open the App

**http://localhost:8000**

You will be automatically redirected to the login page at `http://localhost:8000/login`.

---

## First-time Setup

The database is seeded with an `admin` user, but the password hash in the seed file
is a placeholder and **cannot be verified at runtime**. You must register a new account.

### Step 1 — Register

Go to: **http://localhost:8000/register**

Fill in the form:

| Field | Suggested value |
|---|---|
| Full name | `System Admin` |
| Username | `admin2` |
| Role | `admin` |
| Email | `admin2@uni.edu` |
| Password | `test123` (min 6 chars) |

Click **Create account**. You will be logged in automatically and redirected to the Dashboard.

### Why register instead of logging in as `admin`?

The seeded `admin` account has a placeholder Argon2 hash
(`$argon2id$...$VGhpcyBpcyBhIHBsYWNlaG9sZGVyIGhhc2g` decodes to
"This is a placeholder hash"). The Rust API performs real Argon2 verification so
the credentials `admin / admin123` will fail. Registering creates a proper hash.

---

## Page Walkthrough

### Login / Register

**URL:** `/login` and `/register`

- **Login** (`/login`): Split-screen layout — decorative university branding on the left,
  sign-in form on the right. Supports username + password with JWT cookie-based sessions.
- **Register** (`/register`): Card-style form. Choose a role (`student`, `faculty`, `admin`).
  The role controls what actions you can take across the app.
- **Logout** (`/logout`): Clears the JWT cookie and redirects to login.

---

### Dashboard

**URL:** `/`  **Role:** all logged-in users

The dashboard gives a real-time overview of the university:

#### Stat Cards (top row)
| Card | Source field |
|---|---|
| Total Students | `stats.total_students` |
| Active Students | `stats.active_students` |
| Courses | `stats.total_courses` |
| Departments | `stats.total_departments` |
| Average GPA | `stats.average_gpa` (formatted to 2 decimal places) |

#### Department Analytics Chart
A dual-axis **bar chart** (Chart.js) showing:
- Left Y-axis: student enrollment count per department (indigo bars)
- Right Y-axis: average GPA per department (emerald bars)

Data source: `GET /api/analytics/departments` — returns a list with
`department_name`, `student_count`, `avg_gpa`.

#### Department Summary List
The right-hand panel shows a ranked list of departments with GPA badges:
- **Emerald** badge: avg GPA ≥ 3.5
- **Sky** badge: avg GPA 2.0–3.49
- **Rose** badge: avg GPA < 2.0

#### Quick Action Links (bottom row)
Four shortcut tiles navigate to: Add Student, Add Course, Enroll Student, Departments.

---

### Students

**URL:** `/students`  **Role:** view = all | add/delete = admin or faculty

#### Table columns
| Column | Field | Notes |
|---|---|---|
| Student | `s.first_name`, `s.last_name` | Avatar initials from first letters |
| Email | `s.email` | |
| GPA | `s.gpa` | Emerald ≥ 3.5 · Sky ≥ 2.0 · Rose < 2.0 |
| Status | `s.status` | `active` · `graduated` · `on_leave` · `suspended` |
| Remove | (link) | Only shown for admin/faculty roles |

#### Search
Type any name or email fragment and click **Search**. Uses
`GET /api/students/search/{query}`. Click **Clear** to reset.

#### Add Student (admin/faculty only)
Click the **Add Student** button (top-right). A modal slides in with fields:
- First name, Last name, Email, Date of birth
- Submits to `POST /students/add` → `POST /api/students`

#### Delete Student (admin/faculty only)
Click **Remove** on any row. A browser `confirm()` dialog prevents accidental deletions.
Calls `GET /students/{id}/delete` → `DELETE /api/students/{id}`.

---

### Courses

**URL:** `/courses`  **Role:** view = all | add = admin or faculty

#### Table columns
| Column | Field | Notes |
|---|---|---|
| Code | `c.code` | Monospace badge (e.g. `CS101`) |
| Title | `c.title` | With optional description below |
| Credits | `c.credits` | Pill badge |
| Capacity | `c.capacity` | Fill bar (when `enrolled_student_ids` available) |
| Semester | `c.semester` | Plain text or `—` |
| Status | `c.status` / `c.is_active` | Active (emerald) or Inactive (slate) |

#### Add Course (admin/faculty only)
Click **Add Course** (top-right) to open a modal with:
- Course code (e.g. `CS401`), Title, Credits (1–6), Capacity
- Submits to `POST /courses/add` → `POST /api/courses`

---

### Departments

**URL:** `/departments`  **Role:** view = all

Departments are displayed as **color-coded cards** (6-color rotation: indigo, violet, sky,
emerald, amber, rose).

#### Each card shows
| Field | Source |
|---|---|
| Name | `d.name` |
| Code | `d.code` (monospace) |
| Description | `d.description` (hidden if empty) |
| Faculty count | `d.faculty_ids | length` (0 if not in API response) |
| Course count | `d.course_ids | length` (0 if not in API response) |
| Budget | `d.budget` formatted as `$2,400k` |

> **Note:** The Rust API's `Department` model currently exposes `name`, `code`, and `budget`.
> Faculty and course counts will show `0` until the API is extended to include those arrays.

---

### Faculty

**URL:** `/faculty`  **Role:** view = all

#### Table columns
| Column | Field | Notes |
|---|---|---|
| Faculty Member | `f.first_name`, `f.last_name` | Avatar color by rank |
| Email | `f.email` | |
| Specialisation | `f.specialisation` | `—` if not in API response |
| Academic Rank | `f.rank` | Color-coded badge |
| Status | `f.is_active` | Defaults to Active |

#### Rank badge colors
| Rank | Badge |
|---|---|
| `distinguished_professor` | Purple |
| `professor` | Violet |
| `associate_professor` | Indigo |
| `assistant_professor` | Sky |
| `lecturer` | Slate |

A rank legend is shown below the table.

> **Note:** The current Rust `Faculty` model maps `status` but the DB column is
> `is_active (BOOLEAN)`. If the faculty endpoint errors, the page will show an empty state.
> This is a known API model mismatch that does not affect other pages.

---

### Enrollments

**URL:** `/enrollments`  **Role:** view = all | enroll/drop = admin or faculty

#### Student view
When logged in as a `student` role, you see **your own enrollments** (fetched via
`GET /api/enrollments/student/{user.id}` which returns full `EnrollmentDetail`
including `course_code`, `course_title`, `credits`).

#### Admin / Faculty view
You see **all enrollment records** (fetched via `GET /api/enrollments`).
The table adds a **Student** column showing the student's name (looked up from the
`students` list). Course code/title/credits columns show `—` if the API returns basic
enrollment records without the course JOIN. Each active enrollment has a **Drop** button.

#### Table columns
| Column | Notes |
|---|---|
| Student | Admin/Faculty only — avatar + full name |
| Course | Monospace code badge or truncated course ID |
| Title | Course title or `—` |
| Credits | Pill badge or `—` |
| Semester | e.g. `Fall 2025` |
| Status | `registered` (indigo) · `in_progress` (sky pulse) · `completed` (emerald) · `withdrawn` / `failed` (slate/rose) |
| Grade | `A`/`A-` emerald · `B`/`B+` sky · `C` amber · other rose |
| Drop | Rose bordered button for active enrollments (admin/faculty) |

#### Enroll Student (admin/faculty only)
Click **Enroll Student** (top-right) to open a modal with:
- Student dropdown (all students)
- Course dropdown (all courses with code + title)
- Semester text input (e.g. `Spring 2026`)
- Submits to `POST /enrollments/enroll` → `POST /api/enrollments/enroll`

---

## Request Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (http://localhost:8000)                                 │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTP GET/POST (HTML pages, form submits)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI  (erp_web_app, port 8000)                               │
│                                                                  │
│  ① Reads `erp_token` JWT cookie for authentication              │
│  ② Reads `erp_user` JSON cookie for user info (role, name)      │
│  ③ Makes async HTTP calls to Rust API using httpx               │
│  ④ Renders Jinja2 HTML template with API data                   │
│  ⑤ Returns rendered HTML to browser                             │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTP JSON (internal Docker network)
                       │ http://rust_api:3000
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  Rust / Axum API  (erp_rust_api, port 3000)                      │
│                                                                  │
│  ① Validates Bearer JWT token (HS256, 24h expiry)               │
│  ② Executes async SQL via SQLx connection pool                  │
│  ③ Returns JSON response                                         │
└──────────────────────┬───────────────────────────────────────────┘
                       │ TCP (internal Docker network)
                       │ postgres:5432
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16  (erp_postgres, port 5432)                        │
│                                                                  │
│  Tables: users, departments, faculty, students,                  │
│          courses, enrollments, etl_runs                          │
└──────────────────────────────────────────────────────────────────┘

Auth flow (login):
  Browser ──POST /login──► FastAPI ──POST /api/auth/login──► Rust API
          ◄── HTML+cookies─                ◄── {token, user} ──

Subsequent requests:
  Browser ──GET /students (cookie: erp_token)──► FastAPI
                     FastAPI ──GET /api/students (Bearer token)──► Rust
                     Rust  ──JSON──► FastAPI ──rendered HTML──► Browser
```

---

## Seeded Sample Data

The database is pre-seeded (`database/seed.sql`) with the following data.

### Departments (5)

| Code | Name | Budget |
|---|---|---|
| CS | Computer Science | $2,400,000 |
| MATH | Mathematics | $1,800,000 |
| PHY | Physics | $2,100,000 |
| EE | Electrical Engineering | $2,600,000 |
| ME | Mechanical Engineering | $2,200,000 |

### Faculty (8)

| Name | Department | Rank |
|---|---|---|
| Rajesh Kumar | Computer Science | Professor |
| Priya Sharma | Computer Science | Asst. Professor |
| David Johnson | Mathematics | Assoc. Professor |
| Sarah Williams | Physics | Professor |
| Michael Brown | Electrical Engineering | Professor |
| Ananya Patel | Mathematics | Lecturer |
| James Wilson | Mechanical Engineering | Assoc. Professor |
| Fatima Hassan | Physics | Asst. Professor |

### Courses (9)

| Code | Title | Credits | Capacity |
|---|---|---|---|
| CS101 | Introduction to Computer Science | 3 | 120 |
| CS201 | Data Structures & Algorithms | 4 | 80 |
| CS301 | Operating Systems | 3 | 60 |
| MATH201 | Linear Algebra | 3 | 90 |
| MATH301 | Probability & Statistics | 3 | 75 |
| PHY101 | Classical Mechanics | 4 | 100 |
| PHY201 | Electromagnetism | 4 | 70 |
| EE201 | Circuit Analysis | 3 | 65 |
| ME101 | Engineering Mechanics | 3 | 80 |

### Students (12)

| Name | Email | GPA | Dept |
|---|---|---|---|
| Aisha Sharma | aisha.s@uni.edu | 3.98 | CS |
| Rahul Kumar | rahul.k@uni.edu | 3.72 | MATH |
| Priya Patel | priya.p@uni.edu | 3.65 | PHY |
| Ahmed Ali | ahmed.a@uni.edu | 3.54 | EE |
| Sarah Lee | sarah.l@uni.edu | 3.89 | CS |
| Omar Hassan | omar.h@uni.edu | 3.41 | ME |
| Mei Chen | mei.c@uni.edu | 3.76 | CS |
| Chirag Tyagi | chirag.t@uni.edu | 3.82 | CS |
| Deepak Verma | deepak.v@uni.edu | 3.15 | PHY |
| Nina Gupta | nina.g@uni.edu | 2.98 | MATH |
| Carlos Rivera | carlos.r@uni.edu | 3.33 | EE |
| Zara Khan | zara.k@uni.edu | 3.91 | CS |

### Enrollments (21 records)

Mix of `completed` (with grades), `registered`, and `in_progress` enrollments
across `Fall 2025` and `Spring 2026` semesters.

Sample grades present: `A`, `A-`, `B+`, `B`, `B-`, `C+`.

---

## Testing Each Feature

### 1. Register and log in

```
http://localhost:8000/register
→ Fill form with role: admin
→ Auto-redirects to dashboard
```

### 2. View the Dashboard

```
http://localhost:8000/
→ Expect: 12 students (active), 9 courses, 5 departments
→ Department chart shows CS with most students
→ Average GPA ≈ 3.6
```

### 3. Search Students

```
http://localhost:8000/students
→ Type "aisha" in search box → click Search
→ Expect: Aisha Sharma (GPA 3.98, emerald badge)
→ Click Clear to reset
```

### 4. Add a New Student (admin/faculty role)

```
http://localhost:8000/students
→ Click "Add Student"
→ First: Test, Last: User, Email: test.user@uni.edu, DOB: 2002-06-15
→ Click "Add Student" in modal
→ Page reloads — new student appears at end of list with GPA 0.00
```

### 5. Add a New Course (admin/faculty role)

```
http://localhost:8000/courses
→ Click "Add Course"
→ Code: CS401, Title: Machine Learning, Credits: 3, Capacity: 40
→ Click "Add Course" in modal
→ Page reloads — CS401 appears in table with "Active" badge
```

### 6. Browse Departments

```
http://localhost:8000/departments
→ Expect 5 colored department cards (CS, MATH, PHY, EE, ME)
→ Budget displayed on each card
```

### 7. Browse Faculty

```
http://localhost:8000/faculty
→ If the page shows faculty: expect 8 members with rank badges
→ If empty: the Rust Faculty model has a known field mismatch
  (status vs is_active) — this is a backend limitation
```

### 8. View Enrollments

```
http://localhost:8000/enrollments
→ As admin: see all 21 enrollment records with Student column
→ Status badges: green (completed), blue pulse (in_progress), indigo (registered)
→ Grade badges: emerald A, sky B, amber C
```

### 9. Enroll a Student (admin/faculty role)

```
http://localhost:8000/enrollments
→ Click "Enroll Student"
→ Select: Aisha Sharma, CS401 — Machine Learning, Semester: Spring 2026
→ Click "Enroll Student"
→ New enrollment appears with status "registered"
```

### 10. Drop an Enrollment (admin/faculty role)

```
http://localhost:8000/enrollments
→ Find a "registered" or "in_progress" enrollment
→ Click the red "Drop" button
→ Confirm the browser dialog
→ Enrollment is removed from the table
```

### 11. Log Out

```
http://localhost:8000/logout
→ Clears erp_token and erp_user cookies
→ Redirects to /login
```

---

## Stopping the Stack

```bash
# Stop all containers (preserves database volume)
docker compose down

# Stop AND delete all data (fresh start next time)
docker compose down -v

# View live logs
docker compose logs -f

# View logs for one service only
docker compose logs -f web_app
docker compose logs -f rust_api
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 8000 | Wait another 30s — Rust is still compiling |
| Dashboard shows zeros | Rust API not ready yet; refresh in 10s |
| Faculty page is empty | Known API model mismatch (`status` vs `is_active`) — not a frontend bug |
| `Username or email already taken` | Choose a different username on register |
| `Course is full` when enrolling | Select a course with remaining capacity |
| `Already enrolled` error | That student + course + semester combo already exists |
| Login fails with `admin/admin123` | Seed hash is a placeholder; use `/register` to create a real account |

---

*Generated for University ERP (Coforge) — Frontend: Tailwind CSS + Alpine.js + Chart.js | Backend: Rust/Axum + FastAPI | DB: PostgreSQL 16*
