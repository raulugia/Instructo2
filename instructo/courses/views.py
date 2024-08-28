from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from .forms import CourseForm, FeedbackForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .helpers import create_week, get_file_format, save_temp_file, process_resource, notify_enrolled_students_about_resources
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
from django.http import HttpResponseBadRequest, HttpResponseNotFound

#All the code in this file was written without assistance

#view to create a course
@login_required
def create_course_view(request):
    if request.method == "GET":
        #case the user is not a teacher
        if not request.user.is_teacher:
            #redirect user to the home page and display an error
            messages.error(request, "You must be a teacher to create a course.")
            return redirect("users:home_view")
        

        form = CourseForm()
        return render(request, "courses/create_course.html", {"form" : form})
    #case post method
    elif request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        
        #case form is valid
        if form.is_valid():
            try:
                #ensure that if there are errors no partial data is saved to the database - needed as other model instances linked to course will be saved in the helpers methods
                with transaction.atomic():
                    #save the course without committing
                    course = form.save(commit=False)
                    #set the course's teacher
                    course.teacher = request.user
                    #set the course's duration
                    course.duration_weeks = request.POST.get("duration_weeks")
 
                    #get the course cover picture
                    cover_picture = request.FILES.get("cover_picture")
                    #case the teacher submitted a cover picture
                    if cover_picture:
                        #create a new resource, create a thumbnail and upload both pics to supabase storage
                        cover_picture_resource = process_resource(cover_picture, "course_cover_picture")
                        #set the course's cover picture
                        course.cover_picture = cover_picture_resource
                    
                    #save the course
                    course.save()

                    #get the course additional resources
                    additional_resources = request.FILES.getlist("additional_resources")
                    #iterate over each resource
                    for resource_file in additional_resources:
                        #create a new resource, create a thumbnail and upload both pics to supabase storage
                        additional_resource = process_resource(resource_file, "additional_resource")
                        #set the course's additional resources
                        course.additional_resources.add(additional_resource)
                    
                    #save the course
                    course.save()

                    #get the course duration
                    num_weeks = int(request.POST.get("duration_weeks", 1))

                    #iterate over every week
                    for i in range(1, num_weeks + 1):
                        try:
                            #create week, lessons, tests, questions, answers and process resources
                            week = create_week(course, i, request.POST, request.FILES)

                        #add errors to the form if there is a validation error
                        except ValidationError as error:
                            error_message = " ".join(str(message) for message in error.messages)
                            form.add_error(None, f"Error in Week {i}: {error_message}")

                            #raise the error to trigger the rollback of the transaction
                            raise error
                        
                        
                #redirect the user to the home view once the course has been created
                return redirect("users:home_view")
            
            #case there were validation errors
            except ValidationError as error:
                #render the form with the errors
                return render(request, "courses/create_course.html", {"form": form})
        else:
            #case the form is not valid - re-render the course creation page
            return render(request, "courses/create_course.html", {"form": form})

#view to display the details of a course
@login_required    
def course_details_view(request, course_id):
    context ={}
    if request.method == "GET":
        try:
            #fetch the course
            course = Course.objects.get(id=course_id)
            #serialize the course to get and shape the data needed for the template
            serializer = DetailsCoursesSerializer(course)

            #construct the context
            context = {
                "course_data": serializer.data,
                "is_teacher": False,
                "is_course_teacher": False,
                "is_student": False,
                "is_enrolled": False,
                "student_completed_course": False
            }

            #case user is a teacher
            if request.user.is_teacher:
                #update context
                context["is_teacher"] = True
                #case teacher is the owner of the course
                if course.teacher == request.user:
                    #update context
                    context["is_course_teacher"] = True
            
            #case user is a student
            if request.user.is_student:
                #update context
                context["is_student"] = True
                #fetch enrollment to find out if user is enrolled in the course
                enrollment = Enrollment.objects.filter(student=request.user, course=course).first()

                #case student is enrolled
                if enrollment:
                    #update context
                    context["is_enrolled"] = True
                    context["has_completed_course"] = enrollment.has_completed_course()
            
            #render template with context
            return render(request, "courses/course_details.html", context)

        #case course does not exist
        except Course.DoesNotExist:
            messages.error(request, "The course does not exist.")
            return redirect("users:home_view")
    

    #case request method is not GET or POST - return bad request
    return HttpResponseBadRequest("Bad Request")

#view used by students to enroll in a course
@login_required
def enroll_course_view(request, course_id):
    if request.method == "POST":
        try:
            #fetch the course
            course = Course.objects.get(id=course_id)
            user = request.user

            #case user is a student
            if user.is_student:
                #get or create an enrollment for the student
                enrollment, created = Enrollment.objects.get_or_create(student=user, course=course)

                #case the student was not enrolled
                if created:
                    #add success message
                    messages.success(request, "You have successfully enrolled in the course.")
                    
                    #get the default channel layer for sending notifications
                    channel_layer = get_channel_layer()
                    
                    #send the notification to the teacher
                    async_to_sync(channel_layer.group_send)(
                        f"{course.teacher.username}_notifications",
                        {
                            "type": "send_notification",
                            "message": f"Student @{user.username} has enrolled in '{course.title}'."
                        }
                    )

                    #redirect the user to the course page where they can access the materials
                    return redirect("my_course_details_view", course_id=course_id)
                
                #case student was already enrolled
                else:
                    messages.error(request, "Your are already enrolled in this course.")
                    return redirect("course_details_view", course_id=course_id)
            
            #case user is a teacher - teachers cannot enroll in courses
            else:
                messages.error(request, "Only students can enroll in courses.")
                return redirect("course_details_view", course_id=course_id)
        #case course does not exist
        except Course.DoesNotExist:
            messages.error(request, "The course does not exist.")
            return redirect("users:home_view")

#view to display the students enrolled in a course and remove them if needed
@login_required
def manage_students_view(request, course_id):
    context={}
    #fetch the course
    course = Course.objects.get(id=course_id)

    #case course's teacher is not the current user
    if course.teacher != request.user:
        #add an error and redirect
        messages.error(request, "You must be the owner of the course to remove students")
        return redirect("course_details_view", course_id=course.id)
    
    #case get method
    if request.method == "GET":
        #fetch the enrolled students
        enrollments = Enrollment.objects.filter(course=course)

        #construct the context
        context = {
            "course": course,
            "enrollments": enrollments
        }

        #render the template with the context
        return render(request, "courses/manage_students.html", context)
    
    #post case - teacher wants to remove students
    elif request.method == "POST":
        #get the selected students
        selected_students = request.POST.getlist("selected_students")

        #case no selected students - add an error
        if not selected_students:
            messages.error(request, "No students were selected")
        #case there are selected students
        else:
            #iterate over the selected students
            for student_id in selected_students:
                #fetch the student
                student = CustomUser.objects.get(id=student_id)
                #fetch the enrollment
                enrollment = Enrollment.objects.filter(course=course, student=student)

                #case the student is enrolled
                if enrollment:
                    #delete enrollment
                    enrollment.delete()
                    #add a success message
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

        #redirect teacher
        return redirect("manage_students_view", course_id=course_id)

#view to update the resources related to a certain course
@login_required
def manage_resources_view(request, course_id):
    try:
        #case user is a teacher
        if request.user.is_teacher:
            #get the course created by the user
            course = Course.objects.get(id=course_id, teacher=request.user)
    #redirect the user if the course does not exist       
    except Course.DoesNotExist:
        messages.error(request, "Course does not exist.")
        return redirect("course_details_view", course_id=course_id)
    
    #case GET
    if request.method == "GET":
        #get all the weeks related to the course and prefetch the lessons and their resources
        weeks = Week.objects.filter(course=course).prefetch_related("lessons__lesson_resources")
        #get all additional resources related to the course
        additional_resources = Resource.objects.filter(course=course, resource_type="additional_resource")

        #construct the context with the fetched data
        context = {
            "course": course,
            "weeks": weeks,
            "additional_resources": additional_resources,
        }

        #render template with context - this template will allow teachers to manage the course resources
        return render(request, "courses/manage_resources.html", context)
    
    #case POST
    elif request.method == "POST":
        #case the user is a teacher
        if request.user.is_teacher:
            #get new cover picture submitted by the teacher
            new_course_cover_picture = request.FILES.get("course_cover_picture")
            
            #case there is a new cover picture
            if new_course_cover_picture:
                #case there is an existing cover picture
                if course.cover_picture:
                    #delete existing cover picture from supabase storage, upload the new one with its thumbnail and update the resource in the database
                    cover_picture_resource = process_resource(new_course_cover_picture, "course_cover_picture", course=course, existing_resource=course.cover_picture)
                #case there is no existing cover picture
                else:
                    #upload the new one with its thumbnail and save the new resource in the database
                    cover_picture_resource = process_resource(new_course_cover_picture, "course_cover_picture", course=course)
                
                #update the course's cover picture
                course.cover_picture = cover_picture_resource
                #save updated course
                course.save()

                #notify enrolled students that the cover picture has been updated
                notify_enrolled_students_about_resources(course, f"The cover picture of '{course.title}' has been updated.")
            
            #handle additional resources updates
            #loop over the additional resources in the course
            for resource in Resource.objects.filter(course=course, resource_type="additional_resource"):
                #get the new additional resource submitted by the teacher
                updated_resource = request.FILES.get(f"update_additional_resource_{resource.id}")

                #case the teacher submitted a new additional resource to update an existing one
                if updated_resource:
                    #delete existing additional resource from supabase storage, upload the new one and update the resource in the database
                    process_resource(updated_resource, "additional_resource", course=course, existing_resource=resource)
                    #notify enrolled students that the resource was updated
                    notify_enrolled_students_about_resources(course, f"An additional resource of the course '{course.title}' has been updated.")
            
            #handle new additional resources
            #get the new additional resources submitted by the teacher
            new_additional_resources = request.FILES.getlist("additional_resources")
            #loop over each new additional resource
            for new_resource_file in new_additional_resources:
                #upload the new additional resource to supabase storage and save the new resource in the database
                process_resource(new_resource_file, "additional_resource", course=course)
                #notify enrolled students about the new additional resource
                notify_enrolled_students_about_resources(course, f"An additional resource has been added to your course '{course.title}'.")
            
            #handle new learning materials
            #loop over the weeks in the course
            for week in Week.objects.filter(course=course):
                #loop over the lessons in every week
                for lesson in week.lessons.all():
                    #get the new learning material submitted by the teacher
                    updated_material = request.FILES.get(f"week_{week.week_number}_lesson_{lesson.lesson_number}_learning_material")
                    #case the teacher uploaded a new learning material to update the existing one
                    if updated_material:
                        #get the existing learning material
                        existing_learning_material = lesson.lesson_resources.first()
                        #case there is an existing learning material
                        if existing_learning_material:
                            #delete the existing learning material from supabase storage, upload the new one and update the resource in the database
                            process_resource(updated_material, "learning_material", lesson=lesson, existing_resource=existing_learning_material)
                            #notify the enrolled students that a learning material has been updated
                            notify_enrolled_students_about_resources(course, f"A learning material in lesson {lesson.lesson_number}-Week {week.week_number} in the course '{course.title}' has been updated.")
                        #case there is no existing learning material
                        else:
                            #upload the new learning material to supabase and update the resource in the database
                            process_resource(updated_material, "learning_material", lesson=lesson)
                            #notify the enrolled students that a new learning material has been added
                            notify_enrolled_students_about_resources(course, f"A new learning material in lesson {lesson.lesson_number}-Week {week.week_number} in the course '{course.title}' has been added.")
            
            #display a success message after the resources have been changed
            messages.success(request, "Resources updates successfully")
            #redirect the user back to the manage resources page
            return redirect("manage_resources_view", course_id=course_id)


#view to display the course details and materials - student must be enrolled
@login_required
def my_course_details_view(request, course_id, week_number=None):
    context = {}
    #clear stored messages
    list(messages.get_messages(request))

    #case no week number provided - redirect user to the first week
    if week_number is None:
        return redirect("my_course_details_view", course_id=course_id, week_number=1)

    #case get
    if request.method == "GET":
        try:
            #fetch course
            course = Course.objects.get(id=course_id)
            user = request.user

            #case user is a student
            if user.is_student:
                try:
                    #get enrollment
                    enrollment = Enrollment.objects.get(student=user, course=course)

                    #case the student is enrolled
                    if enrollment:
                        #get the week along with its related tests, questions and answers
                        week = Week.objects.prefetch_related("tests__questions__answers").get(course=course, week_number = week_number)
                        #serialize the fetched data
                        serializer = WeekSerializer(week, context={"student": user})

                        #construct the context
                        context ={
                            "course": course,
                            "enrollment": enrollment,
                            "course_data": serializer.data,
                            "week_number": week_number,
                        }

                        #render the template with the context
                        return render(request, "courses/my_course_details.html", context)
                
                #case user is not enrolled
                except Enrollment.DoesNotExist:
                    messages.error(request, "You must be enrolled in the course to access its content.")
                    return redirect("course_details_view", course_id=course.id)

                #case week does not exist        
                except Week.DoesNotExist:
                    messages.error(request, "The selected week does not exist")
                    return redirect("my_course_details", course_id=course.id, week_number=week_number)

        #case course does not exist
        except Course.DoesNotExist:
            messages.error(request, "The selected course does not exist")
            return redirect("users:home_view")        
        
#view to see the additional resources in a course
@login_required
def additional_resources_view(request, course_id):
    context={}
    if request.method == "GET":
        try:
            #fetch the course
            course = Course.objects.get(id=course_id)
            #serialize the course to get the right data
            serializer = CourseResourcesSerializer(course)
            
            #construct the context
            context={
                "course_data": serializer.data
            }

            #render the template with the context
            return render(request, "courses/additional_resources.html", context) 
        
        #case course does not exist
        except Course.DoesNotExist:
            messages.error(request, "The selected course does not exist")
            return redirect("users:home_view")

#view to create/update feedback        
@login_required
def leave_feedback_view(request, course_id):    
    try:
        #fetch the course
        course = Course.objects.get(id=course_id)
        user = request.user
        
        #case user is not a student
        if not user.is_student:
            messages.error(request, "Only students can leave feedback.")
            return redirect("course_details_view")

        #case the user is a student
        if user.is_student:
            #fetch the enrollment
            enrollment = Enrollment.objects.get(student=user, course=course)

            #case student is not enrolled
            if not enrollment:
                messages.error(request, "You must enroll the course to leave feedback.")
                return redirect("course_details_view")
            
            try:
                #try to fetch existing feedback by current user
                feedback = Feedback.objects.get(student=user, course=course)
                #update flag
                existing_feedback = True
            
            #case there is no existing feedback
            except Feedback.DoesNotExist:
                #set feedback to none
                feedback = None
                #update flag
                existing_feedback = False

            #case get
            if request.method == "GET":
                ##only add the info message if there are no success messages
                if existing_feedback and not any(message.level == messages.SUCCESS for message in messages.get_messages(request)):
                    messages.info(request, "You have already reviewed this course.")

                #prepare form
                form = FeedbackForm()

                #construct context
                context = {
                    "course": course,
                    "form": form,
                    "existing_feedback": existing_feedback,
                    "feedback": feedback,
                }

                #render template with context
                return render(request, "courses/leave_feedback.html", context)
            
            #case post
            elif request.method == "POST":
                stored_messages = messages.get_messages(request)
                stored_messages.used = True

                form = FeedbackForm(request.POST)

                context = {
                    "course": course,
                    "form": form
                }

                if form.is_valid():
                    #case there is existing feedback
                    if existing_feedback:
                        #update existing feedback
                        feedback.feedback = form.cleaned_data["feedback"]
                        #save the new feedback and add a message
                        feedback.save()
                        messages.success(request, "Your feedback was updated successfully")
                    #case no pre-existing feedback    
                    else:
                        #save the new feedback without committing
                        feedback = form.save(commit=False)
                        #set feedback's student and course
                        feedback.student = user
                        feedback.course = course

                        #save feedback and add a success message
                        feedback.save()
                        messages.success(request, "Your feedback has been submitted successfully")
                    
                    #redirect student to the same page 
                    return redirect("leave_feedback_view", course_id=course.id)
                
                #case form was not valid
                else:
                    return render(request, "courses/leave_feedback.html", context)
    #case course does not exist
    except Course.DoesNotExist:
        messages.error(request, "The selected course does not exist")
        return redirect("users:home_view")

    

#view to submit a test or see the previous result
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
