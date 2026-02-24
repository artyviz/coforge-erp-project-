import json
from django.views import View
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from .services import AuthService, StudentService, CourseService, AnalyticsService, APIClient

class BaseView(View):
    """Base class for all ERP views with authentication checking."""
    
    def get_token(self, request):
        return request.session.get(settings.ERP_SESSION_TOKEN_KEY)

    def get_user(self, request):
        return request.session.get(settings.ERP_USER_DATA_KEY)

    def is_authenticated(self, request):
        return self.get_token(request) is not None

    def handle_no_auth(self):
        return redirect('login')


class LoginView(View):
    async def get(self, request):
        if request.session.get(settings.ERP_SESSION_TOKEN_KEY):
            return redirect('dashboard')
        return render(request, 'login.html', {'page': 'login'})

    async def post(self, request):
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        
        service = AuthService()
        result = await service.login(username, password)
        
        if result.get('error') or 'token' not in result:
            return render(request, 'login.html', {
                'error': result.get('message', 'Invalid credentials'),
                'page': 'login'
            })
        
        # Store in session
        request.session[settings.ERP_SESSION_TOKEN_KEY] = result['token']
        request.session[settings.ERP_USER_DATA_KEY] = result['user']
        return redirect('dashboard')


class LogoutView(View):
    def get(self, request):
        request.session.flush()
        return redirect('login')


class DashboardView(BaseView):
    async def get(self, request):
        if not self.is_authenticated(request):
            return self.handle_no_auth()
        
        token = self.get_token(request)
        user = self.get_user(request)
        
        analytics_service = AnalyticsService(token)
        stats = await analytics_service.get_dashboard_stats()
        depts = await analytics_service.get_department_summary()
        
        return render(request, 'dashboard.html', {
            'user': user,
            'stats': stats,
            'departments': depts if isinstance(depts, list) else [],
            'page': 'dashboard'
        })


class StudentListView(BaseView):
    async def get(self, request):
        if not self.is_authenticated(request):
            return self.handle_no_auth()
        
        token = self.get_token(request)
        user = self.get_user(request)
        search_query = request.GET.get('search', '')
        
        service = StudentService(token)
        if search_query:
            students = await service.search_students(search_query)
            total = len(students)
        else:
            result = await service.list_students()
            students = result.get('data', [])
            total = result.get('total', 0)
            
        return render(request, 'students.html', {
            'user': user,
            'students': students,
            'total': total,
            'search': search_query,
            'page': 'students'
        })


class CourseListView(BaseView):
    async def get(self, request):
        if not self.is_authenticated(request):
            return self.handle_no_auth()
        
        token = self.get_token(request)
        user = self.get_user(request)
        
        service = CourseService(token)
        result = await service.list_courses()
        courses = result.get('data', []) if isinstance(result, dict) else []
        
        return render(request, 'courses.html', {
            'user': user,
            'courses': courses,
            'page': 'courses'
        })
