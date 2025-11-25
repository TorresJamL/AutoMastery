import requests

class Mastery():
    def __init__(self, page_url, course_id, headers):
        self.PAGE_URL = page_url
        self.COURSE_ID = course_id
        self.headers = headers

        self.outcome_updates_dict = {} # {assignment id : calculated outcomes}

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
    
    def __score_to_rubric_score(self, score):
        """Returns the score on the rubric given an assignment score."""
        if score >= 90: return 4
        elif score >= 80: return 3
        elif score >= 60: return 2
        elif score >= 40: return 1
        else: return 0

    def calc_assignment_outcomes(self, assignment_id, student_pairs:dict):
        """Calculates the outcome scores for each student on a particular assignment
        Args:
            assignment_id (int): ID of the assignment
        Returns:
            dict: {student id : {rubric_id : score}, ...}
        """
        rubrics = self.get_assignment_rubrics()
        new_students_outcomes = {}

        for index, (student_id, student_name) in enumerate(student_pairs.items()):
            submission_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments/{assignment_id}/submissions/{student_id}"
            response = requests.get(submission_url, headers=self.headers)

            submission_data: dict = response.json()
            new_students_outcomes[student_id] = {} # 0th index is the rubric dictionary holding {id : outcome score}, 1st is the response

            for rubric_id in rubrics:
                new_students_outcomes[student_id][rubric_id] = self.__score_to_rubric_score(
                    submission_data['score'] if type(submission_data['score']) == float else 0.0)

        self.outcome_updates_dict[assignment_id] = new_students_outcomes    
        return new_students_outcomes

    def update_assignment_outcomes(self, assignment_id, is_jamil_scared_of_updating_every_students_outcome = True):
        """
        Updates the outcomes attached to a singular assignment for every student.
        > MUST CALL calc_assignment_outcomes ON assignment_id FIRST
        Parameters:
            assignment_id (int): id of the assignment
            is_jamil_scared_of_updating_every_students_outcome (bool): Only forces the grade of 1 student, usually the first one on the json list.
        """
        if assignment_id not in self.outcome_updates_dict:
            raise Exception(f"Assignment ID: {assignment_id} not found -> you must call calc_assignment_outcomes on {assignment_id} first.")

        assignment_outcome_data = self.outcome_updates_dict[assignment_id]
        for student_id in assignment_outcome_data:
            submission_url = f"{self.PAGE_URL}/courses/{self.COURSE_ID}/assignments/{assignment_id}/submissions/{student_id}"

            for rubric_id in assignment_outcome_data[student_id]:
                new_outcome = {
                    "rubric_assessment": {
                        str(rubric_id): 
                        {"points" : assignment_outcome_data[student_id][rubric_id]}}}
                
                out_response = requests.put(submission_url, headers=self.headers, json = new_outcome)
                out_response.raise_for_status()
                
                if is_jamil_scared_of_updating_every_students_outcome: break

    def update_all_new_outcomes(self):
        """Updates every changed outcome"""
        for assignment_id in self.outcome_updates_dict:
            self.update_assignment_outcomes(assignment_id)