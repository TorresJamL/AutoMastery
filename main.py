import requests
from _t_ import TOKEN
from pathlib import Path
import json
import os
import pandas as pd

# import gradescope CSVs and make DataFrames
exam1 = pd.read_csv("exam1file.csv")
exam2 = pd.read_csv("exam2file.csv")
# print(exam2.columns[14]) # exam subquestions start at index 14 for both exams

"""
Given a grade already published from Gradescope to Canvas, 
mark a rubric item based on their grade and some threshold: 
    at least a "if score is above T, assign "Mastery" 
where T can be something like an 80
"""
class CourseInfo():
    def __init__(self, course_id, overwrite_jsons: bool = False):
        """
        override_jsons if true will overwrite the json loaded data regardless of whether they exist or not
        """
        self.PAGE_URL = "https://sit.instructure.com/api/v1"
        self.COURSE_ID = course_id #80807
        self.headers = {
            "Authorization": f"Bearer {TOKEN}"
        }
        # students is a list of dictionaries formated in the following:
        # {id: ---, name: ---, created_at: ---, sortable_name: ---, short_name: ---}
        self.students = None
        self.id_name_pairs = None
        if Path("student_data.json").exists():
            with open("student_data.json", 'r') as student_data_file:
                print("Begin JSON loading...")
                self.id_name_pairs = json.load(student_data_file) 
                print("JSON loading done.")
        else:
            self.students = self.get_students() 
            self.id_name_pairs = self.get_id_name_pairs()
            with open("student_data.json", 'w+') as student_data_file:
                print("Begin JSON data dump...")
                json.dump(self.id_name_pairs, student_data_file, indent=4)
                print("JSON data dump done.")

    def get_students(self):
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
    
    def get_id_name_pairs(self):
        student_dict = {}
        for student in self.students:
            student_dict[student['id']] = student['name']
        return student_dict
    
    def get_assignments(self):
        assignment_pairs = {}
        assignment_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments"
        response = requests.get(assignment_url, headers=self.headers)

        max_loop_count = 100
        while assignment_url and max_loop_count >= 0:
            try:
                print(assignment_url)
                response = requests.get(assignment_url, headers=self.headers)
                if not response.ok:
                    print("Error:", response.status_code, response.text)
                    raise Exception("Response not ok :(")
                
                assignments = response.json()
                for assignment in assignments:
                    # assignment_pairs.append({assignment['id'] : assignment['name']})
                    assignment_pairs[assignment['id']] = assignment['name']
                
                if "next" in response.links:
                    assignment_url = response.links["next"]["url"]
                else:
                    assignment_url = None
                max_loop_count-=1
            except Exception as err:
                print("Error while fetching:", err)
                break

        return assignment_pairs
    
    def get_assignment_rubrics(self, assignment_id):
        """Returns a dictionary where the key is the rubric ID and the value is the rubric item name."""
        rubric_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments/{assignment_id}?include[]=rubric&include[]=rubric_association"
        response = requests.get(rubric_url, headers=self.headers)
        response.raise_for_status()

        rubrics_data = response.json()
        #print(rubrics_data["rubric_settings"]) # HOW TO RETRIEVE RUBRIC ID
        # I think my issue with defining a separate function for all rubric outcomes is 
        # not working because the ID is associated with an assignment so let's just make this function longer.
        assignment_name = rubrics_data['name']

        #collect all of the possible rubric outcomes from rubric_id
        rubric_id = rubrics_data['rubric_settings']['id']
        rubrics_url = (
        f"{self.PAGE_URL}/courses/{self.COURSE_ID}/rubrics/{rubric_id}"
        f"?include[]=rubric&include[]=rubric_associations"
        )
        response2 = requests.get(rubrics_url, headers=self.headers)
        response2.raise_for_status()
        all_outcomes = response2.json()

        # This retrieves the rubric used for each assignment
        rubric_pairs = {}
        for i in range(len(rubrics_data['rubric'])):
            rubric_pairs[rubrics_data['rubric'][i]['id']] = rubrics_data['rubric'][i]['description']
        return [assignment_name, rubric_pairs, all_outcomes]
    
    def update_assignment_outcomes(self, assignment_id, is_jamil_scared_of_updating_every_students_outcome = True):
        """
        Updates the outcomes attached to a singular assignment for every student.
        """
        def _score_to_rubric_score(score):
            """Returns the score on the rubric given an assignment score."""
            if score >= 90: return 4
            elif score >= 80: return 3
            elif score >= 60: return 2
            elif score >= 40: return 1
            else: return 0

        ### Test with labs 2 & 3
        rubrics = self.get_assignment_rubrics()
        for index, (student_id, student_name) in enumerate(self.id_name_pairs.items()):
            submission_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments/{assignment_id}/submissions/{student_id}"
            response = requests.get(submission_url, headers=self.headers)

            submission_data: dict = response.json()
            for rubric_id in rubrics:
                new_outcome = {
                    "rubric_assessment": {
                        str(rubric_id): 
                        {"points" : _score_to_rubric_score(
                            submission_data['score'] if type(submission_data['score']) != float else 0)}}}
                
                out_response = requests.put(submission_url, headers=self.headers, json = new_outcome)
                out_response.raise_for_status()
                
                print(f"User: {student_id}, {student_name} :: Score: {response.json()['score']}, Rubric Score: {new_outcome['rubric_assessment'][str(rubric_id)]['points']}")
                if is_jamil_scared_of_updating_every_students_outcome: break

''' Class to hold data for an assignment, including questions and subquestions
    Note: Canvas assignments are one assignment per lab/HW/whatever, but PER QUESTION for each exam question.
'''
class Assignment():
    # constructor with no name/id for Exams since they are by question on canvas
    def __init__(self, course, name):
        self.course = course
        self.name = name 
        self.id = None
        self.mastery_score = 0
        if (self.id is not None):
            self.rubric = self.course.get_assignment_rubrics(self.id)

    def __init__(self, course, name, eid):
        self.course = course # instance of CourseInfo
        self.name = name
        self.id = eid
        self.mastery_score = 0 # default value
        if (self.id is not None):
            self.rubric = self.course.get_assignment_rubrics(self.id)

class Exam(Assignment):
    def __init__(self, course, name):
        super().__init__(course, name) # we will be using the name for personal id purposes
        self.questions = []
        self.canvas_ids = []

    ''' Add sub questions from Gradescope CSV to self attribute.'''
    def assign_questions(self, df):
        for col in df[14:]: # index 14 is where the questions start
            self.questions.append(col)

    ''' Save all Canvas assignment ids for an exam since there are assignments
        per question on Canvas
    '''
    def get_ids(self):
        for id in self.course.get_assignments().keys():
            # specific use when given a name, it should be "Exam 1" or "Exam 2"
            # or whatever part is contained in each Canvas assignment title
            if self.name in id:
                self.canvas_ids.append(id)

def main():
    pass
    #lab 2: 624443
    # exam 1 q1: 630173
    # course.update_assignment_outcomes(624443) 

    course = CourseInfo(80807)
    assignments = course.get_assignments()
    rubric = course.get_assignment_rubrics(624443)[2]
    print(rubric)
    #e1 = Exam()
    #print(assignments[630173])
    #print(course.get_assignment_rubrics(630173)[1]) # return the assignment name
    # OUTPUT: {'_9538': '2: Correctly implement code according to a given design'}

if __name__ == "__main__":

    main()