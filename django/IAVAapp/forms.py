from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Student


ALLOWED_EMAIL_DOMAINS = ['gmail.com', 'outlook.com', 'yourschool.edu']

def validate_allowed_email_domains(email):
    domain = email.split('@')[-1]
    if domain not in ALLOWED_EMAIL_DOMAINS:
        raise ValidationError(f"Email domain '{domain}' is not allowed. Only gmail.com, outlook.com, and school emails are accepted.")

def validate_level(value):
    if not value.isdigit():
        raise ValidationError('Level must be a number.')
    elif int(value) < 4 or int(value) > 6:
        raise ValidationError('Level must be between 4 and 6.')
    
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, validators=[validate_allowed_email_domains])

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username is already taken")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
            if len(password1) < 8:
                raise forms.ValidationError("Password is too short")
        return password2

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'password', 'level'] 
    
    password = forms.CharField(widget=forms.PasswordInput)
    level = forms.CharField(max_length=6, validators=[validate_level]) 

StudentFormSet = forms.formset_factory(StudentForm, extra=1)