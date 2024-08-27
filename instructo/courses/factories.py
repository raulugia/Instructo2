import factory
from django.utils import timezone
from .models import Course, Week, Lesson, Test, Question, Answer, Resource, Enrollment, Feedback

class ResourceFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("sentence", nb_words=4)
    file = factory.Faker("url")
    thumbnail = factory.Faker("url")
    resource_format = "pdf"
    resource_type = "learning_material"

    class Meta:
        model = Resource

class ProfilePicResourceFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("sentence", nb_words=4)
    file = factory.Faker("url")
    thumbnail = factory.Faker("url")
    resource_format = "image"
    resource_type = "user_profile_picture"

    class Meta:
        model = Resource