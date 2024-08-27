from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser
from courses.models import Course
from chat.models import Message
from .serializers import *


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_own_user_details_view(request):
    #
    # if request.user.username != username:
    #     return Response({"error": "You are not authorized to access this data."}, status = status.HTTP_403_FORBIDDEN)
    if request.user.is_teacher:
        user_serializer = CustomUserTeacherSerializer(request.user)
        return Response(user_serializer.data)
    elif request.user.is_student:
        user_serializer = CustomUserStudentSerializer(request.user)
        return Response(user_serializer.data)


#view to get the students in common between 2 teachers.
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
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_course(request):
    if not request.user.is_teacher:
        return Response ({"error": "You do not have permission to perform this action."}, status=403)
    
    serializer = Post_CourseSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(teacher=request.user)

        return Response(serializer.data, status=200)
    
    return Response(serializer.errors, status=400)