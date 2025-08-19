from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from .models import Student
from .forms import RegisterForm, StudentForm
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET"])
def api_health(request):
    """Health check endpoint for the Django service"""
    return JsonResponse({"status": "healthy", "service": "django-auth"})

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API endpoint for login"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                "success": False,
                "message": "Username and password are required"
            }, status=400)
        
        # Try to authenticate as a regular Django user (parent)
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # This is a parent account
            login(request, user)
            return JsonResponse({
                "success": True,
                "message": "Login successful",
                "user_type": "parent",
                "user_id": user.id,
                "username": user.username
            })
        else:
            # Try to authenticate as a student
            try:
                student = Student.objects.get(name=username)
                if check_password(password, student.password):
                    # Student authentication successful
                    return JsonResponse({
                        "success": True,
                        "message": "Login successful",
                        "user_type": "student",
                        "student_id": student.id,
                        "student_name": student.name,
                        "parent_user_id": student.user.id
                    })
                else:
                    return JsonResponse({
                        "success": False,
                        "message": "Invalid password"
                    }, status=401)
            except Student.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid username or password"
                }, status=401)
                
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Login API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """API endpoint for user registration"""
    try:
        data = json.loads(request.body)
        form = RegisterForm(data)
        
        if form.is_valid():
            user = form.save()
            return JsonResponse({
                "success": True,
                "message": "Registration successful",
                "user_id": user.id,
                "username": user.username
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Registration failed",
                "errors": form.errors
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Registration API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """API endpoint for logout"""
    try:
        logout(request)
        return JsonResponse({
            "success": True,
            "message": "Logout successful"
        })
    except Exception as e:
        logger.error(f"Logout API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_students(request, user_id):
    """API endpoint to get students for a parent"""
    try:
        user = User.objects.get(id=user_id)
        students = Student.objects.filter(user=user)
        
        students_data = []
        for student in students:
            students_data.append({
                "id": student.id,
                "name": student.name,
                "level": student.level,
                "user_id": student.user.id
            })
        
        return JsonResponse({
            "success": True,
            "students": students_data
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "User not found"
        }, status=404)
    except Exception as e:
        logger.error(f"Get students API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_register_student(request):
    """API endpoint to register a new student"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        name = data.get('name')
        password = data.get('password')
        level = data.get('level')
        
        if not all([user_id, name, password, level]):
            return JsonResponse({
                "success": False,
                "message": "All fields are required"
            }, status=400)
        
        user = User.objects.get(id=user_id)
        
        # Check if student name already exists for this user
        if Student.objects.filter(user=user, name=name).exists():
            return JsonResponse({
                "success": False,
                "message": "Student name already exists"
            }, status=400)
        
        # Create student
        student = Student(
            user=user,
            name=name,
            level=level
        )
        student.set_password(password)
        student.save()
        
        return JsonResponse({
            "success": True,
            "message": "Student registered successfully",
            "student": {
                "id": student.id,
                "name": student.name,
                "level": student.level
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Parent user not found"
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Register student API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_student(request, student_id):
    """API endpoint to delete a student"""
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({
                "success": False,
                "message": "User ID is required"
            }, status=400)
        
        user = User.objects.get(id=user_id)
        student = Student.objects.get(id=student_id, user=user)
        
        student_name = student.name
        student.delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Student '{student_name}' deleted successfully"
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "User not found"
        }, status=404)
    except Student.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Student not found or access denied"
        }, status=404)
    except Exception as e:
        logger.error(f"Delete student API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_student_details(request, student_id):
    """API endpoint to get student details"""
    try:
        student = Student.objects.get(id=student_id)
        
        return JsonResponse({
            "success": True,
            "student": {
                "id": student.id,
                "name": student.name,
                "level": student.level,
                "user_id": student.user.id,
                "parent_username": student.user.username
            }
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Student not found"
        }, status=404)
    except Exception as e:
        logger.error(f"Get student details API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def api_update_student(request, student_id):
    """API endpoint to update student details"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "message": "User ID is required"
            }, status=400)
        
        user = User.objects.get(id=user_id)
        student = Student.objects.get(id=student_id, user=user)
        
        # Update fields if provided
        if 'name' in data:
            student.name = data['name']
        if 'level' in data:
            student.level = data['level']
        if 'password' in data:
            student.set_password(data['password'])
        
        student.save()
        
        return JsonResponse({
            "success": True,
            "message": "Student updated successfully",
            "student": {
                "id": student.id,
                "name": student.name,
                "level": student.level
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "User not found"
        }, status=404)
    except Student.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Student not found or access denied"
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Update student API error: {e}")
        return JsonResponse({
            "success": False,
            "message": "Internal server error"
        }, status=500)