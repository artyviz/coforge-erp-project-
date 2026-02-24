from django.urls import path
from .views import DashboardView, LoginView, LogoutView, StudentListView, CourseListView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('students/', StudentListView.as_view(), name='students'),
    path('courses/', CourseListView.as_view(), name='courses'),
]
