#All the code in this file was written without assistance
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .forms import CustomSetPasswordForm

app_name = "users"

urlpatterns = [
    #
    path("", views.signIn_view, name="signIn_view"),
    path("register/", views.register_view, name="register_view"),
    path("reset-password/", auth_views.PasswordResetView.as_view(template_name="users/reset_password.html"), name="password_reset"),
    path("reset-password/email-sent/", auth_views.PasswordResetDoneView.as_view(template_name="users/reset_password_done.html"), name="password_reset_done"),
    path("reset-password/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(template_name="users/reset_password_confirm.html", form_class=CustomSetPasswordForm), name="password_reset_confirm"),
    path("reset-password/confirmed/", auth_views.PasswordResetCompleteView.as_view(template_name="users/reset_password_confirmed.html"), name="password_reset_complete"),
    path("home/", login_required(views.home_view, login_url="users:signIn_view"), name="home_view"),
    path("search/", login_required(views.searchBar_view, login_url="users:signIn_view"), name="searchBar_view"),
]
