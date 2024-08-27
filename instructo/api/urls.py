from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

#All the code in this file was written without assistance

urlpatterns = [
    #get own user's details
    path("my-details/", login_required(views.get_own_user_details_view, login_url="users:signIn_view"), name="get_own_user_details_view"),
    #get students in common between user (teacher) and another teacher
    path("teacher/<str:username>/students-in-common/", login_required(views.get_students_in_common_view, login_url="users:signIn_view"), name="get_students_in_common_view"),
    #get students enrolled in a course
    path("course/<int:course_id>/students/", login_required(views.get_enrolled_students_view, login_url="users:signIn_view"), name="get_enrolled_students_view"),
    #get chat messages in a course
    path("course/<int:course_id>/chat-messages/", login_required(views.get_course_chat_history, login_url="users:signIn_view"), name="get_course_chat_history"),
    #get course full details
    path("course/<int:course_id>/details/", login_required(views.get_course_details, login_url="users:signIn_view"), name="get_course_details"),
    #update a course title/description
    path("course/<int:course_id>/update/title-description", login_required(views.update_course_title_description, login_url="users:signIn_view"), name="update_course_title_description"),
    #create a course
    path("course/create-course", login_required(views.create_course, login_url="users:signIn_view"), name="create_course"),
]
