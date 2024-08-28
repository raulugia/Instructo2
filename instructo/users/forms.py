from django import forms
from django.forms import ModelForm
from .models import CustomUser
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
import re
from datetime import date, datetime

#All the code in this file was written without assistance

#form for user registration
class RegistrationForm(ModelForm):
    #password field
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Password must be at least 8 characters long, contain an uppercase letter and a special character(. , @ # ? $ &)"
    )

    #password confirmation field
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Confirm your password"
    )

    #account type field (radio buttons) - 2 types: teacher or student
    account_type = forms.ChoiceField(
        choices=[("teacher", "Teacher"), ("student", "Student")],
        widget=forms.RadioSelect,
        required=True,
        label="Type of Account"
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email","first_name", "last_name", "date_of_birth", "city", "country", "password1", "password2"]
    
    #email validator
    def clean_email(self):
        #get the email
        email = self.cleaned_data.get("email")

        #case email already exists
        if CustomUser.objects.filter(email=email).exists():
            #raise an error
            raise ValidationError("Email already in use")
        #return the validated email
        return email
    
    #username validator
    def clean_username(self):
        #get the username
        username = self.cleaned_data.get("username")

        #case username already exists
        if CustomUser.objects.filter(username=username).exists():
            #raise an error
            raise ValidationError("Username already taken")
        #return the validated username
        return username
    
    #date of birth validator
    def clean_date_of_birth(self):
        #get the date of birth
        dob = self.cleaned_data.get("date_of_birth")

        #case not provided
        if not dob:
            #raise an error
            raise ValidationError("Date of birth is required")
        
        #get today's date
        today = date.today()
        #calculate the user's age
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        #case the user is under 18 years old
        if age < 18:
            #raise an error
            raise ValidationError("You must be at least 18 years old to register")
        
        #return the validated date of birth
        return dob
    
    #password validator
    def clean_password1(self):
        #get the password
        password1 = self.cleaned_data.get("password1")

        #case password is less than 8 characters
        if len(password1) < 8:
            #raise an error
            raise ValidationError("Password must be at least 8 characters long")
        #case password does not have an upper case
        if not re.search(r"[A-Z]", password1):
            #raise an error
            raise ValidationError("Password must have at least one uppercase letter")
        #case password does not have an allowed special character
        if not re.search(r"[,.@#?$&]", password1):
            #raise an error
            raise ValidationError("Password must have at least one special character (. , @ # ? $ &)")
        
        #return the validated password
        return password1
    
    #city validator
    def clean_city(self):
        #get the city
        city = self.cleaned_data.get("city")

        #raise an error if not provided
        if not city:
            raise ValidationError("City is required")
        
        #case city contains characters that are not allowed
        if not re.match(r'^[A-Za-z\s.]+$', city):
            #raise an error
            raise ValidationError("City names can only contain letters, spaces and periods")

        #return the validated city
        return city

    #country validator
    def clean_country(self):
        #get the provided country
        country = self.cleaned_data.get("country")

        #raise an error if no country provided
        if not country:
            raise ValidationError("Country is required")
        
        #case country contains characters that are not allowed
        if not re.match(r'^[A-Za-z\s.]+$', country):
            #raise an error
            raise ValidationError("Country names can only contain letters, spaces and periods")

        #return the validated country
        return country

    #account type validator
    def clean_account_type(self):
        #get provided account type
        account_type = self.cleaned_data.get("account_type")

        #case account type is not teacher/student
        if account_type not in ["teacher", "student"]:
            #raise an error
            raise ValidationError("Account type is invalid")
        
        #return the validated account type
        return account_type
    
    #method to validate the form data
    def clean(self):
        #get the cleaned data
        cleaned_data = super().clean()

        #get both provided passwords
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        #case they do not match
        if password1 and password2 and password1 != password2:
            #raise an error
            raise ValidationError("Passwords do not match")
        #return the validated data
        return cleaned_data


#custom form for setting a new password - extend SetPasswordForm
class CustomSetPasswordForm(SetPasswordForm):
    #validate password
    def clean_new_password1(self):
        #get the provided password
        password1 = self.cleaned_data.get("new_password1")

        #check the password  meets the criteria or raise an error
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password1):
            raise ValidationError("Password must have at least one uppercase letter")
        if not re.search(r"[,.@#?$&]", password1):
            raise ValidationError("Password must have at least one special character (. , @ # ? $ &)")
        
        #return the validated password
        return password1
    
    #validate form data
    def clean(self):
        #get the cleaned data
        cleaned_data = super().clean()

        #get both passwords
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        #return an error if they do not match
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")

        #return the validated data
        return cleaned_data