#All the code in this file was written without assistance
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

app_name = "status_updates"

urlpatterns = [
    path("create/",login_required(views.create_status_update_view, login_url="users:signIn_view"), name="create_status_update_view"),
]