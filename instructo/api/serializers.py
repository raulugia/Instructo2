from rest_framework import serializers
from users.models import CustomUser
from courses.models import Course, Week, Lesson, Test
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
    #get the username of the sender
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    #format the timestamp
    timestamp = serializers.DateTimeField(format="%d/%m/%Y %H:%M",read_only=True)

    class Meta:
        model = Message
        fields = ["id","sender_username", "content", "timestamp"]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["lesson_number", "title", "description"]

class TestSerializer(serializers.ModelSerializer):
    deadline = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = Test
        fields = ["title", "description", "deadline"]

class WeekSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True)
    tests = TestSerializer(many=True)

    class Meta:
        model = Week
        fields = ["week_number", "lessons", "tests"]

class CourseAllDetailsSerializer(serializers.ModelSerializer):
    weeks = WeekSerializer(many=True)
    cover_picture = serializers.URLField(source="cover_picture.file", required=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description","cover_picture", "duration_weeks", "weeks"]



class CourseUpdateTitleDescSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["title", "description"]
    
    def validate_title(self, value):
        if value is not None:
            if not value.strip():
                raise serializers.ValidationError("Title cannot be empty.")
            if len(value) > 100:
                raise serializers.ValidationError("Title cannot be more than 100 characters.")
            return value.capitalize()
        return value
    
    def validate_description(self, value):
        if value is not None:
            if not value.strip():
                raise serializers.ValidationError("Title cannot be empty.")
            return value.capitalize()
        return value
    
    def update(self, instance, validated_data):
        #update the title if provided
        if "title" in validated_data:
            instance.title = validated_data.get("title", instance.title)
        #update the description if provided
        if "description" in validated_data:
            instance.description = validated_data.get("description", instance.description)
        
        instance.save()
        return instance
