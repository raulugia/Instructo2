import factory
from .models import Message
from users.factories import CustomUserFactory
from courses.factories import CourseFactory

#All the code in this file was written without assistance

class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    sender = factory.SubFactory(CustomUserFactory)
    receiver = factory.SubFactory(CustomUserFactory)
    content = factory.Faker("sentence")
    course = factory.SubFactory(CourseFactory)
    timestamp = factory.Faker("date_time_this_year")