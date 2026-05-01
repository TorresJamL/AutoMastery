import requests
from _t_ import GS_PWD, GS_USR

from gradescope import Gradescope, Role #! Importing from the gradescope api takes quite a bit.
from gradescope import Course as GradescopeCourse
import os
from _t_ import TOKEN
from pathlib import Path
import json
from MasteryInfo import Mastery

# Given a grade already published from Gradescope to Canvas, 
# mark a rubric item based on their grade and some threshold: 
#     at least a "if score is above T, assign "Mastery" 
# where T can be something like an 80

class Course():
    def __init__(
            self, 
            page_url,
            course_id, 
            overwrite_student_json: bool = False, 
            overwrite_assignment_json: bool = False):
        """
        Either of the overwrite parameters if true will overwrite the respective json loaded data 
        regardless of whether they exist or not.
        """
        self.PAGE_URL = page_url
        self.COURSE_ID = course_id
        self.headers = {
            "Authorization": f"Bearer {TOKEN}"
        }
        self.course_name = self.get_course_name()
        self.mastery = Mastery(self.PAGE_URL, self.COURSE_ID, self.headers)
        self.course_config_root = Path("config") / f"course_id_{self.COURSE_ID}"
        # Data is sensitive student info like grades
        self.course_data_root = Path("data") / f"course_id_{self.COURSE_ID}"
        if not os.path.exists(self.course_config_root):
            os.makedirs(self.course_config_root)
        if not os.path.exists(self.course_data_root):
            os.makedirs(self.course_data_root)

        self.student_data_dict = self.get_student_data(overwrite_student_json) # {id : name}, ...
        self.assignment_id_to_name = self.get_assignment_pairs(overwrite_assignment_json) # {assignment id : assignment name}, ...
        self.gradescope =  Gradescope(
             username=GS_USR,  # * Note, Your user might be the email associated with the account. U
             password=GS_PWD)  # * The password used for the user's gs account )
        gs_courses = self.gradescope.get_courses(role=Role.INSTRUCTOR)
        self.gs_course = self.get_gradescope_course_by_name(gs_courses, self.course_name)

    def get_gradescope_course_by_name(self, courses:list[GradescopeCourse], course_name:str) -> GradescopeCourse:
        for course in courses:
            if course_name in course.full_name:
                return course
        raise ValueError(f"Could not find course name:  {course_name}")


    def get_course_name(self):
        course_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}"
        response = requests.get(course_url, headers=self.headers)
        if not response.ok:
            raise RuntimeError(f"[get_course_name]:\n"\
                               f"| status code: {response.status_code}\n"\
                               f"| text: {response.text}")

        resp_json = response.json()
        return resp_json["name"]

    def find_assignment_id_by_name(self, assignment_name):
        for assignment_id in self.assignment_id_to_name:
            if assignment_name in self.assignment_id_to_name[assignment_id]:
                return assignment_id
        raise RuntimeError(f"Assignment name '{assignment_name}' not found")

    def get_students(self):
        """
        Returns a list of dictionaries holding individual student data.
        More accurately returns a list of User objects: https://developerdocs.instructure.com/services/canvas/resources/users#user
        """
        all_students = []
        course_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/users?enrollment_type[]=student"

        response = requests.get(course_url, headers=self.headers)
        if not response.ok:
            print("Error:", response.status_code, response.text)
            raise Exception("Response not ok :(")
        while course_url != None:
            try: 
                response = requests.get(course_url, headers=self.headers)

                if not response.ok:
                    print("Error:", response.status_code, response.text)
                    break
                students = response.json()
                all_students.extend(students)

                if "next" in response.links:
                    course_url = response.links["next"]["url"]
                else:
                    course_url = None
                print(course_url)
            except Exception as err:
                print("Error while fetching:", err)
                break
        return all_students
    
    def get_student_data(self, should_overwrite = False):
        """Returns a dictionary where the key is the student ID and the value is the student name.

        Can raise a key error when the user running Automastery is not a teacher. 
        email & sis_user_id require Teacher permissions on the chosen course.
        """
        if (self.course_data_root /  "student_data.json").exists() and not should_overwrite:
            with open(self.course_data_root / "student_data.json", 'r') as student_data_file:
                return json.load(student_data_file) 
        else:
            sid_to_student_data_dict = {}
            for student in self.get_students():
                student_data_dict = {}
                keys_in_dict = ["id", "name", "short_name", "email", "sis_user_id", "sortable_name"]
                for key in keys_in_dict:
                    student_data_dict[key] = student[key]
                sid_to_student_data_dict[student["sis_user_id"]] = student_data_dict

            with open(self.course_data_root / "student_data.json", 'w+') as student_data_file:
                json.dump(sid_to_student_data_dict, student_data_file, indent=4)

            return sid_to_student_data_dict
    
    def get_assignments(self):
        """
        Returns a list of dictionaries holding individual assignment data.
        More accurately returns a list of assignment objects: https://developerdocs.instructure.com/services/canvas/resources/assignments
        """
        all_assignments = []
        assignment_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments"

        response = requests.get(assignment_url, headers=self.headers)
        while assignment_url:
            try:
                print(assignment_url)
                response = requests.get(assignment_url, headers=self.headers)
                if not response.ok:
                    print("Error:", response.status_code, response.text)
                    raise Exception("Response not ok :(")
                
                assignments = response.json()
                all_assignments.extend(assignments)
                
                if "next" in response.links:
                    assignment_url = response.links["next"]["url"]
                else:
                    assignment_url = None
            except Exception as err:
                print("Error while fetching:", err)
                break

        return all_assignments
    
    def get_assignment_pairs(self, should_overwrite = False):
        """Returns a dictionary where the key is the assignment ID and the value is the assignment name."""
        if (self.course_config_root / "assignment_data.json").exists() and not should_overwrite:
            with open(self.course_config_root / "assignment_data.json", 'r') as assignment_data_file:
                return json.load(assignment_data_file) 
        else:
            assignment_dict = {}
            for assignment in self.get_assignments() :
                assignment_dict[assignment['id']] = assignment['name']

            with open(self.course_config_root / "assignment_data.json", 'w+') as assignment_data_file:
                json.dump(assignment_dict, assignment_data_file, indent=4)
        
            return assignment_dict

    def create_new_assignment_outcomes(self, assignment_id):
        """ 
        Calculates the outcome scores for each student on a particular assignment
        Args:
            assignment_id (int): 
        """
        self.mastery.calc_assignment_outcomes(assignment_id, self.student_data_dict)
    
    def update_assignment_outcomes(self, assignment_id):
        """
        Updates the outcomes attached to a singular assignment for every student.
        The outcomes for the assignment MUST be calculated first.
        Parameters:
            assignment_id (int): id of the assignment
            is_jamil_scared_of_updating_every_students_outcome (bool): Only forces the grade of 1 student, the first one on the json list.
        """
        self.mastery.update_assignment_outcomes(self, assignment_id)
