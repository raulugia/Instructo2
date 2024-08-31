from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import Course, Question, Answer, Test, Lesson,Week, Resource, Feedback
from django import forms
from django.utils import timezone

#All the code in this file was written without assistance

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
    
    #validate duration_weeks
    def clean_duration_weeks(self):
        #get duration_weeks
        duration_weeks = self.cleaned_data.get("duration_weeks")
        #case course is too long/short
        if duration_weeks < 1 or duration_weeks > 30:
            #raise a validation error
            raise ValidationError("Duration must be between 1 and 30.")
        #returned validated duration_weeks
        return duration_weeks
    
    def clean_title(self):
        title = self.cleaned_data.get("title")
        #validate title
        return normalize_and_validate_text(title, "title", "Course")
        
    
    def clean_description(self):
        description = self.cleaned_data.get("description")
        #validate description
        return normalize_and_validate_text(description, "description", "Course")
        

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "test"]
    
    def clean_text(self):
        #get text from cleaned data
        text = self.cleaned_data.get("text")
        return normalize_and_validate_text(text, "text", "Question")
    
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
        #get form cleaned data
        cleaned_data = super().clean()
        #get the text
        text = cleaned_data.get("text")
        #get the question
        question = cleaned_data.get("question")
        #get the is_correct value
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
            #set is_correct to true
            self.cleaned_data["is_correct"] = True
        
        #return validated data
        return cleaned_data
    
    #final validation once all answers have been created - ensure at least one answer is correct
    def final_validation(self):
        #get the question
        question = self.cleaned_data.get("question")
        #fetch the correct answers linked to the question
        correct_answers = Answer.objects.filter(question=question, is_correct=True)

        #case the current answer is correct
        if self.cleaned_data.get("is_correct"):
            #add it to the list of correct answers
            correct_answers = list(correct_answers) + [self.instance]
        
        #case there are no correct answers
        if len(correct_answers) == 0:
            #raise a validation error
            raise ValidationError("Questions must have at least one correct answer")

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ["title", "description", "deadline", "week"]

    #validate the title
    def clean_title(self):
        #get the title
        title = self.cleaned_data.get("title")
        #returned the validated title
        return normalize_and_validate_text(title, "title", "Test")
    
    #validate the description
    def clean_description(self):
        #get the description
        description = self.cleaned_data.get("description")
        #return the validated description
        return normalize_and_validate_text(description, "description", "Test")
    
    #validate deadline
    def clean_deadline(self):
        #get the deadline
        deadline = self.cleaned_data.get("deadline")

        #ensure the deadline is in the future
        if deadline and deadline <= timezone.now().date():
            #raise a validation error
            raise ValidationError("The deadline must be in the future")
        
        #return validated deadline
        return deadline
    
    #validate week
    def clean_week(self):
        #get week from form
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

    #validate feedback
    def clean_feedback(self):
        #get feedback
        feedback = self.cleaned_data.get('feedback')
        
        #raise a validation error if it is too short/long
        if len(feedback.strip()) < 100:
            raise ValidationError("Feedback is too short. Please, provide more details.")
        elif len(feedback.strip()) > 600:
            raise ValidationError("Feedback is too long. Your feedback cannot be larger than 600 characters.")
        
        #return validated feedback
        return feedback

