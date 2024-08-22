from django import forms
from django.forms import ModelForm
from .models import CustomUser
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
import re
from datetime import date, datetime

class RegistrationForm(ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Password must be at least 8 characters long, contain an uppercase letter and a special character(. , @ # ? $ &)"
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Confirm your password"
    )

    account_type = forms.ChoiceField(
        choices=[("teacher", "Teacher"), ("student", "Student")],
        widget=forms.RadioSelect,
        required=True,
        label="Type of Account"
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email","first_name", "last_name", "date_of_birth", "city", "country", "password1", "password2"]
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email already in use")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Username already taken")
        return username
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if not dob:
            raise ValidationError("Date of birth is required")
        
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < 18:
            raise ValidationError("You must be at least 18 years old to register")
        
        return dob
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password1):
            raise ValidationError("Password must have at least one uppercase letter")
        if not re.search(r"[,.@#?$&]", password1):
            raise ValidationError("Password must have at least one special character (. , @ # ? $ &)")
        return password1
    
    def clean_city(self):
        city = self.cleaned_data.get("city")
        if not city:
            raise ValidationError("City is required")
        
        if not re.match(r'^[A-Za-z\s.]+$', city):
            raise ValidationError("City names can only contain letters, spaces and periods")

        return city

    def clean_country(self):
        country = self.cleaned_data.get("country")
        if not country:
            raise ValidationError("Country is required")
        
        if not re.match(r'^[A-Za-z\s.]+$', country):
            raise ValidationError("Country names can only contain letters, spaces and periods")

        return country

    def clean_account_type(self):
        account_type = self.cleaned_data.get("account_type")
        if account_type not in ["teacher", "student"]:
            raise ValidationError("Account type is invalid")
        return account_type
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")
    
        return cleaned_data


class CustomSetPasswordForm(SetPasswordForm):
    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password1):
            raise ValidationError("Password must have at least one uppercase letter")
        if not re.search(r"[,.@#?$&]", password1):
            raise ValidationError("Password must have at least one special character (. , @ # ? $ &)")
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")
    
        return cleaned_data