import factory
from django.utils import timezone
from .models import Course, Week, Lesson, Test, Question, Answer, Resource, Enrollment, Feedback
from users.factories import CustomUserFactory

#All the code in this file was written without assistance

class ResourceFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("sentence", nb_words=4)
    file = factory.Faker("url")
    thumbnail = factory.Faker("url")
    resource_format = "pdf"
    resource_type = "learning_material"

    class Meta:
        model = Resource

class CourseFactory(factory.django.DjangoModelFactory):
    teacher = factory.SubFactory(CustomUserFactory)
    title = factory.Sequence(lambda n: f"Course {n}")
    description = factory.Faker("text", max_nb_chars=200)
    duration_weeks = 5
    
    class Meta:
        model = Course

class WeekFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory(CourseFactory)
    week_number = factory.Sequence(lambda n: n + 1)

    class Meta:
        model = Week

class LessonFactory(factory.django.DjangoModelFactory):
    week = factory.SubFactory(WeekFactory)
    lesson_number = factory.Sequence(lambda n: n + 1)
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=200)

    class Meta:
        model = Lesson

class TestFactory(factory.django.DjangoModelFactory):
    week = factory.SubFactory(WeekFactory)
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=200)
    deadline = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=10))

    class Meta:
        model = Test

class QuestionFactory(factory.django.DjangoModelFactory):
    test = factory.SubFactory(TestFactory)
    text = factory.Faker("sentence", nb_words=4)

    class Meta:
        model = Question

class AnswerFactory(factory.django.DjangoModelFactory):
    question = factory.SubFactory(QuestionFactory)
    text = factory.Faker("sentence", nb_words=4)
    is_correct = factory.Faker("boolean")

    class Meta:
        model = Answer

class EnrollmentFactory(factory.django.DjangoModelFactory):
    student = factory.SubFactory(CustomUserFactory)
    course = factory.SubFactory(CourseFactory)

    class Meta:
        model = Enrollment


class FeedbackFactory(factory.django.DjangoModelFactory):
    student = factory.SubFactory(CustomUserFactory)
    course = factory.SubFactory(CourseFactory)
    feedback = factory.Faker("text", max_nb_chars=200)

    class Meta:
        model = Feedback