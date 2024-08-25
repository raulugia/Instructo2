from rest_framework import serializers
from courses.models import Resource, Course, Week, Test
from status_updates.models import StatusUpdate

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["title", "file", "thumbnail", "resource_format"]

    #method to exclude thumbnail from the serialized data if the file is not an image
    def to_representation(self, instance):
        #get default serialized data
        representation = super().to_representation(instance)

        #case file is not an image
        if instance.resource_format != "image":
            #remove the thumbnail from the serialized representation
            representation.pop("thumbnail")
        #return the representation
        return representation

class StatusUpdateSerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source="user.username", read_only=True)
    resources = ResourceSerializer(many=True, source="status_update_resource", read_only=True)
    created_at = serializers.DateTimeField(format="%d/%m/%Y at %H:%M")

    class Meta:
        model = StatusUpdate
        fields = ["teacher_username", "content", "created_at", "course", "resources"]



class StudentHome_TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ["title", "deadline"]

class StudentHome_WeekSerializer(serializers.ModelSerializer):
    tests =  StudentHome_TestSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = ["week_number", "tests"]

class StudentHome_CourseSerializer(serializers.ModelSerializer):
    weeks = StudentHome_WeekSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["title", "weeks"]

class StudentHome_StatusUpdateSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source="user_username", read_only=True)
    resources = ResourceSerializer(many=True, source="status_update_resource", read_only=True)
    created_at = serializers.DateTimeField(format="%d/%m/%Y at %H:%M")

    class Meta:
        model = StatusUpdate
        fields = ["student_username", "content", "created_at", "resources"]


class StudentHomeSerializer(serializers.Serializer):
    student_status_updates = StudentHome_StatusUpdateSerializer(many=True)
    courses_status_updates = StudentHome_StatusUpdateSerializer(many=True)
    courses = StudentHome_CourseSerializer(many=True)

