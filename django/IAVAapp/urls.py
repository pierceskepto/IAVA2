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

    # Gamification endpoints
    path('api/quiz-completion/', views.record_quiz_completion, name='record_quiz_completion'),
    path('api/student-stats/<int:student_id>/', views.get_student_stats, name='get_student_stats'),
    path('api/leaderboard/', views.get_leaderboard, name='get_leaderboard'),

    # Daily Challenge routes
    path('api/daily-challenge/<int:student_id>/', views.get_daily_challenge, name='get_daily_challenge'),
    path('api/daily-challenge/submit/', views.submit_daily_challenge, name='submit_daily_challenge'),
    path('api/daily-challenge/history/<int:student_id>/', views.get_challenge_history, name='challenge_history'),
    path('daily-challenge/', views.daily_challenge_view, name='daily_challenge'),
]