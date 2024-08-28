import factory
from .models import Message
from users.factories import CustomUserFactory
from courses.factories import CourseFactory

class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    sender = factory.SubFactory(CustomUserFactory)
    receiver = factory.SubFactory(CustomUserFactory)
    content = factory.Faker("sentence")
    course = factory.SubFactory(CourseFactory)
    timestamp = factory.Faker("date_time_this_year")