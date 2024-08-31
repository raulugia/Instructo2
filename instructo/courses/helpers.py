from .models import Resource

from .forms import QuestionForm, AnswerForm, TestForm, WeekForm, LessonForm
from django.core.exceptions import ValidationError
import os
import tempfile
from .tasks import create_thumbnail_and_upload, upload_file_to_supabase
from .supabase_client import delete_from_supabase
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import CustomUser

#All the code in this file was written without assistance

def create_week(course, week_number, data, files):
    #initialize the week form with the course and week number
    week_form = WeekForm(data={
        "week_number": week_number,
        "course": course.id,
    })

    #case the form is valid
    if week_form.is_valid():
        #save the week instance
        week = week_form.save()

        #get the number of lessons by counting the number of lesson titles in the form data - needed as template form is generated dynamically with javascript
        lesson_keys = [key for key in data.keys() if key.startswith(f"week_{week_number}_lesson_") and key.endswith("_title")]
        number_of_lessons = len(lesson_keys)
        
        #iterate over each lesson and create it
        for j in range(1, number_of_lessons + 1):
            lesson = create_lesson(week, week_number, j, data, files, course)
        
        #create the test linked to the week
        create_test(week, data)

        #returned the created week
        return week
    #case the form is not valid - raise a validation error
    else:
        raise ValidationError(week_form.errors)

#method to create the lessons in a week
def create_lesson(week, week_number, lesson_number, data, files, course):
    #get the lesson title from the form data
    lesson_title = data.get(f"week_{week_number}_lesson_{lesson_number}_title")
    #get the lesson description from the form data
    lesson_description = data.get(f"week_{week_number}_lesson_{lesson_number}_description")

    #initialize the lesson form with the extracted data
    lesson_form = LessonForm(data={
        "week": week,
        "title": lesson_title,
        "description": lesson_description,
        "lesson_number": lesson_number
    })

    #case the form is valid
    if lesson_form.is_valid():
        #save the lesson instance
        lesson = lesson_form.save()

        #get the learning material linked to the lesson
        learning_material = files.get(f"week_{week_number}_lesson_{lesson_number}_learning_material")
        #case there is learning material
        if learning_material:
            #create and save a resource instance, create thumbnail if needed and upload files to supabase storage
            process_resource(learning_material, "learning_material", lesson=lesson, course=course)
        #return the created lesson
        return lesson
    #case the form is not valid - raise an error
    else:
        raise ValidationError(lesson_form.errors)

#function to create a test and the questions and answers linked to it for a given week
def create_test(week, data):
    #get the keys linked to questions - needed due to dynamic form
    question_keys = [key for key in data.keys() if key.startswith(f"question_week_{week.week_number}_")]
    #determine the number of questions based on the length of question_keys
    number_of_questions = len(question_keys)

    #initialize the test form with the extracted data
    test_form = TestForm(data={
        "title": f"Task for Week {week.week_number}",
        "description": f"Task description for Week {week.week_number}",
        "deadline": data.get(f"deadline_week_{week.week_number}"),
        "week": week.id
    })

    #case form validated successfully
    if test_form.is_valid():
        #save the test instance
        test = test_form.save()

        #loop though each question and create it
        for j in range(1, number_of_questions + 1):
            create_question(test, week.week_number, j, data)

        #return the created test
        return test
    #case form was not validated successfully
    else:
        #raise an error
        raise ValidationError(test_form.errors)

#function to create a question and its linked answers for a given week
def create_question(test, week_number, question_number, data):
    #get the question text
    question_text = data.get(f"question_week_{week_number}_{question_number}")
    
    #initialize the question form with the extracted data
    question_form = QuestionForm(data = {
        "text": question_text,
        "test": test.id
    })
    
    #case form validated successfully
    if question_form.is_valid():
        #save the question instance
        question = question_form.save()

        answer_forms = []
        #loop to create up to 4 answers for the question
        for k in range(1, 5):
            #create an answer
            answer_form = create_answer(question, week_number, question_number, k, data)
            #case answer was created
            if answer_form:
                #add it to answer_forms for final validation
                answer_forms.append(answer_form)
        
        #perform a final validation for the answers once they have been created
        for answer_form in answer_forms:
            answer_form.final_validation()
        
        #return the created question  
        return question
    #case form was not validated successfully
    else:
        #raise an error
        raise ValidationError(question_form.errors)
    
#function to create an answer for a given question
def create_answer(question, week_number, question_number, answer_number, data):
    #get the answer text and is_correct
    answer_text = data.get(f"answer_week_{week_number}_{question_number}_{answer_number}")
    is_correct =  data.get(f"correct_week_{week_number}_{question_number}_{answer_number}") == "on"

    #initialize the answer form with the extracted data
    answer_form = AnswerForm(data = {
        "text": answer_text,
        "is_correct": is_correct,
        "question": question.id
    })

    #case form validated successfully
    if answer_form.is_valid():
        #save the answer instance
        answer_form.save()
    #case form was not validated successfully
    else:
        #raise an error
        raise ValidationError(answer_form.errors)
    
    return answer_form

#method to get the file format of a file
def get_file_format(resource_file):
    #get the file extension of the file
    _, file_extension = os.path.splitext(resource_file.name.lower())

    #return the resource type based on the file extension
    if file_extension in [".jpg", ".jpeg", ".svg", ".png"]:
        return "image"
    if file_extension in [".pdf"]:
        return "pdf"
    if file_extension in [".mp4", ".avi"]:
        return "video"
    else:
        raise ValidationError(f"Unsupported file format: {file_extension}")

#method to save an uploaded file to a temporary directory and return full path
def save_temp_file(resource_file):
    #get the path to the temp directory
    temp_dir = tempfile.gettempdir()
    #create a full path with the temp path and the file name
    temp_file_path = os.path.join(temp_dir, resource_file.name)

    #open the file in write binary mode
    with open(temp_file_path, 'wb+') as destination:
        #loop over each chunk of data and write it to the destination file
        for chunk in resource_file.chunks():
            destination.write(chunk)

    #return the full path to the temp file
    return temp_file_path

#method to create and save a Resource instance and call the methods to upload files to supabase storage and create a thumbnail
def process_resource(resource_file, resource_type, course=None, lesson=None, status_update=None, existing_resource=None):
    #case the resource will be updated
    if existing_resource:
        #delete existing file from supabase storage
        delete_from_supabase(existing_resource.file)

        #case the existing resource is an image with a thumbnail
        if existing_resource.resource_format == "image" and existing_resource.thumbnail:
            #delete the thumbnail from supabase storage
            delete_from_supabase(existing_resource.thumbnail)

        #update the resource details
        existing_resource.title = resource_file.name
        existing_resource.resource_format = get_file_format(resource_file)
        existing_resource.save()

        #get the temp file full path
        file_path = save_temp_file(resource_file)

        #case the file is an image
        if existing_resource.resource_format == "image":
            #create a thumbnail, upload both thumbnail and image by updating existing files in supabase storage
            #use on_commit to ensure Resource is available in the database
            transaction.on_commit(lambda: create_thumbnail_and_upload.delay(file_path, existing_resource.id))
        #case the resource is not an image - no thumbnail needed
        else:
            #upload file and update resource with URL
            #use on_commit to ensure Resource is available in the database
            transaction.on_commit(lambda: upload_file_to_supabase.delay(file_path, existing_resource.id))
        
        return existing_resource
    
    #case new resource
    #create a new resource - file/thumbnail fields will be updated once the tasks are completed
    resource = Resource.objects.create(
        lesson= lesson,
        course= course,
        status_update = status_update,
        title = resource_file.name,
        resource_format = get_file_format(resource_file),
        resource_type = resource_type
    )
    #save resource to the database
    resource.save()

    #get the temp file full path
    file_path = save_temp_file(resource_file)

    #case the file is an image
    if resource.resource_format == "image":
        #create a thumbnail, upload both thumbnail and image and update resource with URLs
        #use on_commit to ensure Resource is available in the database
        transaction.on_commit(lambda: create_thumbnail_and_upload.delay(file_path, resource.id))
    #case the resource is not an image - no thumbnail needed
    else:
        #upload file and update resource with URL
        #use on_commit to ensure Resource is available in the database
        transaction.on_commit(lambda: upload_file_to_supabase.delay(file_path, resource.id))
    
    #return the updated resource
    return resource

#method to send a notification to the students enrolled in a certain course when the teacher updates resources
def notify_enrolled_students_about_resources(course, message):
    #get the channel layer for the websocket
    channel_layer = get_channel_layer()
    #get all the students enrolled in the course
    enrolled_students = CustomUser.objects.filter(enrollments__course=course, is_student=True)

    #sent the notification to each enrolled student
    for student in enrolled_students:
        #create a unique group name
        group_name = f"{student.username}_notifications"
        #send the notification to the group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "message": message
            },
        )


        
        
