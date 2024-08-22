from django.contrib import admin
from .models import Course, Lesson, Test,Resource, Enrollment, Feedback, Question, Answer, Week, UserAnswer

admin.site.register(Course)
admin.site.register(Test)
admin.site.register(Lesson)
admin.site.register(Resource)
admin.site.register(Enrollment)
admin.site.register(Feedback)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Week)
admin.site.register(UserAnswer)
