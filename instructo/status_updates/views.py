from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import StatusUpdate
from .forms import StatusUpdateForm
from django.contrib import messages
from courses.helpers import process_resource

@login_required
def create_status_update_view(request):
    if request.method == "POST":
        user = request.user
        if user.is_teacher:
            status_update_form = StatusUpdateForm(request.POST, request.FILES)
            if status_update_form.is_valid():
                try:
                    status_update = status_update_form.save(commit=False)
                    status_update.user = user
                    status_update.save()

                    if "status_update_file" in request.FILES:
                        status_update_file = request.FILES["status_update_file"]
                        process_resource(status_update_file, "status_update", status_update=status_update)
                    
                    return redirect("users:home_view")
                    

                except ValidationError as error:
                    return render(request, "students/home.html", {"form": status_update_form})
        else:
            messages.error(request, "Only teachers can create status updates.")
            return redirect("users:home_view")