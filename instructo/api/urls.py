from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("my-details/", login_required(views.get_own_user_details_view, login_url="users:signIn_view"), name="get_own_user_details_view"),

]
