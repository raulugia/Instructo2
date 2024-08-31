from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

#All the code in this file was written without assistance

schema_view = get_schema_view(
   openapi.Info(
      title="Instructo API",
      default_version='v1',
      description="API documentation for Instructo",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@instructo.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

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
