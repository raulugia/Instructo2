from .models import Week, Test, Question, Answer, Resource, Lesson

from .forms import QuestionForm, AnswerForm, TestForm, WeekForm, LessonForm
from django.core.exceptions import ValidationError
import os
import tempfile
from .tasks import create_thumbnail_and_upload, upload_file_to_supabase
from .supabase_client import upload_to_supabase
from django.db import transaction

def create_week(course, week_number, data, files):
    # week = Week.objects.create(course=course, week_number=week_number)
    # create_resources(week, files.get(f"learning_material_week_{week_number}"))
    # create_task(week, data)
    # return week
    #print("course ID: ", course.id)
    week_form = WeekForm(data={
        "week_number": week_number,
        "course": course.id,
    })

    #print("week form before validation: ", week_form)
    #print("week form data before validation: ", week_form.data)
    #print("week form initial before validation: ", week_form.initial)
    if week_form.is_valid():
        #print("week form is VALID")
        week = week_form.save()
        #print("week: ", week)
        #number_of_lessons = int(data.get(f"number_of_lessons_week_{week_number}"))
        lesson_keys = [key for key in data.keys() if key.startswith(f"week_{week_number}_lesson_") and key.endswith("_title")]
        number_of_lessons = len(lesson_keys)
        print("number of lessons: ", number_of_lessons)
        for j in range(1, number_of_lessons + 1):
            lesson = create_lesson(week, week_number, j, data, files)
        #create_resources(week, files.get(f"learning_material_week_{week_number}"))
        create_test(week, data)
        return week
    else:
        #print("week form errors: ",week_form.errors.as_json())
        raise ValidationError(week_form.errors)


def create_lesson(week, week_number, lesson_number, data, files):
    print("creating lesson...")
    lesson_title = data.get(f"week_{week_number}_lesson_{lesson_number}_title")
    print("lesson title", lesson_title)
    lesson_description = data.get(f"week_{week_number}_lesson_{lesson_number}_description")

    lesson_form = LessonForm(data={
        "week": week,
        "title": lesson_title,
        "description": lesson_description,
        "lesson_number": lesson_number
    })

    if lesson_form.is_valid():
        print("lesson form is valid")
        lesson = lesson_form.save()

        learning_material = files.get(f"week_{week_number}_lesson_{lesson_number}_learning_material")
        if learning_material:
            print("there is learning material")
            process_resource(learning_material, "learning_material", lesson=lesson, week=week)
        
        return lesson
    else:
        #print("week form errors: ",week_form.errors.as_json())
        raise ValidationError(lesson_form.errors)

# def create_lesson(week, data, files):
#     number_of_lessons = data.get(f"number_of_lessons_week_{week.week_number}")
#     for i in range(1, int(number_of_lessons) + 1):
#         lesson = create_lesson(week, i, data, files)
#         create_tests(lesson, data)

#def create_lesson(week, lesson_number, data, files):
    # lesson_form = LessonForm(data={
    #     "title": data.get(f"title_lesson_{lesson_number}_week_{week.week_number}"),
    #     "description": data.get(f"description_lesson_{lesson_number}_week_{week.week_number}"),
    #     "week": week.id
    # })

    # if lesson_form.is_valid():
    #     lesson = lesson_form.save()
    #     create_resources(lesson, files.get(f"learning_material_lesson_{lesson_number}_week_{week.week_number}"))
    #     return lesson
    # else:
    #     raise ValidationError(lesson_form.errors)
    pass

def create_tests(lesson, data):
    # number_of_tests = data.get(f"number_of_tests_lesson_{lesson.id}")
    # for j in range(1, int(number_of_tests) + 1):
    #     test = create_test(lesson, j, data)
    #     create_questions(test, data)
    pass

#function to create a task and the questions and answers linked to it for a given week
def create_test(week, data):
    #get the keys linked to questions - needed due to dynamic form
    question_keys = [key for key in data.keys() if key.startswith(f"question_week_{week.week_number}_")]
    #determine the number of questions based on the length of question_keys
    number_of_questions = len(question_keys)

    #create a new task instance using the task form
    test_form = TestForm(data={
        "title": f"Task for Week {week.week_number}",
        "description": f"Task description for Week {week.week_number}",
        "deadline": data.get(f"deadline_week_{week.week_number}"),
        "week": week.id
    })

    #case form validated successfully
    if test_form.is_valid():
        #print("TASK FORM IS VALID")
        #save task
        test = test_form.save()
        #loop though each question and create it
        for j in range(1, number_of_questions + 1):
            create_question(test, week.week_number, j, data)

        return test
    #case form was not validated successfully
    else:
        #print("TASK ERRORS", task_form.errors)
        raise ValidationError(test_form.errors)

#function to create a question and its linked answers for a given week
def create_question(test, week_number, question_number, data):
    #get the question text
    question_text = data.get(f"question_week_{week_number}_{question_number}")
    #print("question text", question_text)
    #create a new question instance using the question form
    question_form = QuestionForm(data = {
        "text": question_text,
        "test": test.id
    })
    
    #case form validated successfully
    if question_form.is_valid():
        #print("QUESTION FORM IS VALID")
        #save the question
        question = question_form.save()

        answer_forms = []
        #loop to create up to 4 answers for the question
        for k in range(1, 5):
            answer_form = create_answer(question, week_number, question_number, k, data)
            if answer_form:
                answer_forms.append(answer_form)
        
        for answer_form in answer_forms:
            answer_form.final_validation()
        
        #return the question instance    
        return question
    #case form was not validated successfully
    else:
        print("QUESTION ERRORS", question_form.errors)
        raise ValidationError(question_form.errors)
    
#function to create an answer for a given question
def create_answer(question, week_number, question_number, answer_number, data):
    #get the answer text and is_correct
    answer_text = data.get(f"answer_week_{week_number}_{question_number}_{answer_number}")
    is_correct =  data.get(f"correct_week_{week_number}_{question_number}_{answer_number}") == "on"

    #print("answer text: ", answer_text)
    #print("is it correct?", is_correct)
    #print(data.get(f"correct_week_{week_number}_{question_number}_{answer_number}"))
    #create a new answer instance using the answer form
    answer_form = AnswerForm(data = {
        "text": answer_text,
        "is_correct": is_correct,
        "question": question.id
    })

    #case form validated successfully
    if answer_form.is_valid():
        #print("ANSWER FORM IS VALID")
        #save the answer
        answer_form.save()
    else:
        #print("ANSWER ERRORS", answer_form.errors)
        raise ValidationError(answer_form.errors)
    
    return answer_form

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

def process_resource(resource_file, resource_type, week=None, lesson=None):
    print("processing resource")
    #create a new resource - file/thumbnail fields will be updated once the tasks are completed
    resource = Resource.objects.create(
        week = week,
        lesson= lesson,
        title = resource_file.name,
        resource_format = get_file_format(resource_file),
        resource_type = resource_type
    )
    #save resource to the database
    resource.save()

    #get the temp file full path
    file_path = save_temp_file(resource_file)
    print("processing resource - path: ", file_path)

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

        
        
