from rest_framework import serializers
from users.models import CustomUser
from courses.models import Course
from django.db.models import Count

class CourseDetailsSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    teacher_username = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["title", "description", "student_count", "teacher_username"]

    #method to remove student_count from fields when needed
    def __init__(self, *args, **kwargs):
        #0.
        self.include_student_count = kwargs.pop("context", {}).get("include_student_count", False)
        self.include_student_count = kwargs.pop("context", {}).get("include_teacher_username", False)
        super().__init__(*args, **kwargs)
        
        #case include_student_count is not in the context
        if not self.include_student_count:
            #remove student_count
            self.fields.pop("student_count")
    
    def get_student_count(self, obj):
        return obj.get_student_count()
    
    def get_teacher_username(self, obj):
        return obj.teacher.username

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
            return CourseDetailsSerializer(courses, many=True, context={"include_student_count": True, "include_teacher_username": False}).data
        
        return []
    
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
            return CourseDetailsSerializer(top_courses, many=True, context=self.context).data
        
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
            #get the courses created by the user
            courses = Course.objects.filter(course_enrollments__student=obj).distinct()
            #returned the serialized courses
            return CourseDetailsSerializer(courses, many=True, context={"include_student_count": False, "include_teacher_username": True}).data
    
        return []