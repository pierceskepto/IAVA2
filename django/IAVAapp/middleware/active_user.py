from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

class ActiveUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check for regular Django user authentication (parents)
        if (request.user.is_authenticated and 
            'is_parent' in request.session and 
            'is_student' not in request.session):
            # This is definitely a parent session
            cache.set(f'parent_seen_{request.user.id}', now(), timeout=300)
            # Debug print
            print(f"DEBUG: Updated parent {request.user.id} last seen time")
        
        # Check for session-based student login
        elif ('student_id' in request.session and 
              'is_student' in request.session and 
              not request.user.is_authenticated):
            # This is definitely a student session
            student_id = request.session['student_id']
            cache.set(f'student_seen_{student_id}', now(), timeout=300)
            # Debug print
            print(f"DEBUG: Updated student {student_id} last seen time")
    
    def process_response(self, request, response):
        # Clean up expired cache entries on logout redirect
        if (response.status_code == 302 and 
            ('login' in response.url or response.url.endswith('/login/'))):
            # This is likely a logout redirect
            if 'student_id' in request.session:
                student_id = request.session['student_id']
                cache.delete(f'student_seen_{student_id}')
                print(f"DEBUG: Middleware cleared student {student_id} cache on logout redirect")
            elif request.user.is_authenticated:
                cache.delete(f'parent_seen_{request.user.id}')
                print(f"DEBUG: Middleware cleared parent {request.user.id} cache on logout redirect")
        
        return response