import requests
from _t_ import TOKEN
from pathlib import Path
import json
"""
Given a grade already published from Gradescope to Canvas, 
mark a rubric item based on their grade and some threshold: 
    at least a "if score is above T, assign "Mastery" 
where T can be something like an 80
"""
class CourseInfo():
    def __init__(self, course_id, overwrite_jsons: bool = False):
        """
        override_jsons if true will overwrite the json loaded data regardless of whether they exist or not. (in case of students withdraw or join in)
        """
        self.PAGE_URL = "https://sit.instructure.com/api/v1"
        self.COURSE_ID = course_id #80807 for CS115
        self.headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        # students is a list of dictionaries formated in the following:
        # {id: ---, name: ---, created_at: ---, sortable_name: ---, short_name: ---}
        self.students = None
        # id - name, dictionary formatted: {id : name}
        self.id_name_pairs = None
        if Path("student_data.json").exists() and not overwrite_jsons:
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
    
    def get_id_name_pairs(self):
        """Returns a dictionary where the key is the student ID and the value is the student name."""
        student_dict = {}
        for student in self.students:
            student_dict[student['id']] = student['name']
        return student_dict
    
    def get_assignments(self):
        """Returns a dictionary where the key is the assignemnt ID and the value is the assignemnt name."""
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

        rubric_pairs = {}
        for i in range(len(rubrics_data['rubric'])):
            rubric_pairs[rubrics_data['rubric'][i]['id']] = rubrics_data['rubric'][i]['description']
        return rubric_pairs
    
    def update_assignment_outcomes(self, assignment_id, is_jamil_scared_of_updating_every_students_outcome = True):
        """
        Updates the outcomes attached to a singular assignment for every student.

        Parameters:
            assignment_id (int): id of the assignment
            is_jamil_scared_of_updating_every_students_outcome (bool): Only forces the grade of 1 student, usually the first one on the json list.
        
        Returns:
            None (None): 
        """
        def _score_to_rubric_score(score):
            """Returns the score on the rubric given an assignment score."""
            # TODO: Customize rubric thresholds to remove this function!
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
                            submission_data['score'] if type(submission_data['score']) == float else 0.0)}}}
                
                out_response = requests.put(submission_url, headers=self.headers, json = new_outcome)
                out_response.raise_for_status()
                
                print(f"User: {student_id}, {student_name} :: Score: {response.json()['score']}, Rubric Score: {new_outcome['rubric_assessment'][str(rubric_id)]['points']}")
                if is_jamil_scared_of_updating_every_students_outcome: break
    

def main():
    course = CourseInfo(80807)

if __name__ == "__main__":
    main()