from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from .forms import CourseForm, FeedbackForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .helpers import create_week, get_file_format, save_temp_file, process_resource
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Course, Enrollment, Week, Test, Lesson, UserAnswer, Answer, Resource, Feedback
from .serializers import CourseResourcesSerializer, WeekSerializer, DetailsCoursesSerializer
from chat.models import Message
import os
from users.models import CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@login_required
def create_course_view(request):
    if request.method == "GET":
        print(request.user)
        if not request.user.is_teacher:
            messages.error(request, "You must be a teacher to create a course.")
            return redirect("users:home_view")
        form = CourseForm()
        return render(request, "courses/create_course.html", {"form" : form})
    
    elif request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        print(request.POST)
        print(request.user)
        print("FILES: ",request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save(commit=False)
                    course.teacher = request.user
                    course.duration_weeks = request.POST.get("duration_weeks")
                    # course.save() 
                    print("course: ", course)
                    print("----FORM cleaned data: ", form.cleaned_data)

                    cover_picture = request.FILES.get("cover_picture")
                    if cover_picture:
                        print("there is a cover pic: ", cover_picture)
                        cover_picture_resource = process_resource(cover_picture, "course_cover_picture")
                        course.cover_picture = cover_picture_resource
                    
                    course.save()


                    additional_resources = request.FILES.getlist("additional_resources")
                    for resource_file in additional_resources:
                        additional_resource = process_resource(resource_file, "additional_resource")
                        course.additional_resources.add(additional_resource)
                    
                    course.save()


                    num_weeks = int(request.POST.get("duration_weeks", 1))

                    for i in range(1, num_weeks + 1):
                        #print("num of weeks", num_weeks)
                        try:
                            #print("trying to create week")
                            week = create_week(course, i, request.POST, request.FILES)
                            #print("created week: ", week)

                            #learning_material = request.FILES.get(f"learning_material_week{i}")
                            #print("LEARNING MATERIAL: ", learning_material)
                            # if learning_material:
                            #     process_resource(learning_material, "learning_material", week=week)

                        except ValidationError as error:
                            error_message = " ".join(str(message) for message in error.messages)
                            form.add_error(None, f"Error in Week {i}: {error_message}")
                            # for field, messages in error.message_dict.items():
                            #     for message in messages:
                            #         form.add_error(None ,f"Week {i} - {field.capitalize()}: {message}")
                            raise error
                        
                        
                print("completed")
                return redirect("users:home_view")
            except ValidationError as error:
                #form.add_error(None, error)
                return render(request, "courses/create_course.html", {"form": form})
        else:
            # errors = {field: errors.get_json_data() for field, errors in form.errors.items()}
            # print("form errors: ", errors)
            # return JsonResponse({"errors": errors}, status=400)
            return render(request, "courses/create_course.html", {"form": form})

@login_required    
def course_details_view(request, course_id):
    context ={}
    if request.method == "GET":
        print("here")
        try:
            course = Course.objects.get(id=course_id)
            serializer = DetailsCoursesSerializer(course)

            print(serializer.data)

            context = {
                "course_data": serializer.data,
                "is_teacher": False,
                "is_course_teacher": False,
                "is_student": False,
                "is_enrolled": False,
                "student_completed_course": False
            }

            if request.user.is_teacher:
                context["is_teacher"] = True
                if course.teacher == request.user:
                    context["is_course_teacher"] = True
            
            if request.user.is_student:
                context["is_student"] = True

                enrollment = Enrollment.objects.filter(student=request.user, course=course).first()

                if enrollment:
                    context["is_enrolled"] = True
                    context["has_completed_course"] = enrollment.has_completed_course()
            
            return render(request, "courses/course_details.html", context)

        except Course.DoesNotExist:
            return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)
    

    #case request method is not GET or POST - return bad request
    return JsonResponse({"error": "Bad Request"}, status=400)

@login_required
def enroll_course_view(request, course_id):
    if request.method == "POST":
        try:
            course = Course.objects.get(id=course_id)
            user = request.user

            if user.is_student:
                enrollment, created = Enrollment.objects.get_or_create(student=user, course=course)

                if created:
                    messages.success(request, "You have successfully enrolled in the course.")
                    
                    #get the default channel layer
                    channel_layer = get_channel_layer()
                    #send the notification
                    async_to_sync(channel_layer.group_send)(
                        f"{course.teacher.username}_notifications",
                        {
                            "type": "send_notification",
                            "message": f"Student @{user.username} has enrolled in '{course.title}'."
                        }
                    )

                    return redirect("my_course_details_view", course_id=course_id)
                else:
                    messages.error(request, "Your are already enrolled in this course.")
                    return redirect("course_details_view", course_id=course_id)
            else:
                messages.error(request, "Only students can enroll in courses.")
                return redirect("course_details_view", course_id=course_id)
        
        except Course.DoesNotExist:
            return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)

@login_required
def manage_students_view(request, course_id):
    context={}
    course = Course.objects.get(id=course_id)

    if course.teacher != request.user:
        messages.error(request, "You must be the owner of the course to remove students")
        return redirect("course_details_view", course_id=course.id)
    
    if request.method == "GET":
        enrollments = Enrollment.objects.filter(course=course)
        context = {
            "course": course,
            "enrollments": enrollments
        }
        return render(request, "courses/manage_students.html", context)
    
    elif request.method == "POST":
        print("HERE")
        selected_students = request.POST.getlist("selected_students")

        if not selected_students:
            messages.error(request, "No students were selected")
        else:
            for student_id in selected_students:
                student = CustomUser.objects.get(id=student_id)
                enrollment = Enrollment.objects.filter(course=course, student=student)
                if enrollment:
                    enrollment.delete()
                    messages.success(request, "Student(s) removed from the course successfully")

                    #notify the student using websocket
                    #get the default channel layer
                    channel_layer = get_channel_layer()
                    #send the notification
                    async_to_sync(channel_layer.group_send)(
                        f"{student.username}_notifications",
                        {
                            "type": "send_notification",
                            "message": f"You have been removed from '{course.title}'."
                        }
                    )

        return redirect("manage_students_view", course_id=course_id)

@login_required
def my_course_details_view(request, course_id, week_number=None):
    context = {}
    #clear stored messages
    list(messages.get_messages(request))
    if week_number is None:
        return redirect("my_course_details_view", course_id=course_id, week_number=1)

    if request.method == "GET":
        try:
            course = Course.objects.get(id=course_id)
            user = request.user

            if user.is_student:
                try:
                    enrollment = Enrollment.objects.get(student=user, course=course)

                    if enrollment:
                        #use prefetch_related to improve performance
                        week = Week.objects.prefetch_related("tests__questions__answers").get(course=course, week_number = week_number)
                        #serializer = CourseSerializer(course)
                        serializer = WeekSerializer(week, context={"student": user})

                        print(serializer.data)

                        context ={
                            "course": course,
                            "enrollment": enrollment,
                            "course_data": serializer.data,
                            "week_number": week_number,
                        }

                        return render(request, "courses/my_course_details.html", context)
                except Enrollment.DoesNotExist:
                    messages.error(request, "You must be enrolled in the course to access its content.")
                    return redirect("course_details_view", course_id=course.id)        
                except Week.DoesNotExist:
                    messages.error(request, "The selected week does not exist")
                    return redirect("my_course_details", course_id=course.id, week_number=week_number)

        except Course.DoesNotExist:
            messages.error(request, "The selected course does not exist")
            return redirect("users:home_view")        
        

@login_required
def additional_resources_view(request, course_id):
    context={}
    if request.method == "GET":
        try:
            course = Course.objects.get(id=course_id)
            print(course.additional_resources.all())
            serializer = CourseResourcesSerializer(course)
            print(serializer.data)
            context={
                "course_data": serializer.data
            }

            return render(request, "courses/additional_resources.html", context) 
        
        except Course.DoesNotExist:
            return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)
        
@login_required
def leave_feedback_view(request, course_id):    
    try:
        course = Course.objects.get(id=course_id)
        user = request.user

        if not user.is_student:
            messages.error(request, "Only students can leave feedback.")
            return redirect("course_details_view")

        if user.is_student:
            enrollment = Enrollment.objects.get(student=user, course=course)

            if not enrollment:
                messages.error(request, "You must enroll the course to leave feedback.")
                return redirect("course_details_view")
            
            try:
                feedback = Feedback.objects.get(student=user, course=course)
                existing_feedback = True
            except Feedback.DoesNotExist:
                feedback = None
                existing_feedback = False

            if request.method == "GET":
                ##only add the info message if there are no success messages
                if existing_feedback and not any(message.level == messages.SUCCESS for message in messages.get_messages(request)):
                    messages.info(request, "You have already reviewed this course.")

                form = FeedbackForm()

                context = {
                    "course": course,
                    "form": form,
                    "existing_feedback": existing_feedback,
                    "feedback": feedback,
                }

                return render(request, "courses/leave_feedback.html", context)
            
            elif request.method == "POST":
                stored_messages = messages.get_messages(request)
                stored_messages.used = True

                form = FeedbackForm(request.POST)

                context = {
                    "course": course,
                    "form": form
                }

                if form.is_valid():
                    print("form is valid")
                    if existing_feedback:
                        feedback.feedback = form.cleaned_data["feedback"]
                        feedback.save()
                        messages.success(request, "Your feedback was updated successfully")
                    else:
                        feedback = form.save(commit=False)
                        feedback.student = user
                        feedback.course = course
                        feedback.save()
                        messages.success(request, "Your feedback has been submitted successfully")
                    
                    return redirect("leave_feedback_view", course_id=course.id)
                else:
                    return render(request, "courses/leave_feedback.html", context)
    
    except Course.DoesNotExist:
        return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)

    


@login_required
def test_form_view(request, course_id, week_number, test_id):
    #initialize the context dictionary
    context={}
    #get task and user
    test = Test.objects.get(id=test_id, week__course_id=course_id, week__week_number=week_number)
    user = request.user

    #case method is get - test form is rendered so user can submitted
    if request.method == "GET":
        #get mode - complete means this is the 1st attempt
        mode = request.GET.get("mode", "complete")
        #dictionary to store the user's answers
        user_answers = {}

        #case mode is feedback - test form is rendered with pre-existing answers and grade
        if mode == "feedback":
            #get previous answers
            user_answers = {
                user_answer.question_id: user_answer.selected_answer_id for user_answer in UserAnswer.objects.filter(student=user, test=test)
            }

        #prepare the context that will be sent to the template
        context ={
                "test": test,
                "questions": test.questions.all(),
                "week_number": week_number,
                "user_answers": user_answers,
                "grade": test.grade,
                "mode": mode,
            }
        
        #render the form with the context
        return render(request, "courses/test_form.html", context)
    
    #case post - user is submitting the test
    elif request.method == "POST":
        #get the pre-existing answers if there are any
        old_user_answers = list(UserAnswer.objects.filter(student=user, test=test))
        #variable to store the new user answers temporarily
        temp_user_answers = []

        #loop over the questions linked to the task
        for question in test.questions.all():
            #get answer ids
            selected_answer_ids = request.POST.getlist(f"question_{question.id}")
            
            #loop over the selected answers ids
            for answer_id in selected_answer_ids:
                #get the answer object by id
                answer = Answer.objects.get(id=answer_id)
                #append a new UserAnswer to the temporary list
                temp_user_answers.append(UserAnswer(student=user, question=question, selected_answer=answer,test=test))
        
        #save the new answers temporarily
        UserAnswer.objects.bulk_create(temp_user_answers)
            
        #calculate the new grade
        new_grade = test.calculate_grade(user)

        #case there is a new grade and it is higher than the pre-existing one or there is no pre-existing grade
        if new_grade is not None and (test.grade is None or new_grade > test.grade):
            #remove old answers
            UserAnswer.objects.filter(student=user, test=test).exclude(id__in=[user_answer.id for user_answer in temp_user_answers]).delete()
            
            #save the new grade
            test.grade = new_grade
            test.save()
        #case there this is the first attempt or new grade is lower than the pre-existing one    
        else:
            #discard the new user answers
            UserAnswer.objects.filter(student=user, test=test).delete()
            #restore old answers - only the answers linked to the highest grade are kept
            UserAnswer.objects.bulk_create(old_user_answers)

        #get the answers selected by user
        user_answers = {
                user_answer.question_id: user_answer.selected_answer_id for user_answer in UserAnswer.objects.filter(student=user, test=test)
            }

        #create the context that will be sent to the client
        context ={
            "test": test,
            "questions": test.questions.all(),
            "week_number": week_number,
            "user_answers": user_answers,
            "grade": new_grade if new_grade is not None else test.grade,
            "mode": "feedback",
            }

        #render the form with feedback
        return render(request, "courses/test_form.html", context)


# Create your views here.
@login_required
def group_chat_view(request, course_id):
    if request.method == "GET":
        try:
            course = Course.objects.get(id=course_id)
            user = request.user

            # if not user.is_student and user != course.teacher:
            #     messages.error(request, "You do not have permission to access the chat")
            #     return redirect("course_details_view", course_id=course_id)

            enrollment = Enrollment.objects.filter(student=user, course=course).first()
            if not enrollment and user != course.teacher:
                messages.error(request, "You must enroll to access the chat")
                return redirect("course_details_view", course_id=course_id)

            chat_messages = Message.objects.filter(course=course).order_by('timestamp')
            context = {
                'course': course,
                "messages": chat_messages,
            }

            return render(request, "courses/my_course_chat.html", context)
        
        except Course.DoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)
        except Enrollment.DoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)