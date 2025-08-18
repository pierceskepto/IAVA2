import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from IAVAapp.views import is_student_online  # Import your existing function


print("DEBUG: consumers.py loaded!")  # Add this line

try:
    from IAVAapp.views import is_student_online
    print("DEBUG: Successfully imported is_student_online")
except ImportError as e:
    print(f"DEBUG: Failed to import is_student_online: {e}")


class StudentStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("student_status", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("student_status", self.channel_name)

    @database_sync_to_async
    def get_student_status(self, student_id):
        return is_student_online(student_id)  # Use your existing function

    async def send_student_status(self, event):
        await self.send(text_data=json.dumps({
            'student_id': event['student_id'],
            'is_online': event['is_online']
        }))