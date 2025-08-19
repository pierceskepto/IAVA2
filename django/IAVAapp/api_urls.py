from django.urls import path
from . import api_views

urlpatterns = [
    # Health check
    path('health/', api_views.api_health, name='api_health'),
    
    # Authentication endpoints
    path('auth/login/', api_views.api_login, name='api_login'),
    path('auth/register/', api_views.api_register, name='api_register'),
    path('auth/logout/', api_views.api_logout, name='api_logout'),
    
    # Student management endpoints
    path('students/<int:user_id>/', api_views.api_get_students, name='api_get_students'),
    path('students/register/', api_views.api_register_student, name='api_register_student'),
    path('students/<int:student_id>/', api_views.api_delete_student, name='api_delete_student'),
    path('students/<int:student_id>/details/', api_views.api_get_student_details, name='api_get_student_details'),
    path('students/<int:student_id>/update/', api_views.api_update_student, name='api_update_student'),
]