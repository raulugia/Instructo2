import factory
from django.contrib.auth.hashers import make_password
from .models import CustomUser
from courses.factories import ResourceFactory

#All the code in this file was written without assistance

class CustomUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
    
    #create a unique email for each user
    email = factory.Sequence(lambda n: f"user{n}@instructo.com")
    #create a unique username for each user
    username = factory.Sequence(lambda n: f"user_{n}")

    #set default values for the other fields
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    date_of_birth = factory.Faker("date_of_birth")
    city = factory.Faker("city")
    country = factory.Faker("country")

    #create a profile picture using the Resource factory model from app courses
    profile_picture = factory.SubFactory(ResourceFactory, resource_type="user_profile_picture", resource_format="image")

    #set default to user is teacher
    is_student = False
    is_teacher = True

    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        if create:
            obj.password = make_password("password")
            obj.save()

