from .models import StatusUpdate
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from courses.models import Course, Resource
from courses.forms import normalize_and_validate_text



class StatusUpdateForm(ModelForm):
    class Meta:
        model = StatusUpdate
        fields = ["content", "course"]

class ResourceForm(forms.ModelForm):
    resource_file = forms.FileField(required=True)
    class Meta:
        model = Resource
        fields = ["course", "title", "resource_format", "resource_type"]

    #validator to normalize and validate title
    def clean_title(self):
        title = self.cleaned_data.get("title")
        #return normalized and validated title
        return normalize_and_validate_text(title, "title", "Resource")
    
    #validator to ensure the extension is allowed
    def clean_resource_file(self):
        resource_file = self.cleaned_data.get("resource_file")

        #ensure the file url is valid and ends with an allowed extension
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".svg", ".png"]
        if resource_file and not any(resource_file.name.lower().endswith(extension) for extension in allowed_extensions):
            #raise a validation error
            raise ValidationError("Invalid file format.")
        
        #return validated file
        return resource_file