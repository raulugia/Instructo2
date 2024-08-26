from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import StatusUpdate
from .forms import StatusUpdateForm, ResourceForm
from django.contrib import messages
from courses.models import Course
from courses.helpers import process_resource, get_file_format
from users.models import CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

#view to create a new status update
@login_required
def create_status_update_view(request):
    # case post method
    if request.method == "POST":
        #get user
        user = request.user

        #case user is a teacher - extract course 
        if user.is_teacher:
            form_data = {
                "content": request.POST.get("content"),
                "course": request.POST.get("course")
            }
        #case user is a student - set course to None as students cannot link status updates to courses    
        elif user.is_student:
            form_data = {
                "content": request.POST.get("content"),
                "course": None
            }

        #use the data provided by the user to create a form instance
        status_update_form = StatusUpdateForm(data=form_data)

        #case form is valid
        if status_update_form.is_valid():
            try:
                #save the form data without committing 
                status_update = status_update_form.save(commit=False)
                #set the status update user
                status_update.user = user

                #case the teacher does not want to notify students or status update was created by a student
                if not form_data["course"]:
                    #set status update course to None
                    status_update.course = None
                
                #save status update to the database
                status_update.save()

                #get the file linked to the status update
                status_update_file = request.FILES.get("resource_file")
                #case there is a file
                if status_update_file:
                    #prepare the data needed by the resource form so it can be validated
                    resource_form_data = {
                        "course": status_update.course,
                        "title": status_update_file.name,
                        "resource_format": get_file_format(status_update_file),
                        "resource_type": "status_update"
                    }

                    #create a ResourceForm instance with the file data and file uploaded by user
                    resource_form = ResourceForm(data=resource_form_data, files={"resource_file": status_update_file})

                    #case form is valid
                    if resource_form.is_valid():
                        #upload file to supabase storage ans save Resource to the database - a thumbnail will be created if the file is an image
                        process_resource(status_update_file, "status_update", status_update = status_update)

                #case the status update has a course - teacher wants to notify course students of the status update    
                if status_update.course:
                    #notify students enrolled in the course
                    notify_enrolled_students(status_update.course)
                
                #redirect user to the home page
                return redirect("users:home_view")
                
            #case there are validation errors while creating an status update
            except ValidationError as error:
                #initialize the context to be sent to the user
                context ={
                    "form": status_update_form,
                    "status_updates": StatusUpdate.objects.filter(user=user).order_by("-created_at"),
                    "error": error
                }
                
                #case the user is a teacher
                if request.user.is_teacher:
                    #add courses to the context
                    context["courses"] = Course.objects.all()

                #render the home page with the context containing the validation errors
                return render(request, "users/teacher_home.html" if request.user.is_teacher else "users/student_home.html", context)
        else:
            messages.error(request, "There was an error creating the status update.")
            return redirect("users:home_view")

#method to send a notification to the students enrolled in a certain course when the teacher posts a status update linked to a course
def notify_enrolled_students(course):
    #get the channel layer for the websocket
    channel_layer = get_channel_layer()
    #get all the students enrolled in the course
    enrolled_students = CustomUser.objects.filter(enrollments__course=course, is_student=True)
    #create the notification message
    notification_message = f"There is a new update for your course '{course.title}'"

    #sent the notification to each enrolled student
    for student in enrolled_students:
        #create a unique group name
        group_name = f"{student.username}_notifications"
        #send the notification to the group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "message": notification_message
            },
        )
