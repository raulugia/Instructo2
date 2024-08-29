from courses.models import Course, Enrollment, Week
from .models import Message
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

#view to get the messages linked to the course - chat history
@login_required
def group_chat_view(request, course_id):
    if request.method == "GET":
        try:
            #fetch the course
            course = Course.objects.get(id=course_id)
            user = request.user

            # if not user.is_student and user != course.teacher:
            #     messages.error(request, "You do not have permission to access the chat")
            #     return redirect("course_details_view", course_id=course_id)

            #fetch the enrollment between user and course
            enrollment = Enrollment.objects.filter(student=user, course=course).first()
            #case student is not enrolled - redirect
            if not enrollment and user != course.teacher:
                messages.error(request, "You must enroll to access the chat")
                return redirect("courses:course_details_view", course_id=course_id)

            #fetch the course chat messages ordered by timestamp
            chat_messages = Message.objects.filter(course=course).order_by('timestamp')

            #fetch the course weeks so construct urls in the template to a particular week
            course_weeks = Week.objects.filter(course=course).order_by('week_number')

            context = {
                'course': course,
                "messages": chat_messages,
                "course_weeks": course_weeks
            }

            return render(request, "chat/my_course_chat.html", context)
        
        except Course.DoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)
        except Enrollment.DoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)