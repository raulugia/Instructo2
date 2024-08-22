from django.db import models
from users.models import CustomUser
from courses.models import Resource

class StatusUpdate(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="status_updates")
    content = models.CharField(max_length=500)
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_updates_resource")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Status update by @{self.user.username} at {self.created_at}"
