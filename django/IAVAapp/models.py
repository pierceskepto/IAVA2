from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password

class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    
@receiver(post_save, sender=User)
def assign_to_parents_group(sender, instance, created, **kwargs):
    if created:  # Check if a new user is created
        parents_group, created = Group.objects.get_or_create(name='Parents')
        instance.groups.add(parents_group)

class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Students')
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=128)  # Large enough for hashed passwords
    level = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

def check_password(self, raw_password):
        """Check if the provided password matches the stored hashed password."""
        return check_password(raw_password, self.password)
    
def __str__(self):
        return self.name