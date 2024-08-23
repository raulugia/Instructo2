from rest_framework import serializers
from courses.models import Resource
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