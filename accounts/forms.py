"""Traino v2 – accounts/forms.py"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    """Registration form for both students and instructors."""
    email    = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_username(self):
        """
        Override to allow duplicate usernames.
        (Default UserCreationForm rejects duplicates.)
        """
        return self.cleaned_data.get('username')


class LoginForm(forms.Form):
    """Login form using email + password."""
    email    = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)