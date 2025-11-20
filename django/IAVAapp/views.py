from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, StudentForm
from .models import Student, Badge, StudentBadge, QuizAttempt
from django.forms import modelformset_factory
from .utils import is_student_online
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


@login_required(login_url='login')
def home(request):
    # Check if this is actually a parent session, not a student
    if 'is_student' in request.session:
        messages.error(request, 'Students cannot access parent dashboard.')
        return redirect('homestudent')
    
    # Retrieve the students associated with the logged-in parent (user)
    students = Student.objects.filter(user=request.user)

    # Add online status to each student
    for student in students:
        student.is_online = is_student_online(student.id)
        # Debug print - remove after testing
        print(f"DEBUG: Student {student.name} (ID: {student.id}) is_online = {student.is_online}")

    # Retrieve all messages from the session and pass them to the template
    all_messages = messages.get_messages(request)
    
    # Render the 'home.html' template and pass the student data
    return render(request, "home.html", {'students': students, 'messages': all_messages})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            login(request, user)  # Log the user in after successful registration
            
            # Clear any student session data that might exist
            request.session.pop('student_id', None)
            request.session.pop('student_name', None)
            request.session.pop('is_student', None)
            
            messages.success(request, 'Account created successfully! Welcome to IAVA.')
            # Use reverse to generate URL and then add query parameters
            url = reverse('register-students') + '?from_register=True'
            return redirect(url)  # Redirect to register-students with query parameter
        else:
            # Handle form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    if 'username' in field.lower():
                        messages.error(request, f'Username Error: {error}')
                    elif 'email' in field.lower():
                        messages.warning(request, f'Email Error: {error}')
                    elif 'password' in field.lower():
                        messages.error(request, f'Password Error: {error}')
                    else:
                        messages.error(request, f'{field.title()} Error: {error}')
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def add_students(request):
    # Ensure this is a parent session
    if 'is_student' in request.session:
        messages.error(request, 'Students cannot add other students.')
        return redirect('homestudent')
        
    StudentFormSet = modelformset_factory(Student, form=StudentForm, extra=1)

    if request.method == 'POST':
        formset = StudentFormSet(request.POST, queryset=Student.objects.none(), prefix='students')
        if formset.is_valid():
            instances = formset.save(commit=False)  # Don't commit yet to modify the instances
            student_count = 0
            for instance in instances:
                instance.user = request.user  # Assign the logged-in user to the instance
                instance.set_password(instance.password)  # Hash the password
                instance.save()
                student_count += 1
            
            if student_count == 1:
                messages.success(request, f'Student {instances[0].name} was added successfully!')
            else:
                messages.success(request, f'All {student_count} students were added successfully!')
            return redirect('home')
        else:
            # Handle formset validation errors
            for form in formset:
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            if 'level' in field.lower():
                                messages.warning(request, f'Grade Level Error: {error}')
                            elif 'name' in field.lower():
                                messages.error(request, f'Student Name Error: {error}')
                            elif 'password' in field.lower():
                                messages.error(request, f'Password Error: {error}')
                            else:
                                messages.error(request, f'{field.title()} Error: {error}')
            
            # Check for non-field errors
            if formset.non_form_errors():
                for error in formset.non_form_errors():
                    messages.error(request, f'Form Error: {error}')
    else:
        formset = StudentFormSet(queryset=Student.objects.none(), prefix='students')

    from_register = request.GET.get('from_register', False)

    return render(request, 'registerstudents.html', {'formset': formset, 'from_register': from_register})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"DEBUG: Attempting login for username: {username}")
        
        # First, try to authenticate as a regular Django user (parent)
        user = authenticate(username=username, password=password)
        
        if user is not None:
            print(f"DEBUG: Django user authentication successful for {username}")

            # Clear any existing session data before login
            request.session.flush()
            
            # This is a parent account
            login(request, user)
            print(f"DEBUG: User logged in: {request.user.is_authenticated}")

            # Explicitly mark this as a parent session
            request.session['is_parent'] = True
            print(f"DEBUG: Session after parent login: {dict(request.session)}")

            messages.success(request, f'Welcome back, {username}! Login successful.')
            return redirect('home')  # Redirect to parent home
        else:
            print(f"DEBUG: Django user authentication failed, trying student login")
            # Try to authenticate as a student
            try:
                student = Student.objects.get(name=username)
                # Check if the provided password matches the student's password
                from django.contrib.auth.hashers import check_password
                if check_password(password, student.password):
                    # Clear any existing session data before login
                    request.session.flush()
                    
                    # Student authentication successful
                    # Create a session for the student (without Django's user system)
                    request.session['student_id'] = student.id
                    request.session['student_name'] = student.name
                    request.session['is_student'] = True
                    request.session['parent_user_id'] = student.user.id  # Store parent ID for reference
                    
                    messages.success(request, f'Welcome back, {username}! Login successful.')
                    return redirect('homestudent')  # Redirect to student home
                else:
                    # Student exists but password is wrong
                    messages.error(request, 'Password Error: The password you entered is incorrect. Please check your password and try again.')
            except Student.DoesNotExist:
                # Check if it might be a parent username that doesn't exist in Django User model
                from django.contrib.auth.models import User
                try:
                    User.objects.get(username=username)
                    # Username exists as parent but password was wrong (already handled above)
                    # This shouldn't happen due to the flow, but just in case
                    messages.error(request, 'Password Error: The password you entered is incorrect. Please check your password and try again.')
                except User.DoesNotExist:
                    # Username doesn't exist anywhere (neither as parent nor student)
                    messages.error(request, 'Username Error: No account found with this username. Please check your username and try again.')
    
    return render(request, 'login.html')


def homestudent_view(request):
    # Check if student is logged in
    if 'student_id' not in request.session or 'is_student' not in request.session:
        messages.error(request, 'Please log in to access this page.')
        return redirect('login')
    
    # Ensure this is actually a student session
    if request.user.is_authenticated and 'is_parent' in request.session:
        messages.error(request, 'Parents cannot access student dashboard.')
        return redirect('home')
    
    # Get the student from session
    student_id = request.session.get('student_id')
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found. Please log in again.')
        request.session.flush()
        return redirect('login')
    
    # Use the student's own ID to check online status
    student.is_online = is_student_online(student.id)
    print(f"DEBUG: Student {student.name} (ID: {student.id}) is_online = {student.is_online}")

    return render(request, 'homestudent.html', {'student': student})


# NEW: Quiz view for both parents and students
def quiz_view(request):
    # Check authentication - allow both parents and students
    is_parent = request.user.is_authenticated and 'is_parent' in request.session
    is_student = 'is_student' in request.session and 'student_id' in request.session
    
    if not is_parent and not is_student:
        messages.error(request, 'Please log in to access the quiz.')
        return redirect('login')
    
    # Get user context for the template
    context = {}
    if is_student:
        try:
            student_id = request.session.get('student_id')
            student = Student.objects.get(id=student_id)
            context['student'] = student
            context['user_type'] = 'student'
        except Student.DoesNotExist:
            messages.error(request, 'Student not found. Please log in again.')
            return redirect('login')
    else:
        # Parent user
        context['user'] = request.user
        context['user_type'] = 'parent'
    
    return render(request, 'quiz.html', context)


# NEW: Quiz interface view for the actual quiz game
def quiz_interface_view(request):
    # Check authentication - allow both parents and students
    is_parent = request.user.is_authenticated and 'is_parent' in request.session
    is_student = 'is_student' in request.session and 'student_id' in request.session
    
    if not is_parent and not is_student:
        messages.error(request, 'Please log in to access the quiz.')
        return redirect('login')
    
    topic = request.GET.get('topic', '')
    
    # Get user context for the template
    context = {'topic': topic}
    
    if is_student:
        try:
            student_id = request.session.get('student_id')
            student = Student.objects.get(id=student_id)
            context['student'] = student
            context['user_type'] = 'student'
            context['student_id'] = student_id
        except Student.DoesNotExist:
            messages.error(request, 'Student not found. Please log in again.')
            return redirect('login')
    else:
        # Parent user
        context['user'] = request.user
        context['user_type'] = 'parent'
    
    return render(request, 'quiz_interface.html', context)


# NEW: Topic overview view (placeholder for now)
def topic_overview_view(request):
    # Check authentication
    is_parent = request.user.is_authenticated and 'is_parent' in request.session
    is_student = 'is_student' in request.session and 'student_id' in request.session
    
    if not is_parent and not is_student:
        messages.error(request, 'Please log in to access the quiz.')
        return redirect('login')
    
    topic = request.GET.get('topic', '')
    
    # For now, redirect back to quiz page if no topic
    if not topic:
        return redirect('quiz')
    
    # TODO: Create topic overview template and logic
    # For now, just show a placeholder
    context = {'topic': topic}
    return render(request, 'topic_overview.html', context)


def logout_view(request):
    from .utils import clear_student_online_status, clear_parent_online_status
    from channels.layers import get_channel_layer  # Add this import
    from asgiref.sync import async_to_sync           # Add this import
    
    username = None
    user_id_to_notify = None  # Track which ID to send in WebSocket
    
    if 'is_student' in request.session:
        # This is a student user
        student_name = request.session.get('student_name', 'Student')
        student_id = request.session.get('student_id')
        username = student_name
        user_id_to_notify = student_id  # Store student ID for WebSocket
        
        # Clear the student's online status from cache immediately
        if student_id:
            clear_student_online_status(student_id)
            print(f"DEBUG: Cleared online status for student ID {student_id}")
        
        # Clear all session data for student
        request.session.flush()
        messages.info(request, f'Goodbye {username}! You have been logged out successfully.')
        
    elif request.user.is_authenticated:
        # This is a parent user
        username = request.user.username
        parent_id = request.user.id
        user_id_to_notify = parent_id  # Store parent ID for WebSocket
        
        # Clear the parent's online status from cache
        clear_parent_online_status(parent_id)
        print(f"DEBUG: Cleared online status for parent ID {parent_id}")
        
        # Standard Django logout
        logout(request)
        # Clear any remaining session data
        request.session.flush()
        messages.info(request, f'Goodbye {username}! You have been logged out successfully.')
        
    else:
        # No active session
        request.session.flush()
        messages.info(request, 'You have been logged out successfully.')

    # Send real-time notification (only if we have a valid ID)
    if user_id_to_notify:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("student_status", {
            "type": "send_student_status",
            "student_id": user_id_to_notify,
            "is_online": False
        })
        print(f"DEBUG: Sent WebSocket notification for user ID {user_id_to_notify}")

    return redirect('login')

# Decorator for student authentication
def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'student_id' not in request.session or 'is_student' not in request.session:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Ensure this is not a parent trying to access student views
        if request.user.is_authenticated and 'is_parent' in request.session:
            messages.error(request, 'Parents cannot access student areas.')
            return redirect('home')
            
        return view_func(request, *args, **kwargs)
    return wrapper

# Example usage of the decorator
@student_required
def student_protected_view(request):
    student_id = request.session.get('student_id')
    student = Student.objects.get(id=student_id)
    return render(request, 'some_student_page.html', {'student': student})


def about_view(request):
    return render(request, 'about.html')

@login_required
def delete_student(request, student_id):
    # Ensure this is a parent session
    if 'is_student' in request.session:
        messages.error(request, 'Students cannot delete other students.')
        return redirect('homestudent')
        
    student = get_object_or_404(Student, id=student_id, user=request.user)  # Ensure user owns the student
    student_name = student.name
    student.delete()
    messages.success(request, f'Student "{student_name}" has been successfully deleted.')
    return redirect('home')

def check_and_award_badges(student):
    """Check if student has earned any new badges"""
    all_badges = Badge.objects.all()
    newly_earned = []
    
    for badge in all_badges:
        # Check if student already has this badge
        if StudentBadge.objects.filter(student=student, badge=badge).exists():
            continue
        
        # Check if student meets the requirement
        if badge.requirement_field == 'streak_count':
            if student.streak_count >= badge.requirement:
                StudentBadge.objects.create(student=student, badge=badge)
                newly_earned.append(badge)
        
        elif badge.requirement_field == 'accuracy':
            if student.get_accuracy() >= badge.requirement:
                StudentBadge.objects.create(student=student, badge=badge)
                newly_earned.append(badge)
        
        elif badge.requirement_field == 'current_level':
            if student.current_level >= badge.requirement:
                StudentBadge.objects.create(student=student, badge=badge)
                newly_earned.append(badge)
        
        elif badge.requirement_field == 'xp':
            if student.xp >= badge.requirement:
                StudentBadge.objects.create(student=student, badge=badge)
                newly_earned.append(badge)
    
    return newly_earned


@csrf_exempt
@require_http_methods(["POST"])
def record_quiz_completion(request):
    """Record quiz completion and update student stats"""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        topic = data.get('topic')
        score = data.get('score')
        total_questions = data.get('total_questions')
        xp_earned = data.get('xp_earned')
        time_spent = data.get('time_spent')
        
        student = Student.objects.get(id=student_id)
        
        # Record quiz attempt
        QuizAttempt.objects.create(
            student=student,
            topic=topic,
            score=score,
            total_questions=total_questions,
            xp_earned=xp_earned,
            time_spent=time_spent
        )
        
        # Update student stats
        student.total_questions_answered += total_questions
        student.correct_answers += score
        
        # Add XP and check for level up
        leveled_up, new_level = student.add_xp(xp_earned)
        
        # Update streak
        student.update_streak()
        
        # Check for new badges
        new_badges = check_and_award_badges(student)
        
        return JsonResponse({
            'success': True,
            'leveled_up': leveled_up,
            'new_level': new_level,
            'current_xp': student.xp,
            'xp_for_next_level': student.xp_for_next_level(),
            'xp_progress': student.xp_progress_percentage(),
            'streak': student.streak_count,
            'new_badges': [
                {
                    'name': badge.name,
                    'description': badge.description,
                    'icon': badge.icon
                } for badge in new_badges
            ]
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_student_stats(request, student_id):
    """Get detailed student statistics"""
    try:
        student = Student.objects.get(id=student_id)
        badges = StudentBadge.objects.filter(student=student).select_related('badge')
        recent_attempts = QuizAttempt.objects.filter(student=student).order_by('-completed_at')[:5]
        
        return JsonResponse({
            'success': True,
            'stats': {
                'xp': student.xp,
                'level': student.current_level,
                'xp_for_next_level': student.xp_for_next_level(),
                'xp_progress': student.xp_progress_percentage(),
                'streak': student.streak_count,
                'total_questions': student.total_questions_answered,
                'correct_answers': student.correct_answers,
                'accuracy': student.get_accuracy(),
                'badges': [
                    {
                        'name': sb.badge.name,
                        'description': sb.badge.description,
                        'icon': sb.badge.icon,
                        'earned_date': sb.earned_date.isoformat()
                    } for sb in badges
                ],
                'recent_attempts': [
                    {
                        'topic': attempt.topic,
                        'score': attempt.score,
                        'total': attempt.total_questions,
                        'xp_earned': attempt.xp_earned,
                        'time_spent': attempt.time_spent,
                        'completed_at': attempt.completed_at.isoformat()
                    } for attempt in recent_attempts
                ]
            }
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_leaderboard(request):
    """Get leaderboard of top students"""
    sort_by = request.GET.get('sort_by', 'xp')  # xp, level, streak, accuracy
    
    if sort_by == 'xp':
        students = Student.objects.order_by('-xp')[:10]
    elif sort_by == 'level':
        students = Student.objects.order_by('-current_level', '-xp')[:10]
    elif sort_by == 'streak':
        students = Student.objects.order_by('-streak_count')[:10]
    elif sort_by == 'accuracy':
        students = Student.objects.all()
        students = sorted(students, key=lambda s: s.get_accuracy(), reverse=True)[:10]
    else:
        students = Student.objects.order_by('-xp')[:10]
    
    leaderboard_data = []
    for rank, student in enumerate(students, 1):
        leaderboard_data.append({
            'rank': rank,
            'name': student.name,
            'xp': student.xp,
            'level': student.current_level,
            'streak': student.streak_count,
            'accuracy': student.get_accuracy(),
            'badge_count': StudentBadge.objects.filter(student=student).count()
        })
    
    return JsonResponse({
        'success': True,
        'leaderboard': leaderboard_data,
        'sort_by': sort_by
    })