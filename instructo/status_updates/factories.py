import factory
from django.utils import timezone
from users.factories import CustomUserFactory
from .models import StatusUpdate
from courses.factories import CourseFactory

#All the code in this file was written without assistance

class StatusUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StatusUpdate

    user = factory.SubFactory(CustomUserFactory)
    content = factory.Faker("sentence", nb_words=10)
    created_at = factory.LazyFunction(timezone.now)
    course = factory.SubFactory(CourseFactory)