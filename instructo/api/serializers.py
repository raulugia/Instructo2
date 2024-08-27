from rest_framework import serializers
from users.models import CustomUser
from courses.models import Course
from django.db.models import Count
from chat.models import Message

class CourseDetailsSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id","title", "description", "student_count"]
        
    
    def get_student_count(self, obj):
        return obj.get_student_count()

class CustomUserTeacherSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    account_created = serializers.DateTimeField(source="date_joined", format="%d/%m/%Y %H:%M:%S")
    top_courses = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "city", "country", "profile_picture", "is_teacher", "is_student", "email", "top_courses","courses","account_created"]
    
    #get the courses create dby the teacher
    def get_courses(self, obj):
        if obj.is_teacher:
            #get the courses created by the user
            courses = Course.objects.filter(teacher=obj)
            #returned the serialized courses
            return CourseDetailsSerializer(courses, many=True).data
        
        #return an error if the user is not a teacher
        raise serializers.ValidationError("You must be a teacher to access this data.")
    
    #get the top 3 courses based on number of students
    def get_top_courses(self, obj):
        if obj.is_teacher:
            #get all courses created by the teacher
            courses = Course.objects.filter(teacher=obj).annotate(student_count=Count("course_enrollments"))

            #case all courses have 0 students - teacher is new or not popular
            if all(course.student_count == 0 for course in courses):
                return [{"message": "All courses have 0 students."}]

            #sort the courses by student count in descending order to get the top 3 courses
            top_courses = courses.order_by("-student_count")[:3]

            #return the serialized top 3 courses
            return CourseDetailsSerializer(top_courses, many=True).data
        
        #return an error if the user is not a teacher
        raise serializers.ValidationError("You must be a teacher to access this data.")

class CustomUserStudentSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    account_created = serializers.DateTimeField(source="date_joined", format="%d/%m/%Y %H:%M:%S")

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "city", "country", "profile_picture", "is_teacher", "is_student", "email","courses","account_created"]
    
    def get_courses(self, obj):
        if obj.is_student:
            courses = Course.objects.filter(course_enrollments__student=obj).distinct()
            return CourseDetailsSerializer(courses, many=True).data
        return []
    
class CommonStudentsSerializer(serializers.ModelSerializer):
    enrolled_courses = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "enrolled_courses"]

    
    def get_enrolled_courses(self, obj):
        courses = Course.objects.filter(course_enrollments__student=obj).distinct()
        return CourseDetailsSerializer(courses, many=True).data
    
class EnrolledStudentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username"]

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    timestamp = serializers.DateTimeField(format="%d/%m/%Y %H:%M",read_only=True)

    class Meta:
        model = Message
        fields = ["id","sender_username", "content", "timestamp"]