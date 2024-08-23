from .models import StatusUpdate
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from courses.models import Course


class StatusUpdateForm(ModelForm):
    resource_file = forms.FileField(required=False)
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False)

    class Meta:
        model = StatusUpdate
        fields = ["content", "resource_file", "course"]