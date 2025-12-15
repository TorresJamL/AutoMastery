import json
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import re
from pathlib import Path
from data_utils import assignment_match_to_csv_name

import requests

''' Class to hold data for an assignment, including questions and subquestions
    Note: Canvas assignments are one assignment per lab/HW/whatever, but PER QUESTION for each exam question.
'''
class StudentNotFoundError(RuntimeError):
    pass

class StudentSubmissionNotFoundError(RuntimeError):
    pass
class Assignment(ABC):
    def __init__(self, name, id, course):
        self.name = name
        self.course = course
        self.assignment_id = id

    @property
    @abstractmethod
    def need_to_update_total_question_score(self):
        raise NotImplementedError()

    @abstractmethod
    def compute_new_outcome(self, sid, student_name, submission_url):
        pass

    def score_to_rubric_score(self, score):
        """Returns the score on the rubric given an assignment score."""
        if score >= 0.99:
            return 4
        elif score >= 0.75:
            return 3
        elif score >= 0.5:
            return 2
        elif score >= 0.25:
            return 1
        else:
            return 0

    def update_mastery_scores(self, student_name_match=None):
        student_data_dict = self.course.student_data_dict #read only
        for sid in student_data_dict.keys():
            if student_name_match is not None:
                if student_name_match not in student_data_dict[sid]["name"]:
                    continue
            self.update_mastery_score_for_student(int(sid), student_data_dict[sid])


    def update_mastery_score_for_student(self, sid, student_data_dict):
        # Prepare the request
        student_id = student_data_dict["id"]
        submission_url = f"{self.course.PAGE_URL}/courses/{self.course.COURSE_ID}/assignments/{self.assignment_id}/submissions/{student_id}"
        student_name = student_data_dict["short_name"]
        new_outcome = self.compute_new_outcome(sid, student_name, submission_url)

        # Needs to be done without the score to work for some reason
        out_response = requests.put(submission_url, headers=self.course.headers, json=new_outcome)
        out_response.raise_for_status()

        if self.need_to_update_total_question_score:
            total_question_score = self.compute_total_question_score(sid, student_name)
            # Then make sure to update the score. I don't know why this is needed...
            out_response = requests.put(submission_url, headers=self.course.headers, json=new_outcome,
                                        data={"submission[posted_grade]": int(total_question_score)})
            out_response.raise_for_status()


class LoadFromCSVAssignment(Assignment):
    def __init__(self, name, id, course):
        super().__init__(name, id, course)
        csv_name = assignment_match_to_csv_name(self.name)
        self.score_df = pd.read_csv(csv_name)
        self.rubric_id_to_qkeys = self.load_rubric_id_to_qkeys() #load from a json file
        self.rubric_id_to_total_pts = self.get_rubric_id_to_total_pts(self.rubric_id_to_qkeys)

    @property
    def need_to_update_total_question_score(self):
        return True

    def load_rubric_id_to_qkeys(self):
        #looks for the filename
        filename = Path('rubric_id_to_question_keys') / f"{self.assignment_id}.json"
        if not filename.exists():
            rubric_id_to_qkeys = self.select_rubric_id_to_qkeys()
            with open(filename, "w") as json_file:
                json.dump(rubric_id_to_qkeys, json_file)
            return rubric_id_to_qkeys
        else:
            with open(filename) as json_file:
                return json.load(json_file)

    def _question_key_to_total_pts(self, question_key):
        match = re.search(r'\((\d+(?:\.\d+)?)\s*pts\)', question_key)
        if match:
            return float(match.group(1))
        else:
            raise RuntimeError("Unable to find match")


    def get_rubric_id_to_total_pts(self, rubric_id_to_qkeys):
        rubric_id_to_total_pts = {}
        for rubric_id in rubric_id_to_qkeys:
            rubric_id_to_total_pts[rubric_id] = 0
            for question_key in rubric_id_to_qkeys[rubric_id]:
                rubric_id_to_total_pts[rubric_id] += self._question_key_to_total_pts(question_key)
        return rubric_id_to_total_pts

    def select_rubric_id_to_qkeys(self):
        """Returns a dictionary where the key is the rubric ID and the value is the rubric item name."""
        rubric_id_to_rubric_data = {}
        rubric_url = f"{self.course.PAGE_URL}/courses/{self.course.COURSE_ID}/assignments/{self.assignment_id}?include[]=rubric&include[]=rubric_association"
        response = requests.get(rubric_url, headers=self.course.headers)
        response.raise_for_status()
        canvas_rubrics_data = response.json()
        for rubric in canvas_rubrics_data['rubric']:
            print(rubric) # print description and some more info about it
            print(f"Rubric item description: {rubric['description']}")

            # print df questions and corresponding indices
            inferred_keys = self.infer_assignment_keys_from_df(self.score_df)
            keys_for_rubric_item = []
            # get the indices
            for i, question_key in enumerate(inferred_keys):
                print("##########################")
                print(f"Subquestion {i} \n")
                print(question_key)
                res = input("Does this key correspond to the above rubric item? (y/n)")
                if res == "y":
                    keys_for_rubric_item.append(question_key)
                print("##########################")

            # wait for confirmation
            print("Confirm that these are the correct question keys")
            for question_key in keys_for_rubric_item:
                print(f"Confirming question key: {question_key}")
            print("Done: saving to the dictionary")
            rubric_id_to_rubric_data[rubric['id']] = keys_for_rubric_item
        return rubric_id_to_rubric_data


    def find_student_df_in_df(self, sid, student_name):
        if sid not in list(self.score_df["SID"]):
            #raise RuntimeError(f"Could not find student: {student_name}")
            raise StudentNotFoundError(f"Could not find student: {student_name}")

        student_df = self.score_df.loc[self.score_df["SID"] == sid].squeeze()
        return student_df


    def compute_new_outcome(self, sid, student_name, submission_url):
        student_df = self.find_student_df_in_df(sid, student_name)
        if student_name is None:
            return None

        new_outcome = {
            "rubric_assessment": {}}

        for rubric_id in self.rubric_id_to_qkeys:
            qkeys = self.rubric_id_to_qkeys[rubric_id]
            mastery_score = self.compute_mastery_score(rubric_id, qkeys, student_df)
            new_outcome["rubric_assessment"][str(rubric_id)] = {"points": mastery_score}
        print(f"{student_name} new outcome: {new_outcome}")
        return new_outcome


    def compute_mastery_score(self, rubric_id, qkeys, student_df) -> int:
        total_mastery_score = 0
        for qkey in qkeys:
            if qkey not in student_df:
                print("Cannot find student data for key {qkey}")
            subscore = student_df[qkey]
            total_mastery_score += subscore
        score = total_mastery_score / self.rubric_id_to_total_pts[rubric_id]
        mastery_score = self.score_to_rubric_score(score)
        return mastery_score

    @abstractmethod
    def infer_assignment_keys_from_df(self, student_df):
        """
        :param student_df:
        :return: Infers which columns of the student_df correspond to
        the assignment based on self.name
        """
        raise NotImplementedError()

    def compute_total_question_score(self, sid, student_name):
        student_df = self.find_student_df_in_df(sid, student_name)
        total_question_score = 0
        inferred_keys = self.infer_assignment_keys_from_df(student_df)
        for qkey in inferred_keys:
            total_question_score += student_df[qkey]
        if np.isnan(total_question_score):
            total_question_score = 0
        return total_question_score



class ExamQuestion(LoadFromCSVAssignment):
    def infer_assignment_keys_from_df(self, student_df):
        assignment_keys = []
        question_in_assignment_name = int(re.search(r'Question\s+(\d+)', self.name).group(1))
        for key in student_df.keys():
            if "pts" not in key:
                continue
            match = re.match(r'(\d+(?:\.\d+)?)\s*:', key)
            if match:
                question_in_key = int(match.group(1)[0])
                if question_in_key == question_in_assignment_name:
                    assignment_keys.append(key)
            else:
                raise RuntimeError("Unable to find match for total question")
        return assignment_keys

class Homework(LoadFromCSVAssignment):
    def infer_assignment_keys_from_df(self, student_df):
        assignment_keys = []
        for key in student_df.keys():
            if "pts" not in key:
                continue
            assignment_keys.append(key)
        return assignment_keys

class Lab(Assignment):

    @property
    def need_to_update_total_question_score(self):
        return False

    def compute_new_outcome(self, sid, student_name, submission_url):
        response = requests.get(submission_url, headers=self.course.headers)

        submission_data: dict = response.json()
        if "score" not in submission_data:
            raise StudentSubmissionNotFoundError(f"Could not find submission: {submission_url}")

        score = submission_data["score"]

        new_outcome = {
            "rubric_assessment": {}}

        rubric_url = f"{self.course.PAGE_URL}/courses/{self.course.COURSE_ID}/assignments/{self.assignment_id}?include[]=rubric&include[]=rubric_association"
        response = requests.get(rubric_url, headers=self.course.headers)
        response.raise_for_status()
        canvas_rubrics_data = response.json()
        for rubric in canvas_rubrics_data['rubric']:
            mastery_score = self.score_to_rubric_score(score/100)
            new_outcome["rubric_assessment"][str(rubric["id"])] = {"points": mastery_score}
        print(f"{student_name} new outcome: {new_outcome}")
        return new_outcome


def make_assignment_from_name(assignment_name, assignment_id, course):
    if "Exam" in assignment_name:
        assignment_cls = ExamQuestion
    elif "Homework" in assignment_name:
        assignment_cls = Homework
    elif "Lab" in assignment_name:
        assignment_cls = Lab
    assignment = assignment_cls(assignment_name, assignment_id, course)
    return assignment
