from rest_framework import serializers
from .models import Course, Feedback, Enrollment, Question, Answer, Test, Week, UserAnswer, Resource
from django.core.exceptions import ValidationError

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text", "is_correct"]

class UserAnswerSerializer(serializers.ModelSerializer):
    selected_answer = AnswerSerializer(read_only=True)

    class Meta:
        model = UserAnswer
        fields = ["id", "question", "selected_answer"]

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    user_answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "text", "answers", "user_answers"]
    
    def get_user_answers(self, obj):
        student = self.context.get("student")
        if student:
            user_answer = UserAnswer.objects.filter(question=obj, student=student).first()
            return UserAnswerSerializer(user_answer).data if user_answer else None
        return None

class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    is_passed = serializers.BooleanField(read_only=True)
    grade = serializers.SerializerMethodField()
    deadline = serializers.DateField(format=None)

    class Meta:
        model = Test
        fields = ["id", "title", "description", "deadline", "grade", "is_passed", "questions"]
    
    def get_grade(self, obj):
        student = self.context.get("student")
        if student:
            #set the grade to 0 if deadline has passed
            obj.update_grade_if_past_deadline()
            return obj.calculate_grade(student)
        return None

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "title", "file", "thumbnail", "resource_type"]

class WeekSerializer(serializers.ModelSerializer):
    tests = TestSerializer(many=True, read_only=True)
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = ["id", "week_number", "tests", "resources"]

class CourseSerializer(serializers.ModelSerializer):
    weeks = WeekSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["teacher", "title", "description", "duration_weeks", "cover_picture", "weeks"]
    
    #validator to ensure user is a teacher
    # def validate_teacher(self, value):
    #     if not value.is_teacher:
    #         raise serializers.ValidationError("The user must be a teacher to create a course.")
    #     return value

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
    additional_resources = ResourceSummarySerializer(many=True, read_only=True)
    cover_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields=["id","title", "cover_thumbnail", "additional_resources", "duration_weeks"]

    def get_cover_thumbnail(self, obj):
        return obj.cover_picture.thumbnail if obj.cover_picture else None
    


class DetailsTestSerializer(serializers.ModelSerializer):
    deadline = serializers.DateField(format=None)

    class Meta:
        model = Test
        fields = ["title", "deadline"]

class DetailsWeekSerializer(serializers.ModelSerializer):
    tests = DetailsTestSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = ["tests", "week_number"]

class DetailsFeedbackSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.username", read_only=True)
    created_at = serializers.DateTimeField(format="%d/%m/%Y at %H:%M")
    updated_at = serializers.DateTimeField(format="%d/%m/%Y at %H:%M")

    class Meta:
        model = Feedback
        fields = ["student_name", "feedback", "created_at", "updated_at"]

class DetailsCoursesSerializer(serializers.ModelSerializer):
    cover_thumbnail = serializers.SerializerMethodField()
    weeks = DetailsWeekSerializer(many=True, read_only=True)
    feedbacks = DetailsFeedbackSerializer(source="course_feedbacks",many=True, read_only=True)

    class Meta:
        model = Course
        fields=["id","teacher","title", "description","cover_thumbnail", "weeks", "duration_weeks", "feedbacks"]

    def get_cover_thumbnail(self, obj):
        return obj.cover_picture.thumbnail if obj.cover_picture else None