from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import StatusUpdate
from .forms import StatusUpdateForm, ResourceForm
from django.contrib import messages
from courses.models import Course
from courses.helpers import process_resource, get_file_format

@login_required
def create_status_update_view(request):
    if request.method == "POST":
        print("FILES: ", request.FILES)
        print("FILES KEYS: ", request.FILES.keys())
        user = request.user
        if user.is_teacher:
            form_data = {
                "content": request.POST.get("content"),
                "course": request.POST.get("course")
            }

            status_update_form = StatusUpdateForm(data=form_data)

            if status_update_form.is_valid():
                print("status form valid")
                try:
                    status_update = status_update_form.save(commit=False)
                    status_update.user = user

                    #case the teacher does not want to notify students - status update not related to a course
                    if not form_data["course"]:
                        status_update.course = None
                    
                    status_update.save()

                    status_update_file = request.FILES.get("resource_file")
                    print("file: ", status_update_file)
                    if status_update_file:
                        print("there is a file")
                        resource_form_data = {
                            "course": status_update.course,
                            "title": status_update_file.name,
                            "resource_format": get_file_format(status_update_file),
                            "resource_type": "status_update"
                        }

                        resource_form = ResourceForm(data=resource_form_data, files={"resource_file": status_update_file})

                        if resource_form.is_valid():
                            print("res form valid")
                            process_resource(status_update_file, "status_update", status_update = status_update)
                        else:
                            print("resorform invalid errors: ", resource_form.errors)
                    
                    return redirect("users:home_view")
                    

                except ValidationError as error:
                    return render(request, "students/home.html", {
                        "form": status_update_form, 
                        "courses": Course.objects.all(), 
                        "status_updates": StatusUpdate.objects.filter(user=user).order_by("-created_at"),
                        "error": error
                    })
        else:
            messages.error(request, "Only teachers can create status updates.")
            return redirect("users:home_view")