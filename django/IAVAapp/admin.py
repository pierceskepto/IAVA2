from django.contrib import admin
from .models import Student

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'level')
    search_fields = ('name', 'user__username')

admin.site.register(Student, StudentAdmin)
