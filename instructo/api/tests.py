from django.test import TestCase
from users.factories import CustomUserFactory
from courses.factories import CourseFactory, EnrollmentFactory, ResourceFactory, WeekFactory, LessonFactory, TestFactory
from rest_framework.test import APIClient
from django.urls import reverse
from courses.models import Course
import json

#All the code in this file was written without assistance

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        #create a teachers
        self.teacher1 = CustomUserFactory(is_teacher=True, is_student=False)
        self.teacher2 = CustomUserFactory(is_teacher=True, is_student=False)
        #create a student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)

        #create cover pictures
        self.cover_picture1 = ResourceFactory(file="https://example.com/path/to/cover_pic.jpeg", thumbnail="https://example.com/path/to/thumbnail_cover_pic.jpeg", resource_format="image", resource_type="user_profile_picture")
        self.cover_picture2 = ResourceFactory(file="https://example.com/path/to/cover_pic.jpeg", thumbnail="https://example.com/path/to/thumbnail_cover_pic.jpeg", resource_format="image", resource_type="user_profile_picture")

        #create courses
        self.course1 = CourseFactory(teacher=self.teacher1, cover_picture=self.cover_picture1, duration_weeks=1)
        self.course2 = CourseFactory(teacher=self.teacher2, cover_picture=self.cover_picture2, duration_weeks=1)

        #create week, lesson and test for course1
        self.week1 = WeekFactory(course=self.course1, week_number=1)
        self.lesson1 = LessonFactory(week=self.week1, lesson_number=1)
        self.test1 = TestFactory(week=self.week1)

        #enroll student
        EnrollmentFactory(course=self.course1, student=self.student)
        EnrollmentFactory(course=self.course2, student=self.student)
    

    #test method to ensure get_own_user_details_view returns student's details
    def test_student_get_own_user_details_view(self):
        #log in student
        self.client.force_login(self.student)

        #send a GET request to the view
        response = self.client.get(reverse("get_own_user_details_view"))
        
        #assert that the response code is 200
        self.assertEqual(response.status_code, 200)

        #assert that the returned data matches the user's data
        self.assertEqual(response.data["username"], self.student.username)
        self.assertEqual(response.data["first_name"], self.student.first_name)
        self.assertEqual(response.data["last_name"], self.student.last_name)
        self.assertEqual(response.data["email"], self.student.email)
        self.assertTrue(response.data["is_student"])
        self.assertFalse(response.data["is_teacher"])
    
    #test method to ensure get_own_user_details_view returns student's details
    def test_teacher_get_own_user_details_view(self):
        #log in teacher1
        self.client.force_login(self.teacher1)

        #send a GET request to the view
        response = self.client.get(reverse("get_own_user_details_view"))
        
        #assert that the response code is 200
        self.assertEqual(response.status_code, 200)

        #assert that the returned data matches the user's data
        self.assertEqual(response.data["username"], self.teacher1.username)
        self.assertEqual(response.data["first_name"], self.teacher1.first_name)
        self.assertEqual(response.data["last_name"], self.teacher1.last_name)
        self.assertEqual(response.data["email"], self.teacher1.email)
        self.assertTrue(response.data["is_teacher"])
        self.assertFalse(response.data["is_student"])

        #assert that top_courses is in the returned data
        self.assertIn("top_courses", response.data)
        #assert that there is only one course in top courses - we only created 1 course for teacher1
        self.assertEqual(len(response.data["top_courses"]), 1)

        #get the top course
        top_course = response.data["top_courses"][0]
        #assert the course data matches the data from course1 created in setup
        self.assertEqual(top_course["id"], self.course1.id)
        self.assertEqual(top_course["title"], self.course1.title)
        self.assertEqual(top_course["description"], self.course1.description)
        self.assertEqual(top_course["student_count"], 1)

        #assert that courses is in the returned data - these are all the courses created by a teacher
        self.assertIn("courses", response.data)
        #assert that only 1 course is in courses - we only created one course by teacher1 in setup
        self.assertEqual(len(response.data["courses"]), 1)

        #get the course
        course = response.data["courses"][0]
        #assert the course data matches the data from course1 created in setup
        self.assertEqual(len(response.data["courses"]), 1)
        self.assertEqual(course["id"], self.course1.id)
        self.assertEqual(course["title"], self.course1.title)
        self.assertEqual(course["description"], self.course1.description)
        #we only enrolled 1 student in course1 in setup
        self.assertEqual(course["student_count"], 1)
    
    #test method to ensure the get_students_in_common_view returns the students 2 teachers have in common
    def test_get_students_in_common_view(self):
        #log in teacher1
        self.client.force_login(self.teacher1)

        #send a GET request to the view - simulate teacher1 trying to see the students in common with teacher2
        response = self.client.get(reverse("get_students_in_common_view", args=[self.teacher2.username]))

        #assert that the response contains 1 student only
        self.assertEqual(len(response.data), 1)

        #get the common student data
        common_student = response.data[0]

        #assert that the common student's data matches the student's data
        self.assertEqual(common_student["username"], self.student.username)
        self.assertEqual(common_student["first_name"], self.student.first_name)
        self.assertEqual(common_student["last_name"], self.student.last_name)
    

    #test method to ensure get_enrolled_students_view returns the enrolled student in a course
    def test_get_enrolled_students_view(self):
        #log in teacher1
        self.client.force_login(self.teacher1)

        #send a GET request to the view - simulate teacher1 trying to see the students in course1
        response = self.client.get(reverse("get_enrolled_students_view", args=[self.course1.id]))

        #assert that 1 student is returned
        self.assertEqual(len(response.data), 1)

        #get the enrolled student
        enrolled_student = response.data[0]

        #assert that the returned student's data matches student1's data
        self.assertEqual(enrolled_student["username"], self.student.username)
        self.assertEqual(enrolled_student["first_name"], self.student.first_name)
        self.assertEqual(enrolled_student["last_name"], self.student.last_name)
    
    #test method to ensure get_course_details returns the right data about a course
    def test_get_course_details(self):
        #log in student
        self.client.force_login(self.student)

        #send a GET request to the view - simulate a student trying to see course1 details
        response = self.client.get(reverse("get_course_details", args=[self.course1.id]))

        #assert that the returned course has the right data
        self.assertEqual(response.data["id"], self.course1.id)
        self.assertEqual(response.data["title"], self.course1.title)
        self.assertEqual(response.data["description"], self.course1.description)
        self.assertEqual(response.data["cover_picture"], self.course1.cover_picture.file)
        self.assertEqual(response.data["duration_weeks"], self.course1.duration_weeks)

        #get the week details linked to the course1
        week = response.data["weeks"][0]
        #assert that the week data is correct
        self.assertEqual(week["week_number"], self.week1.week_number)

        #get the lesson data from weeks
        lesson = week["lessons"][0]
        #assert the lesson data is correct
        self.assertEqual(lesson["lesson_number"], self.lesson1.lesson_number)
        self.assertEqual(lesson["title"], self.lesson1.title)
        self.assertEqual(lesson["description"], self.lesson1.description)

        #get the test data
        test = week["tests"][0]
        self.assertEqual(test["title"], self.test1.title)
        self.assertEqual(test["description"], self.test1.description)
        self.assertEqual(test["deadline"], self.test1.deadline.strftime("%d/%m/%Y"))
    
    #test method to ensure teachers can update the title/description of their courses
    def test_update_course_title_description(self):
        #log in teacher1
        self.client.force_login(self.teacher1)

        data = {
            "title": "New course title",
            "description": "New course description"
        }

        #send the PATCH request to update the course title and description
        response = self.client.patch(reverse("update_course_title_description", args=[self.course1.id]), data=data)

        #assert that the response status is 200
        self.assertEqual(response.status_code, 200)

        #assert that the course title in the response matches the new title
        self.assertEqual(response.data["title"], "New course title")

        #assert that the course description in the response matches the new description
        self.assertEqual(response.data["description"], "New course description")
    
    #test method to ensure teachers can create courses
    def test_create_course(self):
        #log in teacher1
        self.client.force_login(self.teacher1)

        #data needed to create a course
        data = {
            "title": "Advanced python",
            "description": "This course covers advanced python topics.",
            "duration_weeks": 1,
            "cover_picture": {
                "title": "Python Cover Picture",
                "file": "https://hjuaebnlfqxvltsiyltu.supabase.co/storage/v1/object/public/Instructo/python.jpeg",
                "thumbnail": "https://hjuaebnlfqxvltsiyltu.supabase.co/storage/v1/object/public/Instructo/python.jpeg",
                "resource_format": "image",
                "resource_type": "course_cover_picture"
            },
            "additional_resources": [
                {
                    "title": "Supplementary Material 1",
                    "file": "https://hjuaebnlfqxvltsiyltu.supabase.co/storage/v1/object/public/Instructo/AWD-CW2-v3.pdf",
                                "resource_format": "pdf",
                    "resource_type": "additional_resource"
                }
            ],
            "weeks": [
                {
                    "week_number": 1,
                    "lessons": [
                        {
                            "lesson_number": 1,
                            "title": "Introduction to Python",
                            "description": "Overview of Python basics.",
                            "lesson_resources": [
                                {
                                    "title": "Introduction Video",
                                    "file": "https://hjuaebnlfqxvltsiyltu.supabase.co/storage/v1/object/public/Instructo/AWD-CW2-v3.pdf",
                                    "resource_format": "pdf",
                                    "resource_type": "learning_material"
                                }
                            ]
                        }
                    ],
                    "tests": [
                        {
                            "title": "Test on Basics",
                            "description": "Test covering basic Python concepts.",
                            "deadline": "2024-09-30",
                            "questions": [
                                {
                                    "text": "What is Python?",
                                    "answers": [
                                        {"text": "A programming language", "is_correct": True},
                                        {"text": "A type of snake", "is_correct": False}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        data_json = json.dumps(data)

        #send a POST request to create the course
        response = self.client.post(reverse("create_course"), data=data_json, content_type="application/json")

        #assert that the response status is 200
        self.assertEqual(response.status_code, 200)

        #assert that the course data is correct
        self.assertEqual(response.data["title"], "Advanced python")
        self.assertEqual(response.data["description"], "This course covers advanced python topics.")
        self.assertEqual(response.data["duration_weeks"], 1)
        self.assertEqual(response.data["cover_picture"]["title"], "Python Cover Picture")
        self.assertEqual(response.data["cover_picture"]["file"], "https://hjuaebnlfqxvltsiyltu.supabase.co/storage/v1/object/public/Instructo/python.jpeg")
        self.assertEqual(response.data["additional_resources"][0]["file"], "https://hjuaebnlfqxvltsiyltu.supabase.co/storage/v1/object/public/Instructo/AWD-CW2-v3.pdf")
        self.assertEqual(response.data["weeks"][0]["week_number"], 1)
        self.assertEqual(response.data["weeks"][0]["lessons"][0]["title"], "Introduction to Python")
        self.assertEqual(response.data["weeks"][0]["tests"][0]["questions"][0]["text"], "What is Python?")
        self.assertEqual(response.data["weeks"][0]["tests"][0]["questions"][0]["answers"][0]["text"], "A programming language")
        self.assertTrue(response.data["weeks"][0]["tests"][0]["questions"][0]["answers"][0]["is_correct"], "A programming language")




        