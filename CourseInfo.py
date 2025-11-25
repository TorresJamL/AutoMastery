import requests
from _t_ import TOKEN
from pathlib import Path
import json
from MasteryInfo import Mastery
"""
Given a grade already published from Gradescope to Canvas, 
mark a rubric item based on their grade and some threshold: 
    at least a "if score is above T, assign "Mastery" 
where T can be something like an 80
"""
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
        self.COURSE_ID = course_id #80807 for CS115
        self.headers = {
            "Authorization": f"Bearer {TOKEN}"
        }
        self.mastery = Mastery(self.PAGE_URL, self.COURSE_ID, self.headers)
        
        self.student_pairs = self.get_student_pairs(overwrite_student_json) # {id : name}, ...
        self.assignment_pairs = self.get_assignment_pairs(overwrite_assignment_json) # {assignment id : assignment name}, ...

    def get_students(self):
        """Returns a list of dictionaries holding individual student data."""
        max_loop_count = 100
        all_students = []
        course_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/users?enrollment_type[]=student"

        response = requests.get(course_url, headers=self.headers)
        if not response.ok:
            print("Error:", response.status_code, response.text)
            raise Exception("Response not ok :(")
        while course_url != None and max_loop_count > 0:
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
                max_loop_count-=1
            except Exception as err:
                print("Error while fetching:", err)
                break
        return all_students
    
    def get_student_pairs(self, should_overwrite = False):
        """Returns a dictionary where the key is the student ID and the value is the student name."""
        if Path("student_data.json").exists() and not should_overwrite:
            with open("student_data.json", 'r') as student_data_file:
                return json.load(student_data_file) 
        else: 
            student_dict = {}
            for student in self.get_students():
                student_dict[student['id']] = student['name']

            with open("student_data.json", 'w+') as student_data_file:
                json.dump(student_dict, student_data_file, indent=4)

            return student_dict
    
    def get_assignments(self):
        """Returns a dictionary where the key is the assignemnt ID and the value is the assignemnt name."""
        max_loop_count = 100
        all_assignments = []
        assignment_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments"

        response = requests.get(assignment_url, headers=self.headers)
        while assignment_url and max_loop_count >= 0:
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
                max_loop_count-=1
            except Exception as err:
                print("Error while fetching:", err)
                break

        return all_assignments
    
    def get_assignment_pairs(self, should_overwrite = False):
        """Returns a dictionary where the key is the assignment ID and the value is the assignment name."""
        if Path("assignment_data.json").exists() and not should_overwrite:
            with open("assignment_data.json", 'r') as assignment_data_file:
                return json.load(assignment_data_file) 
        else:
            assignment_dict = {}
            for assignment in self.get_assignments() :
                assignment_dict[assignment['id']] = assignment['name']

            with open("assignment_data.json", 'w+') as assignment_data_file:
                json.dump(assignment_dict, assignment_data_file, indent=4)
        
            return assignment_dict

    def create_new_assignment_outcomes(self, assignment_id):
        """ Calculates the outcome scores for each student on a particular assignment
        Args:
            assignment_id (int): 
        Returns:
            dict: A dict holding the new student outcome scores for that assignment. Formatted: {student id : {rubric_id : score}, ...}
        """
        return self.mastery.calc_assignment_outcomes(assignment_id, self.student_pairs)
    
    def update_assignment_outcomes(self, assignment_id):
        """
        Updates the outcomes attached to a singular assignment for every student.
        The outcomes for the assignment MUST be calculated first.
        Parameters:
            assignment_id (int): id of the assignment
            is_jamil_scared_of_updating_every_students_outcome (bool): Only forces the grade of 1 student, the first one on the json list.
        """
        self.mastery.update_assignment_outcomes(self, assignment_id)