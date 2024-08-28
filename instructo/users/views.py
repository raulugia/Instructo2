#imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from courses.models import Course, Enrollment
from django.db.models import Q
from status_updates.models import StatusUpdate
from status_updates.forms import StatusUpdateForm
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from .serializers import StatusUpdateSerializer, StudentHome_StatusUpdateSerializer, StudentHome_CourseSerializer, ProfileSerializer
from courses.helpers import process_resource
from django.db.models import Count

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

@login_required
def logout_view(request):
    #log the user out
    logout(request)

    #redirect the user to the sign in page
    return redirect("users:signIn_view")

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
            profile_picture = request.FILES.get("profile_picture")

            #case there is a profile picture:
            if profile_picture:
                #create the resource, create a thumbnail and upload both to supabase storage
                profile_picture_resource = process_resource(profile_picture, "user_profile_picture")

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
            
            new_user.profile_picture = profile_picture_resource

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

#view to render the home page for both teachers and students
@login_required
def home_view(request):
    context = {}
    #case GET request method
    if request.method == "GET":
        status_update_form = StatusUpdateForm()

        #case the user is a student
        if request.user.is_teacher:
            #get the teacher's status updates ordered by created at
            user_status_updates = StatusUpdate.objects.filter(user=request.user).order_by('-created_at')

            #serialize the status updates
            status_updates_serializer = StatusUpdateSerializer(user_status_updates, many=True)

            #get all the courses created by the teacher
            user_courses = Course.objects.filter(teacher=request.user)
            #annotate each course with the student count
            user_courses = user_courses.annotate(student_count= Count("course_enrollments"))
            #get the top 3 courses based on student count
            top_3_courses = user_courses.order_by("-student_count")[:3]
            
            #construct the context
            context = {
                "form": status_update_form,
                "status_updates":  status_updates_serializer.data,
                "courses": user_courses,
                "top_3_courses": top_3_courses
            }

            #render the template with the context
            return render(request, "users/teacher_home.html", context)
        
        #case user is a student
        elif request.user.is_student:
            #get the list of courses ids the student is enrolled in - needed to filter data in the next queries
            enrolled_courses = Enrollment.objects.filter(student=request.user).values_list("course", flat=True)

            #combine student's status updates with the status updates created by the teachers of the courses the student is enrolled in
            combined_status_updates = StatusUpdate.objects.filter(
                Q(user=request.user) | Q(course__in=enrolled_courses)
            ).order_by("-created_at")
            
            #serialize the combined status updates
            combined_status_updates_serializer = StudentHome_StatusUpdateSerializer(combined_status_updates, many=True)
            
            #for every course the student is enrolled in, prefetch the course's weeks and test in every week - needed to display deadlines
            enrolled_courses_with_weeks = Course.objects.filter(id__in=enrolled_courses).prefetch_related("weeks__tests")

            #serialize enrolled_courses_with_weeks
            course_serializer = StudentHome_CourseSerializer(enrolled_courses_with_weeks, many=True)

            #construct the context
            context = {
                "form": status_update_form,
                "courses": course_serializer.data,
                "status_updates": combined_status_updates_serializer.data
            }

            #render the template with the context
            return render(request, "users/student_home.html", context)

#view to render users' profiles
@login_required
def user_profile_view(request, username):
    #GET case
    if request.method == "GET":
        #fetch the user that current user is trying to see
        other_user = CustomUser.objects.get(username=username)

        #serialize the user's data to ensure only the required user's details are returned to the client
        user_serializer = ProfileSerializer(other_user)

        #case the current user is a teacher trying to view a student's profile
        if request.user.is_teacher and other_user.is_student:

            #get the student's status updates
            status_updates = StatusUpdate.objects.filter(user=other_user).order_by("-created_at")

            #get all the courses the student is enrolled in
            student_courses = Course.objects.filter(course_enrollments__student=other_user).distinct()

            #get the courses created by the teacher in which the student is enrolled in
            teacher_courses = student_courses.filter(teacher=request.user)

            #construct the context with the fetched data
            context = {
                "user": user_serializer.data,
                "status_updates": status_updates,
                "student_courses": student_courses,
                "teacher_courses": teacher_courses,
            }

            #render the template with the context
            return render(request, "users/user_profile.html", context)
        
        #case current user is a student/teacher trying to see a teacher's profile
        elif (request.user.is_teacher or request.user.is_student) and other_user.is_teacher:
            #get the teacher's status updates
            status_updates = StatusUpdate.objects.filter(user=other_user).order_by("-created_at")

            #get the courses created by the teacher
            teacher_courses = Course.objects.filter(teacher=other_user)

            #if the current user is a student, filter the courses to get the ones the current user is enrolled in
            enrolled_courses = None
            if request.user.is_student:
                enrolled_courses = teacher_courses.filter(course_enrollments__student=request.user)

            #if the current user is also a teacher, get the students they have in common
            common_students = None
            if request.user.is_teacher:
                #get the students enrolled in courses created by both the current user and the other user
                common_students = CustomUser.objects.filter(
                    enrollments__course__in=Course.objects.filter(teacher=request.user)
                ).filter(enrollments__course__in=teacher_courses).distinct()
            
            #serialize the common students
            common_students_serializer = ProfileSerializer(common_students, many=True)

            #construct the context with the fetched data
            context = {
                "user": user_serializer.data,
                "status_updates": status_updates,
                "courses": teacher_courses,
                "common_students": common_students_serializer.data,
                "enrolled_courses_by_teacher": enrolled_courses,
            }

            #render the template with the context
            return render(request, "users/user_profile.html", context)
    
    else:
        #ensure only users who have signed in can see profiles
        return HttpResponseForbidden("You do not have permission to view this profile.")



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