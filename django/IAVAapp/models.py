from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta

class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    
@receiver(post_save, sender=User)
def assign_to_parents_group(sender, instance, created, **kwargs):
    if created:
        parents_group, created = Group.objects.get_or_create(name='Parents')
        instance.groups.add(parents_group)

class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Students')
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=128)
    level = models.CharField(max_length=100)
    
    # Gamification fields
    xp = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    streak_count = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    total_questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def add_xp(self, points):
        """Add XP and check for level up"""
        self.xp += points
        old_level = self.current_level
        new_level = self.calculate_level()
        
        if new_level > old_level:
            self.current_level = new_level
            self.save()
            return True, new_level  # Level up occurred
        
        self.save()
        return False, new_level
    
    def calculate_level(self):
        """Calculate level based on XP (100 XP per level, exponential growth)"""
        # Formula: level = floor(sqrt(XP / 100)) + 1
        import math
        return math.floor(math.sqrt(self.xp / 100)) + 1
    
    def xp_for_next_level(self):
        """Calculate XP needed for next level"""
        next_level = self.current_level + 1
        return (next_level - 1) ** 2 * 100
    
    def xp_progress_percentage(self):
        """Calculate percentage progress to next level"""
        current_level_xp = (self.current_level - 1) ** 2 * 100
        next_level_xp = self.xp_for_next_level()
        progress = ((self.xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100
        return min(progress, 100)
    
    def update_streak(self):
        """Update streak based on activity"""
        today = timezone.now().date()
        
        if self.last_activity_date is None:
            # First activity
            self.streak_count = 1
            self.last_activity_date = today
        elif self.last_activity_date == today:
            # Already active today
            pass
        elif self.last_activity_date == today - timedelta(days=1):
            # Continue streak
            self.streak_count += 1
            self.last_activity_date = today
        else:
            # Streak broken
            self.streak_count = 1
            self.last_activity_date = today
        
        self.save()
    
    def get_accuracy(self):
        """Calculate accuracy percentage"""
        if self.total_questions_answered == 0:
            return 0
        return round((self.correct_answers / self.total_questions_answered) * 100, 1)


class Badge(models.Model):
    BADGE_TYPES = [
        ('streak', 'Streak'),
        ('accuracy', 'Accuracy'),
        ('topic', 'Topic Master'),
        ('speed', 'Speed'),
        ('level', 'Level'),
        ('special', 'Special'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    icon = models.CharField(max_length=10, default='🏆')  # Emoji icon
    requirement = models.IntegerField(help_text="Required value to unlock")
    requirement_field = models.CharField(max_length=50, help_text="Field to check (e.g., 'streak_count', 'accuracy')")
    
    def __str__(self):
        return self.name


class StudentBadge(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'badge')
    
    def __str__(self):
        return f"{self.student.name} - {self.badge.name}"


class QuizAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    topic = models.CharField(max_length=100)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    xp_earned = models.IntegerField()
    time_spent = models.FloatField()  # in seconds
    completed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.name} - {self.topic} - {self.score}/{self.total_questions}"