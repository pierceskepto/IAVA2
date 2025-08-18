from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

def is_student_online(student_id):
    """
    Check if a student is currently online based on cache data.
    Returns True if student was seen within the last 5 minutes.
    """
    last_seen = cache.get(f'student_seen_{student_id}')
    if last_seen:
        # Check if the last seen time was within the last 5 minutes
        time_threshold = timezone.now() - timedelta(minutes=5)
        is_online = last_seen > time_threshold
        print(f"DEBUG: Student {student_id} last seen: {last_seen}, threshold: {time_threshold}, online: {is_online}")
        return is_online
    print(f"DEBUG: Student {student_id} has no cache entry - offline")
    return False

def is_parent_online(parent_id):
    """
    Check if a parent is currently online based on cache data.
    Returns True if parent was seen within the last 5 minutes.
    """
    last_seen = cache.get(f'parent_seen_{parent_id}')
    if last_seen:
        # Check if the last seen time was within the last 5 minutes
        time_threshold = timezone.now() - timedelta(minutes=5)
        is_online = last_seen > time_threshold
        print(f"DEBUG: Parent {parent_id} last seen: {last_seen}, threshold: {time_threshold}, online: {is_online}")
        return is_online
    print(f"DEBUG: Parent {parent_id} has no cache entry - offline")
    return False

def clear_student_online_status(student_id):
    """Clear a student's online status from cache."""
    cache.delete(f'student_seen_{student_id}')
    print(f"DEBUG: Manually cleared student {student_id} online status from cache")

def clear_parent_online_status(parent_id):
    """Clear a parent's online status from cache."""
    cache.delete(f'parent_seen_{parent_id}')
    print(f"DEBUG: Manually cleared parent {parent_id} online status from cache")