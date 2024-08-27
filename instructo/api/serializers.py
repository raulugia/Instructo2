from rest_framework import serializers
from users.models import CustomUser
from courses.models import Course, Week, Lesson, Test, Question, Answer, Resource
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

class Post_ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["title", "file", "thumbnail", "resource_format", "resource_type"]


class Post_AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["text", "is_correct"]


class Post_QuestionSerializer(serializers.ModelSerializer):
    answers = Post_AnswerSerializer(many=True)
    class Meta:
        model = Question
        fields = ["text", "answers"]

class Post_TestSerializer(serializers.ModelSerializer):
    questions = Post_QuestionSerializer(many=True)
    deadline = serializers.DateField()

    class Meta:
        model = Test
        fields = ["title", "description", "deadline", "questions"]

class Post_LessonSerializer(serializers.ModelSerializer):
    lesson_resources = Post_ResourceSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = ["lesson_number", "title", "description", "lesson_resources"]


class Post_WeekSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True)
    tests = TestSerializer(many=True)

    class Meta:
        model = Week
        fields = ["week_number", "lessons", "tests"]

class Post_CourseSerializer(serializers.ModelSerializer):
    weeks = WeekSerializer(many=True)
    cover_picture = Post_ResourceSerializer(required=False)
    additional_resources = Post_ResourceSerializer(many=True, required=False)

    class Meta:
        model = Course
        fields = ["title", "description", "duration_weeks", "cover_picture", "weeks", "additional_resources"]
    
    def create(self, validated_data):
        weeks_data = validated_data.pop('weeks')
        cover_picture_data = validated_data.pop('cover_picture', None)
        additional_resources_data = validated_data.pop('additional_resources', [])
        
        course = Course.objects.create(**validated_data)

        if cover_picture_data:
            cover_picture = Resource.objects.create(**cover_picture_data)
            course.cover_picture = cover_picture
            course.save()
        
        for additional_resource_data in additional_resources_data:
            Resource.objects.create(course=course, **additional_resource_data)

        for week_data in weeks_data:
            lessons_data = week_data.pop('lessons')
            tests_data = week_data.pop('tests')
            week = Week.objects.create(course=course, **week_data)

            for lesson_data in lessons_data:
                lesson_resources_data = lesson_data.pop("lesson_resources", [])
                lesson = Lesson.objects.create(week=week, **lesson_data)

                for lesson_resource_data in lesson_resources_data:
                    Resource.objects.create(lesson=lesson, **lesson_resource_data)
            
            for test_data in tests_data:
                questions_data = test_data.pop('questions', [])
                test = Test.objects.create(week=week, **test_data)

                for question_data in questions_data:
                    answers_data = question_data.pop('answers', [])
                    question = Question.objects.create(test=test, **question_data)
                
                    for answer_data in answers_data:
                        Answer.objects.create(question=question, **answer_data)

        return course
