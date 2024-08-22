#imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from courses.models import Course
from django.db.models import Q

#All the code in this file was written without assistance

#view to render the sign in page
def signIn_view(request):
    #case get request
    if request.method == "GET":
        #render the sign in page
        return render(request, "users/signIn.html")
    
    #case post request - user has submitted the sign in details
    elif request.method == "POST":
        #get email and password provider by user
        email = request.POST.get("email")
        password = request.POST.get("password")

        #authenticate user
        user = authenticate(request, email=email, password=password)

        #case user exists
        if user is not None:
            #log in user
            login(request, user)
            #redirect user to the home page
            return redirect("users:home_view")
        #case user was not found
        else:
            #create an error message
            messages.error(request, "Invalid email or passwordd")
            #render the sign in page with the error message
            return render(request, "users/signIn.html")

    #case request method is not GET or POST - return bad request
    return JsonResponse({"error": "Bad Request"}, status=400)

#view to register new users
def register_view(request):
    #create a context to send data to the template
    context = {}

    #case get request
    if request.method == "GET":
        #create a registration form
        registration_form = RegistrationForm()
        #add form to the context
        context["form"] = registration_form
        #render the registration page with the form
        return render(request, "users/register.html", context)
    
    #case post request
    elif request.method == "POST":
        #populate the registration form with the data submitted by user
        registration_form = RegistrationForm(request.POST)

        #case for is valid
        if(registration_form.is_valid()):
            #create a new user - do not save
            new_user = registration_form.save(commit=False)
            print(f"password before hashing: {registration_form.cleaned_data['password1']}")
            #set hashed password
            new_user.set_password(registration_form.cleaned_data["password1"])
            print(f"password after hashing: {new_user.password}")
            #set user's email
            new_user.email = registration_form.cleaned_data["email"]

            #get account type
            account_type = registration_form.cleaned_data["account_type"]
            #case user selected teacher
            if account_type == "teacher":
                new_user.is_teacher = True
                new_user.is_student = False
            #case user selected student
            elif account_type == "student":
                new_user.is_teacher = False
                new_user.is_student = True

            #save the new user to the database
            new_user.save()

            #create a success message
            messages.success(request, "Account created successfully. Please, sign in.")
            #redirect user to the sign in page passing the message
            return redirect("users:signIn_view")
        #case form is not valid
        else:
            #add form to context
            context["form"] = registration_form
            #render the register page with the form and errors
            return render(request, "users/register.html", context)

    #case request method is not GET or POST - return bad request
    return JsonResponse({"error": "Bad Request"}, status=400)

def home_view(request):
    if request.method == "GET":
        return render(request, "users/home.html")

#view for the search bar 
@login_required
def searchBar_view(request):
    #create a context to send data to the template
    context = {}
    
    #case get method 
    if request.method == "GET":
        #get the query submitted by the user
        query = request.GET.get("query")
        
        #case query was provided
        if query:
            #find users whose first name, last name or username contain the query
            users = CustomUser.objects.filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) |
                Q(username__icontains=query)
            )
            #find the courses whose title contains the query
            courses = Course.objects.filter(title__icontains=query)
        
        #case no query provided
        else:
            #return empty querysets
            users = CustomUser.objects.none()
            courses = Course.objects.none()

        #add the results and query to the context
        context = {
            "query": query,
            "users": users,
            "courses": courses,
        }

    #render the search results page with the context
    return render(request, "users/search_results.html", context)