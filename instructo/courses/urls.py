from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("create-course/", login_required(views.create_course_view, login_url="users:signIn_view"), name="create_course_view"),
    path("course/<int:course_id>/", login_required(views.course_details_view, login_url="users:signIn_view"), name="course_details_view"),
    path("course/<int:course_id>/enroll/", login_required(views.enroll_course_view, login_url="users:signIn_view"), name="enroll_course_view"),
    path("my-courses/<int:course_id>/", login_required(views.my_course_details_view, login_url="users:signIn_view"), name="my_course_details_view"),
    path("my-courses/<int:course_id>/additional-resources/", login_required(views.additional_resources_view, login_url="users:signIn_view"), name="additional_resources_view"),
    path("my-courses/<int:course_id>/leave-feedback/", login_required(views.leave_feedback_view, login_url="users:signIn_view"), name="leave_feedback_view"),
    path("my-courses/<int:course_id>/manage-students/", login_required(views.manage_students_view, login_url="users:signIn_view"), name="manage_students_view"),
    path("my-courses/<int:course_id>/manage-resources/", login_required(views.manage_resources_view, login_url="users:signIn_view"), name="manage_resources_view"),
    path("my-courses/<int:course_id>/<int:week_number>/", login_required(views.my_course_details_view, login_url="users:signIn_view"), name="my_course_details_view"),
    path("my-courses/<int:course_id>/<int:week_number>/test/<int:test_id>", login_required(views.test_form_view, login_url="users:signIn_view"), name="test_form_view"),
    path("my-courses/<int:course_id>/group-chat", login_required(views.group_chat_view, login_url="users:signIn_view"), name="group_chat_view"),
]