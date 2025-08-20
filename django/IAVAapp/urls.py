from django.urls import path, include
from . import views
from .views import delete_student
from .views import register_view, login_view, logout_view, add_students, about_view, quiz_view, topic_overview_view, quiz_interface_view

urlpatterns =[
    path("", views.home, name="home"),
    path('about/', about_view, name="about"),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register-students/', add_students, name='register-students'),
    path('delete-student/<int:student_id>/', delete_student, name='delete_student'),
    path('homestudent/', views.homestudent_view, name='homestudent'),
    
    # Quiz routes
    path('quiz/', quiz_view, name='quiz'),
    path('topic-overview/', topic_overview_view, name='topic_overview'),
    path('quiz-interface/', quiz_interface_view, name='quiz_interface'),

    # add api endpoints
    path('api/', include('IAVAapp.api_urls')),
]