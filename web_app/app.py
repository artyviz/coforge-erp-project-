"""
University ERP — FastAPI Web Frontend

Server-rendered Jinja2 templates that proxy to the Rust API.
This layer NEVER touches the database directly.
"""

import os

import httpx
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="University ERP", docs_url=None, redoc_url=None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

API = os.environ.get("RUST_API_URL", "http://localhost:3000")


# ── Helpers ──────────────────────────────────────────
def get_token(request: Request) -> str | None:
    return request.cookies.get("erp_token")


def get_user(request: Request) -> dict | None:
    """Read user info stored in cookie (set at login)."""
    import json
    raw = request.cookies.get("erp_user")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None


async def api_get(path: str, token: str = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API}{path}", headers=headers, timeout=10)
        return r.json() if r.status_code == 200 else {}


async def api_post(path: str, data: dict, token: str = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API}{path}", json=data, headers=headers, timeout=10)
        return r.json(), r.status_code


async def api_delete(path: str, token: str = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{API}{path}", headers=headers, timeout=10)
        return r.status_code


# ── Auth guard ───────────────────────────────────────
def require_login(request: Request):
    """Redirect to /login if not authenticated."""
    token = get_token(request)
    if not token:
        return RedirectResponse(url="/login", status_code=302)
    return None


# ── Login / Register / Logout ────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    user = get_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request, "error": error, "page": "login",
    })


@app.post("/login")
async def login_submit(request: Request, response: Response,
                        username: str = Form(...), password: str = Form(...)):
    result, status = await api_post("/api/auth/login", {
        "username": username,
        "password": password,
    })

    if status != 200:
        msg = result.get("message", "Invalid credentials")
        return templates.TemplateResponse("login.html", {
            "request": request, "error": msg, "page": "login",
        })

    import json
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie("erp_token", result["token"], httponly=True, max_age=86400)
    resp.set_cookie("erp_user", json.dumps(result["user"]), max_age=86400)
    return resp


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = ""):
    return templates.TemplateResponse("register.html", {
        "request": request, "error": error, "page": "register",
    })


@app.post("/register")
async def register_submit(request: Request,
                            username: str = Form(...),
                            email: str = Form(...),
                            password: str = Form(...),
                            full_name: str = Form(""),
                            role: str = Form("student")):
    result, status = await api_post("/api/auth/register", {
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": role,
    })

    if status != 200:
        msg = result.get("message", "Registration failed")
        return templates.TemplateResponse("register.html", {
            "request": request, "error": msg, "page": "register",
        })

    import json
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie("erp_token", result["token"], httponly=True, max_age=86400)
    resp.set_cookie("erp_user", json.dumps(result["user"]), max_age=86400)
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("erp_token")
    resp.delete_cookie("erp_user")
    return resp


# ── Dashboard ────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)
    stats = await api_get("/api/analytics/dashboard", token)
    dept_summary = await api_get("/api/analytics/departments", token)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "departments": dept_summary if isinstance(dept_summary, list) else [],
        "page": "dashboard",
        "user": user,
    })


# ── Students ─────────────────────────────────────────
@app.get("/students", response_class=HTMLResponse)
async def students_list(request: Request, search: str = ""):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)
    if search:
        data = await api_get(f"/api/students/search/{search}", token)
        students = data if isinstance(data, list) else []
        total = len(students)
    else:
        result = await api_get("/api/students", token)
        students = result.get("data", [])
        total = result.get("total", 0)
    return templates.TemplateResponse("students.html", {
        "request": request,
        "students": students,
        "total": total,
        "search": search,
        "page": "students",
        "user": user,
    })


@app.post("/students/add")
async def student_add(request: Request,
                       first_name: str = Form(...),
                       last_name: str = Form(...),
                       email: str = Form(...),
                       date_of_birth: str = Form(...)):
    token = get_token(request)
    await api_post("/api/students", {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "date_of_birth": date_of_birth,
    }, token)
    return RedirectResponse(url="/students", status_code=303)


@app.get("/students/{student_id}/delete")
async def student_delete(request: Request, student_id: str):
    token = get_token(request)
    await api_delete(f"/api/students/{student_id}", token)
    return RedirectResponse(url="/students", status_code=303)


# ── Courses ──────────────────────────────────────────
@app.get("/courses", response_class=HTMLResponse)
async def courses_list(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)
    result = await api_get("/api/courses", token)
    courses = result.get("data", []) if isinstance(result, dict) else []
    return templates.TemplateResponse("courses.html", {
        "request": request,
        "courses": courses,
        "page": "courses",
        "user": user,
    })


@app.post("/courses/add")
async def course_add(request: Request,
                      code: str = Form(...),
                      title: str = Form(...),
                      credits: int = Form(...),
                      capacity: int = Form(...)):
    token = get_token(request)
    await api_post("/api/courses", {
        "code": code, "title": title, "credits": credits, "capacity": capacity,
    }, token)
    return RedirectResponse(url="/courses", status_code=303)


# ── Departments ──────────────────────────────────────
@app.get("/departments", response_class=HTMLResponse)
async def departments_list(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)
    depts = await api_get("/api/departments", token)
    if not isinstance(depts, list):
        depts = []
    return templates.TemplateResponse("departments.html", {
        "request": request,
        "departments": depts,
        "page": "departments",
        "user": user,
    })


# ── Faculty ──────────────────────────────────────────
@app.get("/faculty", response_class=HTMLResponse)
async def faculty_list(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)
    result = await api_get("/api/faculty", token)
    faculty = result.get("data", []) if isinstance(result, dict) else []
    total = result.get("total", 0) if isinstance(result, dict) else 0
    return templates.TemplateResponse("faculty.html", {
        "request": request,
        "faculty": faculty,
        "total": total,
        "page": "faculty",
        "user": user,
    })


# ── Enrollments ──────────────────────────────────────
@app.get("/enrollments", response_class=HTMLResponse)
async def enrollments_list(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)

    if user and user.get("role") == "student":
        result = await api_get(f"/api/enrollments/student/{user['id']}", token)
        enrollments = result.get("data", []) if isinstance(result, dict) else []
    else:
        result = await api_get("/api/enrollments", token)
        enrollments = result.get("data", []) if isinstance(result, dict) else []

    students_data = await api_get("/api/students", token)
    students = students_data.get("data", []) if isinstance(students_data, dict) else []

    courses_data = await api_get("/api/courses", token)
    courses = courses_data.get("data", []) if isinstance(courses_data, dict) else []

    return templates.TemplateResponse("enrollments.html", {
        "request": request,
        "enrollments": enrollments,
        "students": students,
        "courses": courses,
        "page": "enrollments",
        "user": user,
    })


@app.post("/enrollments/enroll")
async def enroll_student(request: Request,
                         student_id: str = Form(...),
                         course_id: str = Form(...),
                         semester: str = Form(...)):
    token = get_token(request)
    await api_post("/api/enrollments/enroll", {
        "student_id": student_id,
        "course_id": course_id,
        "semester": semester,
    }, token)
    return RedirectResponse(url="/enrollments", status_code=303)


@app.get("/enrollments/{enrollment_id}/drop")
async def drop_enrollment(request: Request, enrollment_id: str):
    token = get_token(request)
    await api_delete(f"/api/enrollments/{enrollment_id}/drop", token)
    return RedirectResponse(url="/enrollments", status_code=303)
@app.get("/departments", response_class=HTMLResponse)
async def departments_list(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    token = get_token(request)
    user = get_user(request)
    depts = await api_get("/api/departments", token)
    if not isinstance(depts, list):
        depts = []
    return templates.TemplateResponse("departments.html", {
        "request": request,
        "departments": depts,
        "page": "departments",
        "user": user,
    })
