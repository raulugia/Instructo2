from rest_framework import serializers
from .models import Course, Feedback, Enrollment, Question, Answer, Test, Week, UserAnswer, Resource, Lesson
from django.core.exceptions import ValidationError

#All the code in this file was written without assistance

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text", "is_correct"]

class UserAnswerSerializer(serializers.ModelSerializer):
    #nested serializer to include details of the selected answer
    selected_answer = AnswerSerializer(read_only=True)

    class Meta:
        model = UserAnswer
        fields = ["id", "question", "selected_answer"]

class QuestionSerializer(serializers.ModelSerializer):
    #nested serializer to include all possible answers
    answers = AnswerSerializer(many=True, read_only=True)
    #serializer method to include the user's answers to the question
    user_answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "text", "answers", "user_answers"]
    
    #method to get the user's answers to the question
    def get_user_answers(self, obj):
        #get the student from the serializer context
        student = self.context.get("student")

        if student:
            #get the answers selected by the user
            user_answer = UserAnswer.objects.filter(question=obj, student=student).first()
            #serializer the user's answer or return None if it does not exist
            return UserAnswerSerializer(user_answer).data if user_answer else None
        return None

class TestSerializer(serializers.ModelSerializer):
    #nested serializer to include the test questions
    questions = QuestionSerializer(many=True, read_only=True)
    #include a field that indicates if the test was passed
    is_passed = serializers.BooleanField(read_only=True)
    #serializer method to calculate the grade
    grade = serializers.SerializerMethodField()
    #format the deadline
    deadline = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = Test
        fields = ["id", "title", "description", "deadline", "grade", "is_passed", "questions"]
    
    #method to calculate and return the student's grade
    def get_grade(self, obj):
        #get the student from the serializer context
        student = self.context.get("student")
        
        if student:
            #set the grade to 0 if deadline has passed
            obj.update_grade_if_past_deadline()
            #calculate and return the grade
            return obj.calculate_grade(student)
        return None

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "title", "file", "thumbnail", "resource_type"]

class WeekSerializer(serializers.ModelSerializer):
    #nested serializer to include all the tests in the week
    tests = TestSerializer(many=True, read_only=True)
    #nested serializer to include the lesson materials
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = ["id", "week_number", "tests", "resources"]

class CourseSerializer(serializers.ModelSerializer):
    #nested serializer to include the courses weeks with all their data
    weeks = WeekSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["teacher", "title", "description", "duration_weeks", "cover_picture", "weeks"]
    

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["student", "course", "feedback", "created_at"]

    #validator to ensure that the user leaving feedback on a course is a student and has enrolled the course
    def validate(self, data):
        student = data.get("student")
        course = data.get("course")

         #case user is not a student
        if not student.is_student:
            #raise an error
            raise serializers.ValidationError("Only students can leave feedback")
         #case the student has not enrolled the course they want to review    
        if not Enrollment.objects.filter(student=student, course=course).exists():
            #raise an error
            raise serializers.ValidationError("Students must be enrolled in the course to leave feedback")
        #return validated data
        return data



class ResourceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields=["title", "file"]

class CourseResourcesSerializer(serializers.ModelSerializer):
    #nested serializer to include additional resources
    additional_resources = ResourceSummarySerializer(many=True, read_only=True)
    #serializer method to include the cover picture thumbnail
    cover_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields=["id","title", "cover_thumbnail", "additional_resources", "duration_weeks"]

    #method to get the course's thumbnail cover picture
    def get_cover_thumbnail(self, obj):
        return obj.cover_picture.thumbnail if obj.cover_picture else None
    


class DetailsTestSerializer(serializers.ModelSerializer):
    #format the deadline
    deadline = serializers.DateField(format="%d/%m/%Y")

    class Meta:
        model = Test
        fields = ["title", "deadline"]

class DetailsLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["lesson_number","title"]

class DetailsWeekSerializer(serializers.ModelSerializer):
    #nested serializer to include the tests in the week
    tests = DetailsTestSerializer(many=True, read_only=True)
    #nested serializer to include the lessons in the week
    lessons = DetailsLessonSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = ["tests", "week_number", "lessons"]

class DetailsFeedbackSerializer(serializers.ModelSerializer):
    #include the student's username
    student_name = serializers.CharField(source="student.username", read_only=True)
    #include the student's profile picture
    student_profile_picture = serializers.SerializerMethodField()
    #format the created at field
    created_at = serializers.DateTimeField(format="%d/%m/%Y at %H:%M")
    #format the updated at field
    updated_at = serializers.DateTimeField(format="%d/%m/%Y at %H:%M")

    class Meta:
        model = Feedback
        fields = ["student_name", "feedback", "created_at", "updated_at", "student_profile_picture"]
    
    #get the student's profile picture
    def get_student_profile_picture(self, obj):
        #get the profile picture
        profile_picture = obj.student.profile_picture
        
        #case the student has a profile picture
        if profile_picture:
            #return thumbnail or file (url)
            return profile_picture.thumbnail if profile_picture.thumbnail else profile_picture.file


class DetailsCoursesSerializer(serializers.ModelSerializer):
    #serializer method to include the cover picture thumbnail
    cover_thumbnail = serializers.SerializerMethodField()
    #nested serializer to include the course weeks
    weeks = DetailsWeekSerializer(many=True, read_only=True)
    #nested serializer to include all feedbacks in the course
    feedbacks = DetailsFeedbackSerializer(source="course_feedbacks",many=True, read_only=True)
    #serializer method to include the username of the teacher
    teacher_username = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields=["id","teacher_username","title", "description","cover_thumbnail", "weeks", "duration_weeks", "feedbacks"]

    def get_cover_thumbnail(self, obj):
        return obj.cover_picture.thumbnail if obj.cover_picture else None
    
    def get_teacher_username(self, obj):
        return obj.teacher.username