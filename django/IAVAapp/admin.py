from django.contrib import admin
from .models import Student, Badge, StudentBadge, QuizAttempt

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'level', 'current_level', 'xp', 'streak_count', 'get_accuracy')
    search_fields = ('name', 'user__username')
    list_filter = ('current_level', 'level')
    readonly_fields = ('xp', 'current_level', 'streak_count', 'total_questions_answered', 'correct_answers')

class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'icon', 'requirement', 'requirement_field')
    list_filter = ('badge_type',)
    search_fields = ('name', 'description')

class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'earned_date')
    list_filter = ('badge', 'earned_date')
    search_fields = ('student__name', 'badge__name')

class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'topic', 'score', 'total_questions', 'xp_earned', 'completed_at')
    list_filter = ('topic', 'completed_at')
    search_fields = ('student__name', 'topic')
    date_hierarchy = 'completed_at'

admin.site.register(Student, StudentAdmin)
admin.site.register(Badge, BadgeAdmin)
admin.site.register(StudentBadge, StudentBadgeAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)