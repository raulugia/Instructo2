from rest_framework import serializers
from users.models import CustomUser
from courses.models import Course, Week, Lesson, Test, Question, Answer, Resource
from django.db.models import Count
from chat.models import Message
from django.utils import timezone

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
    
    #ensure the answer text is not empty
    def validate_text(self, value):
        #case the answer is empty
        if not value.strip():
            raise serializers.ValidationError("Answer text cannot be empty")
        #returned the answer text making sure the first letter is capitalized
        return value.capitalize()


class Post_QuestionSerializer(serializers.ModelSerializer):
    answers = Post_AnswerSerializer(many=True)
    class Meta:
        model = Question
        fields = ["text", "answers"]
    
    #ensure the question text is not empty
    def validate_text(self, value):
        #case the question is empty
        if not value.strip():
            raise serializers.ValidationError("Question text cannot be empty")
        #returned the question text making sure the first letter is capitalized
        return value.capitalize()
    
    #ensure each question has between 2 and 4 answers and at least one answer is correct
    def validate_answers(self, value):
        #case there are less than 2 answers
        if len(value) < 2:
            raise serializers.ValidationError("Each question must have at least 2 answers.")
        if len(value) > 4:
            raise serializers.ValidationError("Each question cannot have more than 4 answers.")
        
        #ensure at least one answer is correct
        #get the correct answer/s
        correct_answers = [answer for answer in value if answer.get("is_correct")]
        #case there are no correct answers
        if len(correct_answers) == 0:
            raise serializers.ValidationError("At least one answer must be correct.")
        
        return value


class Post_TestSerializer(serializers.ModelSerializer):
    questions = Post_QuestionSerializer(many=True)
    deadline = serializers.DateField()

    class Meta:
        model = Test
        fields = ["title", "description", "deadline", "questions"]
    
    #ensure the test title is not empty
    def validate_title(self, value):
        #case the title is empty
        if not value.strip():
            raise serializers.ValidationError("Test title cannot be empty.")
        #returned the question text making sure the first letter is capitalized
        return value.capitalize()
    
    #ensure the test description is not empty
    def validate_description(self, value):
        #case the description is empty
        if not value.strip():
            raise serializers.ValidationError("Test description cannot be empty.")
        #returned the test description making sure the first letter is capitalized
        return value.capitalize()

    #ensure the deadline is set in the future
    def validate_deadline(self, value):
        #case the deadline is in the past
        if value <= timezone.now().date():
            raise serializers.ValidationError("The deadline must be in the future.")
        #return validated deadline
        return value
    
    #ensure the test contains at least 1 question
    def validate_questions(self, value):
        #case there are no questions in the test
        if len(value) < 1:
            raise serializers.ValidationError("The test must contain at least one question.")
         #return validated questions
        return value

class Post_LessonSerializer(serializers.ModelSerializer):
    lesson_resources = Post_ResourceSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = ["lesson_number", "title", "description", "lesson_resources"]
    
    #ensure the lesson title is not empty
    def validate_title(self, value):
        #case the title is empty
        if not value.strip():
            raise serializers.ValidationError("Lesson title cannot be empty.")
        #returned the lesson text making sure the first letter is capitalized
        return value.capitalize()
    
    #ensure the lesson description is not empty
    def validate_description(self, value):
        #case the description is empty
        if not value.strip():
            raise serializers.ValidationError("Lesson description cannot be empty.")
        #returned the lesson description making sure the first letter is capitalized
        return value.capitalize()
    
    #ensure that the resource is of the correct type and format
    def validate_lesson_resources(self, value):
        #list of allowed formats
        allowed_formats = ["pdf", "word", "image", "video"]

        #iterate over the resources
        for resource in value:
            #case the resource type is not "learning_material"
            if resource["resource_type"] != "learning_material":
                raise serializers.ValidationError("Lesson resources can only be of type 'learning_material'.")
            
            #case the resource format is not allowed
            if resource["resource_format"] not in allowed_formats:
                raise serializers.ValidationError("Lesson resources format not allowed.")
        
        #return validated resources
        return value


class Post_WeekSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True)
    tests = TestSerializer(many=True)

    class Meta:
        model = Week
        fields = ["week_number", "lessons", "tests"]
    
    #ensure that the lesson_number of every lesson is not bigger than the total number of lessons in the week - cannot have lesson 10 is the week has 2 lessons
    def validate_lessons(self, value):
        #get the number of lessons in the week
        number_of_lessons = len(value)

        #iterate over the lessons
        for lesson in value:
            if lesson["lesson_number"] > number_of_lessons:
                raise serializers.ValidationError(f"Lesson number {lesson['lesson_number']} cannot be greater than the total number of lessons in the week.")
        
        #return validated lessons
        return value

class Post_CourseSerializer(serializers.ModelSerializer):
    weeks = WeekSerializer(many=True)
    cover_picture = Post_ResourceSerializer(required=False)
    additional_resources = Post_ResourceSerializer(many=True, required=False)

    class Meta:
        model = Course
        fields = ["title", "description", "duration_weeks", "cover_picture", "weeks", "additional_resources"]
    
    #ensure the course title is not empty
    def validate_title(self, value):
        #case the title is empty
        if not value.strip():
            raise serializers.ValidationError("Course title cannot be empty.")
        #returned the course title making sure the first letter is capitalized
        return value.capitalize()
    
    #ensure the course description is not empty
    def validate_description(self, value):
        #case the description is empty
        if not value.strip():
            raise serializers.ValidationError("Course description cannot be empty.")
        #returned the course description making sure the first letter is capitalized
        return value.capitalize()
    
    #ensure that the number of weeks matches duration_weeks
    #ensure the week_number of every week is not greater than the total number of weeks
    def validate_weeks(self, value):
        #get the number of weeks
        number_of_weeks = len(value)


        #case the number of weeks and duration_weeks do not match
        if number_of_weeks != self.initial_data.get("duration_weeks"):
            raise serializers.ValidationError("The total number of weeks in the course and 'duration_weeks' must be the same.")
        
        #iterate over every week
        for week in value:
            #case the week number is greater than the total number of weeks
            if week["week_number"] > number_of_weeks:
                raise serializers.ValidationError(f"Week number {week['week_number']} cannot be greater than the total number of weeks in the course.")
        
        #return validated weeks
        return value
    
    #ensure the cover picture has the right type and format
    def validate_cover_picture(self, value):
        if value:
            #case the format is not image
            if value["resource_format"] != "image":
                raise serializers.ValidationError("The cover picture of a course can only be of format image")
            
            #case the resource type is not course_cover_picture
            if value["resource_type"] != "course_cover_picture":
                raise serializers.ValidationError("The cover picture of a course can only be of type 'course_cover_picture'.")
            
        #return validated cover picture
        return value
    
    #ensure the additional resources have the right type and format
    def validate_additional_resources(self, value):
        #list of allowed formats
        allowed_formats = ["pdf", "word", "image", "video"]
        
        #iterate over the resources
        for additional_resource in value:

            #case the format is not allowed
            if additional_resource["resource_format"] not in allowed_formats:
                raise serializers.ValidationError("Additional resources format not allowed.")
            
            #case the resource type is not additional_resource
            if additional_resource["resource_type"] != "additional_resource":
                raise serializers.ValidationError("Additional resources can only be of type 'additional_resource'.")
            
        #return validated additional resources
        return value

    #override the create method
    def create(self, validated_data):
        #extract the weeks data from the validated data
        weeks_data = validated_data.pop('weeks')
        #extract the course cover picture data or set it to None
        cover_picture_data = validated_data.pop('cover_picture', None)
        #extract the course additional resources data or set it to an empty list
        additional_resources_data = validated_data.pop('additional_resources', [])
        
        #create the course instance with the remaining validated data
        course = Course.objects.create(**validated_data)

        #case there is a course cover picture
        if cover_picture_data:
            #create a Resource instance
            cover_picture = Resource.objects.create(**cover_picture_data)
            #add the cover picture to the course
            course.cover_picture = cover_picture
            #save the course to update the cover picture
            course.save()
        
        #iterate over each additional resource
        for additional_resource_data in additional_resources_data:
            #create a Resource instance for every additional resource
            Resource.objects.create(course=course, **additional_resource_data)

        #iterate over each week
        for week_data in weeks_data:
            #extract the lessons data from the week
            lessons_data = week_data.pop('lessons')
            #extract the test data from the week
            tests_data = week_data.pop('tests')

            #create a Week instance linked with the course
            week = Week.objects.create(course=course, **week_data)

            #iterate over each lesson
            for lesson_data in lessons_data:
                #extract the lesson resources or set it to an empty list
                lesson_resources_data = lesson_data.pop("lesson_resources", [])
                
                #create a Lesson instance linked with the week
                lesson = Lesson.objects.create(week=week, **lesson_data)

                #iterate over each lesson resource
                for lesson_resource_data in lesson_resources_data:
                    #create a Resource instance for each resource
                    Resource.objects.create(lesson=lesson, **lesson_resource_data)
            
            #iterate over each test withing a week
            for test_data in tests_data:
                #extract the questions from each test or set it to an empty list
                questions_data = test_data.pop('questions', [])

                #create a Test instance linked with the week
                test = Test.objects.create(week=week, **test_data)

                #iterate over each question withing the test
                for question_data in questions_data:
                    #extract the answers from the question or set it to an empty list
                    answers_data = question_data.pop('answers', [])

                    #create a Question instance linked to the test
                    question = Question.objects.create(test=test, **question_data)

                    #iterate over each answer in the question
                    for answer_data in answers_data:
                        #create an Answer instance linked to the question
                        Answer.objects.create(question=question, **answer_data)

        #return the created course instance
        return course
