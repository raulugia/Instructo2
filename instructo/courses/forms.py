from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import Course, Question, Answer, Test, Lesson,Week, Resource, UserAnswer, Feedback
from django import forms
from django.utils import timezone

#helper to normalize and validate text
def normalize_and_validate_text(field_value, field_name, model_name):
    #case there is a field_value and it is not a whitespace
    if field_value and len(field_value.strip()) > 0:
        #normalize - remove spaces at the beginning/end and capitalize first letter
        field_value = field_value.strip().capitalize()
    
    #case there is no field_value or it is a whitespace
    if not field_value or len(field_value.strip())== 0:
        #raise validation error
        raise ValidationError(f"{model_name}: {field_name} cannot be empty")
    
    #return the normalized and validated field_value
    return field_value

class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "duration_weeks", "cover_picture"]
    
    def clean_duration_weeks(self):
        duration_weeks = self.cleaned_data.get("duration_weeks")
        if duration_weeks < 1 or duration_weeks > 30:
            raise ValidationError("Duration must be between 1 and 30.")
        return duration_weeks
    
    def clean_title(self):
        title = self.cleaned_data.get("title")
        #
        return normalize_and_validate_text(title, "title", "Course")
        # #case there is a title and it is not a whitespace
        # if title and len(title.strip()) > 0:
        #     #normalize - remove spaces at the beginning/end and capitalize first letter
        #     title = title.strip().capitalize()

        # #case there is no title or it is a whitespace
        # if not title or len(title.strip()) == 0:
        #     #raise validation error
        #     raise ValidationError("Title cannot be empty.")

        # #return normalized title    
        # return title
    
    def clean_description(self):
        description = self.cleaned_data.get("description")
        return normalize_and_validate_text(description, "description", "Course")
        # #case there is a title and it is not a whitespace
        # if description and len(description.strip()) > 0:
        #     #normalize - remove spaces at the beginning/end and capitalize first letter
        #     description = description.strip().capitalize()

        # #case there is no description or it is a whitespace
        # if not description or len(description.strip()) == 0:
        #     #raise validation error
        #     raise ValidationError("Description cannot be empty.")
        
        # #return normalized description
        # return description
    
    # def clean_cover_picture(self):
    #     cover_picture = self.cleaned_data.get("cover_picture")
    #     if cover_picture and not cover_picture.lower().endswith((".jpg", ".jpeg", ".svg", ".png", ".bmp", ".webp", ".heic", ".heif", ".tiff")):
    #         raise ValidationError("Invalid image format for course cover picture.")
    #     return cover_picture

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "test"]
    
    def clean_text(self):
        #get text from cleaned data
        text = self.cleaned_data.get("text")
        return normalize_and_validate_text(text, "text", "Question")
    #    #case there is a text and it is not a whitespace
    #     if text and len(text.strip()) > 0:
    #         #normalize - remove spaces at the beginning/end and capitalize first letter
    #         text = text.strip().capitalize()

    #     #case there is no text or it is a whitespace
    #     if not text or len(text.strip()) == 0:
    #         #raise validation error
    #         raise ValidationError("Questions cannot be empty.")

    #     #return normalized text    
    #     return text

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["text", "is_correct", "question"]

    #validator to normalize and validate text
    def clean_text(self):
        #get text from cleaned data
        text = self.cleaned_data.get("text")
        #return validated and normalized text
        return normalize_and_validate_text(text, "text", "Answer")

    #validator to ensure answer is not duplicated for the same question
    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("text")
        question = cleaned_data.get("question")
        is_correct = cleaned_data.get("is_correct")

        #case text and question exist
        if text and question:
            #ensure the same question does not have duplicate answers
            existing_answer = Answer.objects.filter(question=question, text__iexact=text).exclude(pk=self.instance.pk)

            #case answer is duplicated
            if existing_answer.exists():
                #raise a validation error
                raise ValidationError("Answer is duplicated.")
        
        #case question exists
        if is_correct:
            self.cleaned_data["is_correct"] = True
        
        #return validated data
        return cleaned_data
    
    def final_validation(self):
        question = self.cleaned_data.get("question")
        correct_answers = Answer.objects.filter(question=question, is_correct=True)
        if self.cleaned_data.get("is_correct"):
            correct_answers = list(correct_answers) + [self.instance]
        
        if len(correct_answers) == 0:
            raise ValidationError("Questions must have at least one correct answer")

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ["title", "description", "deadline", "week"]

    def clean_title(self):
        title = self.cleaned_data.get("title")
        #
        return normalize_and_validate_text(title, "title", "Test")
    
    def clean_description(self):
        description = self.cleaned_data.get("description")
        #
        return normalize_and_validate_text(description, "description", "Test")
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")

        #ensure the deadline is in the future
        if deadline and deadline <= timezone.now().date():
            #raise a validation error
            raise ValidationError("The deadline must be in the future")
        
        #return validated deadline
        return deadline

    def clean_week(self):
        week = self.cleaned_data.get("week")

        #ensure the selected week exists
        if not Week.objects.filter(id=week.id).exists():
            #raise a validation error
            raise ValidationError("The selected week does not exist.")

        #ensure that the week number is within the course duration
        if week.week_number > week.course.duration_weeks:
            #raise a validation error
            raise ValidationError("This week exceeds the course's duration.")
        
        #return validated week
        return week

class LessonForm (forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["week", "title", "description", "lesson_number"]

class WeekForm(forms.ModelForm):
    class Meta:
        model = Week
        fields = ["week_number", "course"]
    
    #validator to ensure the week number is positive and not 0, not greater than the course duration and not duplicated
    def clean_week_number(self):
        week_number = self.cleaned_data.get("week_number")
        course = self.cleaned_data.get("course")
        print(f"week validator, self: {self}, week number: {week_number}, course: {course}")

        #case week number is < 1
        if week_number < 1:
            #raise a validation error
            ValidationError("Week number must be positive")
        
        #case the week number is greater than the course duration
        if course and week_number > course.duration_weeks:
            #raise a validation error
            ValidationError("Week number exceeds the course duration.")
        
        #try to find an existing week linked to the same course and with the same week number - exclude current week
        existing_week = Week.objects.filter(course=course, week_number=week_number).exclude(pk=self.instance.pk)
        #case week is duplicated
        if existing_week.exists():
            #raise a validation error
            raise ValidationError(f"Week {week_number} already exists in this course.")
        
        #return validated week_number
        return week_number
    
    #validator to ensure the course exists
    # def clean_course(self):
    #     course = self.cleaned_data.get("course")

    #     if not course:
    #         #raise a validation error
    #         raise ValidationError("Course is required.")

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["course","lesson", "title", "file", "resource_format", "resource_type"]
    
    #to normalize and validate title
    def clean_title(self):
        title = self.cleaned_data.get("title")
        #return normalized and validated title
        return normalize_and_validate_text(title, "title", "Resource")
    
    #validator to ensure the extension is allowed
    def clean_file(self):
        file = self.cleaned_data.get("file")

        #ensure the file url is valid and ends with an allowed extension
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".svg", ".png"]
        if file and not any(file.lower().endswith(extension) for extension in allowed_extensions):
            #raise a validation error
            raise ValidationError("Invalid file format.")
        
        #return validated file
        return file
    
    #validator to ensure the format is allowed
    def clean_resource_format(self):
        resource_format = self.cleaned_data.get("resource_format")

        #ensure that the format is valid
        valid_formats = dict(Resource.RESOURCE_FORMAT_CHOICES).keys()
        #case format is not valid
        if resource_format not in valid_formats:
            #raise a validation error
            raise ValidationError("Invalid resource format.")
        
        #return validated format
        return resource_format
    
    #validator to ensure the week exists
    def clean_week(self):
        week = self.cleaned_data["week"]

        #ensure the week exists
        if not Week.objects.filter(id=week.id).exists():
            #raise a validation error
            raise ValidationError("The selected week does not exist.")
        
        #return validated week
        return week


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["feedback"]

    def clean_feedback(self):
        feedback = self.cleaned_data.get('feedback')
        print(feedback)

        if len(feedback.strip()) < 100:
            raise ValidationError("Feedback is too short. Please, provide more details.")
        elif len(feedback.strip()) > 600:
            raise ValidationError("Feedback is too long. Your feedback cannot be larger than 600 characters.")
        
        return feedback

