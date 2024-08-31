from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser
from courses.models import Course
from chat.models import Message
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


#All the code in this file was written without assistance

#view to get own details
@swagger_auto_schema(
    #http method for this schema
    method="get",
    #description of what the API endpoint does
    operation_description="Retrieve details of the authenticated user. The response will contain different fields depending on whether the user is a teacher or a student. Only authenticated users can access this data.",
    #possible responses
    responses={200: CustomUserTeacherSerializer, 403: "Permission Denied"},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_own_user_details_view(request):
    #case the user is a teacher
    if request.user.is_teacher:
        #serialize the teacher's details
        user_serializer = CustomUserTeacherSerializer(request.user)
        #return the serialized data 
        return Response(user_serializer.data)
    
    #case the user is a student
    elif request.user.is_student:
        #serialize the student's details
        user_serializer = CustomUserStudentSerializer(request.user)
        #return the serialized data 
        return Response(user_serializer.data)


#view to get the students in common between 2 teachers.
@swagger_auto_schema(
    #http method for this schema
    method="get",
    #description of what the API endpoint does
    operation_description="This endpoint is only available for teachers. The response includes the students in common with another teacher. Only authenticated users can access this data.",
    #possible responses
    responses={200: CustomUserTeacherSerializer(many=True), 403: "Permission Denied", 404: "User Not Found"},
    #details about the parameters
    manual_parameters=[openapi.Parameter("username", openapi.IN_PATH, description= "Username of the other teacher", type=openapi.TYPE_STRING)],    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_students_in_common_view(request, username):
    if(request.user.is_teacher):
        try:
            #get other user
            other_user = CustomUser.objects.get(username=username)

            #case the other user is a teacher
            if other_user.is_teacher:
                #get current teacher's courses
                current_user_courses = request.user.courses.all()
                #get other teacher's courses 
                other_user_courses = other_user.courses.all()

                #find common students
                common_students = CustomUser.objects.filter(enrollments__course__in=current_user_courses).filter(enrollments__course__in=other_user_courses).distinct()

                #serialize common students
                serializer = CommonStudentsSerializer(common_students, many=True)

                #return the serialized data
                return Response(serializer.data, status=200)
            
            #case the other user is not a teacher
            else:
                return Response({"error": "The user is not a teacher."}, status=400)
        
        #case user does not exist
        except CustomUser.DoesNotExist:
            return Response({"error": "The user does not exist."}, status=404)
    
    #case current user is not a teacher
    else:
        return Response({"error": "You must be a teacher to access this data."}, status=403)

#view to get all the students enrolled in a course
@swagger_auto_schema(
    #http method for this schema
    method="get",
    #description of what the API endpoint does
    operation_description="Retrieve a list of students enrolled in a specific course. Only authenticated users can access this data.",
    #possible responses
    responses={200: EnrolledStudentsSerializer(many=True), 404: "Course Not Found"},
    #details about the parameters
    manual_parameters=[openapi.Parameter("course_id", openapi.IN_PATH, description= "ID of the course", type=openapi.TYPE_INTEGER)],    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_enrolled_students_view(request, course_id):
    try:
        #get the course base don provided course id
        course = Course.objects.get(id=course_id)

        #get all students enrolled in the course
        enrolled_students = CustomUser.objects.filter(enrollments__course=course)

        #serialize the enrolled students
        serializer = EnrolledStudentsSerializer(enrolled_students, many=True)

        return Response(serializer.data, status=200)
    
    except Course.DoesNotExist:
        return Response({"error": "The course does not exist."}, status=404)
    
#view to get all the course details
@swagger_auto_schema(
    #http method for this schema
    method="get",
    #description of what the API endpoint does
    operation_description="Retrieve all details of a specific course including its weeks, lessons and tests. Only authenticated users can access this data.",
    #possible responses
    responses={200: CourseAllDetailsSerializer, 404: "Course Not Found"},
    #details about the parameters
    manual_parameters=[openapi.Parameter("course_id", openapi.IN_PATH, description= "ID of the course", type=openapi.TYPE_INTEGER)],    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_course_details(request, course_id):
    try:
        #get the course using the provided course_id
        course = Course.objects.prefetch_related("weeks__lessons", "weeks__tests").get(id=course_id)

        #serialize the course details
        serializer = CourseAllDetailsSerializer(course)

        #return the serialized course
        return Response(serializer.data, status=200)
    
    except Course.DoesNotExist:
        return Response({"error": "The course does not exist."}, status=404)

#view to get the chat messages of a course
@swagger_auto_schema(
    #http method for this schema
    method="get",
    #description of what the API endpoint does
    operation_description="Retrieve the chat history of a specific course. Users must be authenticated enrolled students or course teacher to access this data.",
    #possible responses
    responses={200: MessageSerializer(many=True), 403: "Permission Denied", 404: "Course Not Found",},
    #details about the parameters
    manual_parameters=[openapi.Parameter("course_id", openapi.IN_PATH, description= "ID of the course", type=openapi.TYPE_INTEGER)],    
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_course_chat_history(request, course_id):
    try:
        #get the course using the provided course_id
        course = Course.objects.get(id=course_id)
        
        #case the user is the course teacher or an enrolled student
        if request.user == course.teacher or request.user.enrollments.filter(course=course).exists():
            #get all the chat messages for the course
            messages = Message.objects.filter(course=course).order_by('timestamp')

            #serialize the messages
            serializer = MessageSerializer(messages, many=True)

            #return the serialized messages
            return Response(serializer.data, status=200)
        
        #case user is not the course teacher or an enrolled student
        else:
            return Response({"error": "You must be enrolled in the course to access this data."}, status=403)
    
    except Course.DoesNotExist:
        return Response({"error": "The course does not exist."}, status=404)

#view to update a courses's title/description
@swagger_auto_schema(
    #http method for this schema
    method="patch",
    #description of what the API endpoint does
    operation_description="Update the title and/or description of a specific course. User must be the course teacher to perform this operation.",
    #possible responses
    responses={200: CourseUpdateTitleDescSerializer, 400: "Bad Request", 403: "Permission Denied", 404: "Course Not Found",},
    #details about the parameters
    manual_parameters=[openapi.Parameter("course_id", openapi.IN_PATH, description= "ID of the course", type=openapi.TYPE_INTEGER)],    
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_course_title_description(request, course_id):
    try:
        #get the course using the provided course_id
        course = Course.objects.get(id=course_id)

        #case the user is not the course's teacher
        if request.user != course.teacher:
            return Response ({"error": "You do not have permission to perform this action."}, status=403)
        
        serializer = CourseUpdateTitleDescSerializer(course, data=request.data, partial=True)

        #case data was successfully validated
        if serializer.is_valid():
            #save the updated course data
            serializer.save()

            #return the data
            return Response(serializer.data, status=200)
        
        #case data was not successfully serialized
        return Response(serializer.errors, status=400)
    
    except Course.DoesNotExist:
        return Response({"error": "The course does not exist."}, status=404)


#view to create a course
@swagger_auto_schema(
    #http method for this schema
    method="post",
    #description of what the API endpoint does
    operation_description="Create a new course. User must be a teacher to perform this operation.",
    #expected request body
    request_body=Post_CourseSerializer,
    #possible responses
    responses={200: Post_CourseSerializer, 400: "Bad Request", 403: "Permission Denied",},   
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_course(request):
    #case the user is not a teacher
    if not request.user.is_teacher:
        return Response ({"error": "You do not have permission to perform this action."}, status=403)
    
    #initialize the serializer with the request data
    serializer = Post_CourseSerializer(data=request.data)

    #case serializer is valid
    if serializer.is_valid():
        #save the course data with the authenticated user as the teacher
        serializer.save(teacher=request.user)
        ##return the course details
        return Response(serializer.data, status=200)
    
    #case the data was not valid
    return Response(serializer.errors, status=400)