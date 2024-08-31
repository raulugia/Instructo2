from django.test import TestCase
from django.urls import reverse
from .factories import CourseFactory, EnrollmentFactory, FeedbackFactory
from users.factories import CustomUserFactory
from .models import Enrollment, Feedback


#All the code in this file was written without assistance

class CourseDetailsViewTest(TestCase):

    #method to create a teacher, student and course needed for the tests - test attributes
    def setUp(self):
        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create a student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)
        #create a course
        self.course = CourseFactory(teacher=self.teacher)
    
    #test method to ensure the right template is rendered - teacher case
    def test_course_details_teacher(self):
        #log in as the teacher
        self.client.force_login(self.teacher)

        #send a GET request to the course details view
        response = self.client.get(reverse("course_details_view", args=[self.course.id]))

        #assert that the response is 200
        self.assertEqual(response.status_code, 200)

        #assert that the correct template is rendered
        self.assertTemplateUsed(response, "courses/course_details.html")

        #assert that the template identifies the user as the teacher of the course
        self.assertTrue(response.context["is_teacher"])
        self.assertTrue(response.context["is_course_teacher"])
    
    #test method to ensure the right template is rendered for a enrolled student
    def test_course_details_student(self):
        #log in as the student
        self.client.force_login(self.student)

        #enroll the the student in the course
        EnrollmentFactory(student=self.student, course=self.course)

        #send a GET request to the course details view
        response = self.client.get(reverse("course_details_view", args=[self.course.id]))

        #assert that the response is 200
        self.assertEqual(response.status_code, 200)

        #assert that the correct template is rendered
        self.assertTemplateUsed(response, "courses/course_details.html")

        #assert that the template identifies the user as student
        self.assertTrue(response.context["is_student"])
        #assert that the template identifies the user as enrolled
        self.assertTrue(response.context["is_enrolled"])

    #test method to ensure the view handles case where course does not exist
    def test_course_details_view_not_found(self):
        #log in as the student
        self.client.force_login(self.student)

        #send a GET request to the course details view with a non-existent course id
        response = self.client.get(reverse("course_details_view", args=[854]))

        #assert that the response status is 302 redirect
        self.assertEqual(response.status_code, 302)

        #assert that the redirect is correct
        self.assertRedirects(response, reverse("users:home_view"))
    

    
class EnrollCourseViewTest(TestCase):

    #method to create a teacher, student and course needed for the tests - test attributes
    def setUp(self):
        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create a student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)
        #create a course
        self.course = CourseFactory(teacher=self.teacher)
    
    #test method to verify a student can enroll a course
    def test_successfully_enrollment(self):
        #log in as the student
        self.client.force_login(self.student)

        #send a POST request to the enroll course view
        self.client.post(reverse("enroll_course_view", args=[self.course.id]))

        #assert that the enrollment was created successfully
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

class ManageStudentsViewTest(TestCase):

    #method to create a teacher, students and course and enroll students - test attributes
    def setUp(self):
        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create students
        self.student1 = CustomUserFactory(is_teacher=False, is_student=True)
        self.student2 = CustomUserFactory(is_teacher=False, is_student=True)
        
        #create a course
        self.course = CourseFactory(teacher=self.teacher)
        #enroll students
        EnrollmentFactory(course=self.course, student=self.student1)
        EnrollmentFactory(course=self.course, student=self.student2)
    
    #test method to ensure teachers can remove students from their courses
    def test_remove_students(self):
        #log in as the teacher
        self.client.force_login(self.teacher)

        #send a POST request to remove a student
        post_data = {"selected_students": [self.student1.id]}
        self.client.post(reverse("manage_students_view", args=[self.course.id]), post_data)

        #assert that the student has been removed
        self.assertFalse(Enrollment.objects.filter(course=self.course, student=self.student1).exists())

        #assert that the other student remains enrolled
        self.assertTrue(Enrollment.objects.filter(course=self.course, student=self.student2).exists())


class LeaveFeedbackViewTest(TestCase):
    #method to create a teacher, student and course and enroll student needed for the tests - test attributes
    def setUp(self):
        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create a student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)
       
        #create a course
        self.course = CourseFactory(teacher=self.teacher)
        #enroll students
        EnrollmentFactory(course=self.course, student=self.student)
        

    #test method to ensure enrolled students can leave feedback
    def test_student_can_leave_feedback(self):
        #log in as the student
        self.client.force_login(self.student)

        #submit new feedback
        feedback_content = "Test feedback long enough: Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem a"
        post_data = {"feedback": feedback_content}
        self.client.post(reverse("leave_feedback_view", args=[self.course.id]), post_data)

        #assert that the feedback was saved successfully
        self.assertTrue(Feedback.objects.filter(student=self.student, course=self.course, feedback=feedback_content).exists())
    

    #test method to ensure students can update their feedback
    def test_student_can_update_feedback(self):
        #create feedback
        old_feedback_content = "Old test feedback long enough: Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem a"
        FeedbackFactory(course=self.course, student=self.student, feedback= old_feedback_content)

        #log in as the student
        self.client.force_login(self.student)

        #submit new feedback
        new_feedback_content = "New test feedback long enough: Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem a"
        post_data = {"feedback": new_feedback_content}
        self.client.post(reverse("leave_feedback_view", args=[self.course.id]), post_data)

        #assert that the feedback was updated successfully
        self.assertTrue(Feedback.objects.filter(student=self.student, course=self.course, feedback= new_feedback_content).exists())
