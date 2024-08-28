from courses.models import Course, Enrollment
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
            course = Course.objects.get(id=course_id)
            user = request.user

            # if not user.is_student and user != course.teacher:
            #     messages.error(request, "You do not have permission to access the chat")
            #     return redirect("course_details_view", course_id=course_id)

            enrollment = Enrollment.objects.filter(student=user, course=course).first()
            if not enrollment and user != course.teacher:
                messages.error(request, "You must enroll to access the chat")
                return redirect("courses:course_details_view", course_id=course_id)

            chat_messages = Message.objects.filter(course=course).order_by('timestamp')
            context = {
                'course': course,
                "messages": chat_messages,
            }

            return render(request, "chat/my_course_chat.html", context)
        
        except Course.DoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)
        except Enrollment.DoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} was not found."}, status=404)