#imports
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .forms import CustomSetPasswordForm
from django.urls import reverse_lazy

#All the code in this file was written without assistance

#namespace users urls
app_name = "users"

urlpatterns = [
    path("", views.signIn_view, name="signIn_view"),
    path("logout/", login_required(views.logout_view, login_url="users:signIn_view"), name="logout_view"),
    path("register/", views.register_view, name="register_view"),
    path("reset-password/", auth_views.PasswordResetView.as_view(template_name="users/reset_password.html", email_template_name="users/password_reset_email.html", success_url=reverse_lazy("users:password_reset_done")), name="password_reset"),
    path("reset-password/email-sent/", auth_views.PasswordResetDoneView.as_view(template_name="users/reset_password_done.html"), name="password_reset_done"),
    path("reset-password/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(template_name="users/reset_password_confirm.html", form_class=CustomSetPasswordForm, success_url=reverse_lazy("users:password_reset_complete")), name="password_reset_confirm"),
    path("reset-password/confirmed/", auth_views.PasswordResetCompleteView.as_view(template_name="users/reset_password_confirmed.html"), name="password_reset_complete"),
    path("home/", login_required(views.home_view, login_url="users:signIn_view"), name="home_view"),
    path("user/<str:username>/", login_required(views.user_profile_view, login_url="users:signIn_view"), name="user_profile_view"),
    path("search/", login_required(views.searchBar_view, login_url="users:signIn_view"), name="searchBar_view"),
]
