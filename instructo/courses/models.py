#imports
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

#All the code in this file was written without assistance

#this model represents the courses created by teachers
class Course(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=100)
    description = models.TextField()
    duration_weeks = models.IntegerField()
    cover_picture = models.OneToOneField("Resource", null=True, blank=True, on_delete=models.CASCADE, related_name="course_cover")

    #override save method to ensure the user is a teacher
    def save(self, *args, **kwargs):
        if not self.teacher.is_teacher:
            raise ValidationError("The user must be a teacher to create a course.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

#
class Week(models.Model):
    course = models.ForeignKey(Course,  on_delete=models.CASCADE, related_name="weeks")
    week_number = models.IntegerField()

    def __str__(self):
        return f"Week {self.week_number} of {self.course.title}"

class Lesson(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="lessons")
    lesson_number = models.IntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

#this model represents the test linked to every week in a course
class Test(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="tests")
    title = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField()
    #resources = models.ManyToManyField("Resource", related_name="tasks", blank=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.title
    
    def is_passed(self):
        return self.grade is not None and self.grade >= 50
    
    def has_deadline_passed(self):
        return timezone.now().date() > self.deadline

    def update_grade_if_past_deadline(self):
        if self.has_deadline_passed() and (self.grade is None or not self.is_passed()):
            self.grade = 0
            self.save()
            return True
        return False

    def get_user_answers(self, student):
        return UserAnswer.objects.filter(test=self, student=student)
    
    def calculate_grade(self, student):
        user_answers = self.get_user_answers(student)
        total_questions = self.questions.count()

        if user_answers.count() < total_questions:
            return None

        correct_answers = sum(1 for answer in user_answers if answer.selected_answer.is_correct)
        return (correct_answers / total_questions) * 100 if total_questions > 0 else None

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

#model that represents the test answers selected by users
class UserAnswer(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_answers")
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="selected_by_users")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="user_answers")

    def __str__(self):
        return f"@{self.student.username}'s answer to question: {self.question.text}"

#this model represents the files linked to courses
class Resource(models.Model):
    RESOURCE_FORMAT_CHOICES = [
        ("pdf", "PDF"),
        ("word", "Word Document"),
        ("video", "Video"),
        ("image", "Image")
    ]

    RESOURCE_TYPE_CHOICES = [
        ("learning_material", "Learning Material"),
        ("additional_resource", "Additional Resource"),
        ("course_cover_picture", "Course Cover Picture"),
        ("user_profile_picture", "User Profile Picture"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="additional_resources")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_resources", null=True, blank=True)
    title = models.CharField(max_length=100)
    file = models.URLField(max_length=200)
    thumbnail = models.URLField(max_length=200, null=True, blank=True)
    resource_format = models.CharField(max_length=10, choices=RESOURCE_FORMAT_CHOICES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)

    def __str__(self):
        return self.title

#this model represent the students that enrolled a course
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_enrollments")
    enrollment_date = models.DateField(auto_now_add=True)

    #ensure that the combination student-course is unique so students cannot enroll the same course more than once
    class Meta:
        unique_together = ("student", "course")
    
    def __str__(self):
        return f"@{self.student.username} enrolled in {self.course.title}"
    
    def has_completed_course(self):
        tests = Test.objects.filter(week__course=self.course)
        return all(test.is_passed() for test in tests)

class Feedback(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_feedbacks")
    feedback = models.TextField()
    #use auto_now_add so the field is set upon creation
    created_at = models.DateTimeField(auto_now_add=True)
    ##use auto_now so the field is set when feedback is modified
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        #case user is not a student
        if not self.student.is_student:
            #raise an error
            raise ValidationError("Only students can leave feedback")
        #case the student has not enrolled the course they want to review
        if not Enrollment.objects.filter(student=self.student, course=self.course).exists():
            #raise an error
            raise ValidationError("Students must be enrolled in the course to leave feedback.")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Feedback by @{self.student.username} for {self.course.title}"