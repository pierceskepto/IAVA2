from django.urls import path
from . import consumers

print("DEBUG: routing.py loaded!")

websocket_urlpatterns = [
    path('ws/student_status/', consumers.StudentStatusConsumer.as_asgi()),
    path('homestudent/ws/student_status/', consumers.StudentStatusConsumer.as_asgi()),  # Add this line
]