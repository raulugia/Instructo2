from django.db import models
from django.conf import settings
from courses.models import Course

#All the code in this file was written without assistance

#this model represents the status updates created by users
class StatusUpdate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="status_updates")
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="status_update_course", null=True, blank=True)

    def __str__(self):
        if self.course:
            return f"Status update by @{self.user.username} for {self.course.title} at {self.created_at}"
        else:    
            return f"Status update by @{self.user.username} at {self.created_at}"
