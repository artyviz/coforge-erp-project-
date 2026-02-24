import httpx
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class APIClient:
    """Base OOP client for interacting with the Rust API."""
    
    def __init__(self, token=None):
        self.base_url = settings.RUST_API_URL
        self.headers = {
            "Content-Type": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def _request(self, method, path, data=None):
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, 
                    url, 
                    json=data, 
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API Error: {e.response.status_code} - {e.response.text}")
            return {"error": True, "message": str(e), "status": e.response.status_code}
        except Exception as e:
            logger.error(f"Connection Error: {str(e)}")
            return {"error": True, "message": "API Connection Failed"}

    async def get(self, path):
        return await self._request("GET", path)

    async def post(self, path, data):
        return await self._request("POST", path, data)

    async def delete(self, path):
        return await self._request("DELETE", path)


class AuthService(APIClient):
    """Handles authentication and user registration."""
    
    async def login(self, username, password):
        return await self.post("/api/auth/login", {
            "username": username,
            "password": password
        })

    async def register(self, username, email, password, role="student", full_name=""):
        return await self.post("/api/auth/register", {
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "full_name": full_name
        })


class StudentService(APIClient):
    """Handles student management operations."""
    
    async def list_students(self, limit=50, offset=0):
        return await self.get(f"/api/students?limit={limit}&offset={offset}")

    async def get_student(self, student_id):
        return await self.get(f"/api/students/{student_id}")

    async def create_student(self, student_data):
        return await self.post("/api/students", student_data)

    async def delete_student(self, student_id):
        return await self.delete(f"/api/students/{student_id}")

    async def search_students(self, query):
        return await self.get(f"/api/students/search/{query}")


class CourseService(APIClient):
    """Handles course management operations."""
    
    async def list_courses(self):
        return await self.get("/api/courses")

    async def create_course(self, course_data):
        return await self.post("/api/courses", course_data)


class AnalyticsService(APIClient):
    """Handles analytics and dashboard data."""
    
    async def get_dashboard_stats(self):
        return await self.get("/api/analytics/dashboard")

    async def get_department_summary(self):
        return await self.get("/api/analytics/departments")
