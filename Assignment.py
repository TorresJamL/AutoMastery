import json
from abc import ABC, abstractmethod
from typing import Union, Any

import numpy as np
import pandas as pd
import re
from pathlib import Path

from data_utils import assignment_match_to_csv_name, StudentNotFoundError, StudentSubmissionNotFoundError, find_student_df_by_SID
from CourseInfo import Course

import requests

''' Class to hold data for an assignment, including questions and subquestions
    Note: Canvas assignments are one assignment per lab/HW/whatever, but PER QUESTION for each exam question.
'''


class Assignment(ABC):
    def __init__(self, name: str, assignment_id: int, course: Course):
        """

        Args:
            name: The name of the assignment, Homework 4, Exam 1, etc..
                must match what the name is on Canvas
            assignment_id: The Canvas assignment ID
            course: Course object.
        """
        self.name = name
        self.course = course
        self.assignment_id = assignment_id

    @property
    @abstractmethod
    def need_to_update_total_question_score(self)->bool:
        """
        Returns: Whether a total_question_score needs to be updated.
        """
        raise NotImplementedError()

    @abstractmethod
    def compute_new_outcome(self, sid :int, student_name: str, submission_url:str)->dict:
        """

        Args:
            sid: Canvas Student ID
            student_name: student name (mostly for logging purposes)
            submission_url: correctly formatted Canvas API submission URL

        Returns:
            A dictionary corresponding to the new outcome, which is compatible with the
            PUT/POST request to update rubric items for a submission.
        """
        pass

    def score_to_rubric_score(self, score:float)->int:
        """

        Args:
            score: A number from 0 to 1 corresponding to the percentage

        Returns:
            A mastery rubric score from 1 to 4.

        """
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

    def update_mastery_scores(self, student_name_match :str = None):
        """

        Updates mastery scores on Canvas for this assignment for all students, or for
        a student who matches a particular name, student_name_match

        Args:
            student_name_match: Optional argument of a student's name to update,
            if not updating scores for all students.

        """
        student_data_dict = self.course.student_data_dict #read only
        for sid in student_data_dict.keys():
            if student_name_match is not None:
                if student_name_match not in student_data_dict[sid]["name"]:
                    continue
            self.update_mastery_score_for_student(int(sid), student_data_dict[sid])


    def update_mastery_score_for_student(self, sid:int, student_data_dict:dict):
        """
        Updates mastery score for a particular student on Canvas
        Args:
            sid: Canvas student ID
            student_data_dict: A dictionary containing all the student's Canvas data
               with their Canvas student ID as keys.

        """
        student_id = student_data_dict["id"]
        submission_url = f"{self.course.PAGE_URL}/courses/{self.course.COURSE_ID}/assignments/{self.assignment_id}/submissions/{student_id}"
        student_name = student_data_dict["short_name"]
        try:
            new_outcome = self.compute_new_outcome(sid, student_name, submission_url)
        except StudentSubmissionNotFoundError as e:
            print(e)
            return
        except StudentNotFoundError as e:
            print(e)
            return

        # Needs to be done without the score to work for some reason
        out_response = requests.put(submission_url, headers=self.course.headers, json=new_outcome)
        out_response.raise_for_status()

        if self.need_to_update_total_question_score:
            total_question_score = self.compute_total_question_score(sid, student_name)
            # Then make sure to update the score. I don't know why this is needed...
            out_response = requests.put(submission_url, headers=self.course.headers, json=new_outcome,
                                        data={"submission[posted_grade]": int(total_question_score)})
            out_response.raise_for_status()

    def compute_total_question_score(self, sid:int, student_name:str)->int:
        """

        Only needs to be implemented if the class has self.need_to_update_total_question_score

        Args:
            sid: Student ID on Canvas
            student_name: student name on canvas (for logging purposes)

        Returns:
            Total question score (as in for the entire question, not subparts)
            for this assignment.

        """
        pass


class LoadFromCSVAssignment(Assignment):
    """
    An assignment that's loaded from a Gradescope CSV
    The name maps to a CSV file (not the cleanest I know...)
    """
    def __init__(self, name:str, assignment_id:int, course:Course):
        super().__init__(name, assignment_id, course)
        csv_name = assignment_match_to_csv_name(self.name)
        self.score_df = pd.read_csv(csv_name)
        self.rubric_id_to_qkeys = self.load_rubric_id_to_qkeys() #load from a json file
        self.rubric_id_to_total_pts = self.get_rubric_id_to_total_pts(self.rubric_id_to_qkeys)

    @property
    def need_to_update_total_question_score(self)->bool:
        return True

    def load_rubric_id_to_qkeys(self)->dict:
        """
            Checks if there is a file for that assignment id
            corresponding to the question keys
            and makes one if not.
        """
        #looks for the filename
        filename = Path('rubric_id_to_question_keys') / f"{self.assignment_id}.json"
        if not filename.exists():
            rubric_id_to_qkeys = self.select_rubric_id_to_qkeys
            with open(filename, "w") as json_file:
                json.dump(rubric_id_to_qkeys, json_file)
            return rubric_id_to_qkeys
        else:
            with open(filename) as json_file:
                return json.load(json_file)

    def _question_key_to_total_pts(self, question_key: str)->int:
        """

        Args:
            question_key: The name of the question on the CSV file

        Returns: How many points that question is worth (as inferred by the
        question key)

        """
        match = re.search(r'\((\d+(?:\.\d+)?)\s*pts\)', question_key)
        if match:
            return float(match.group(1))
        else:
            raise RuntimeError("Unable to find match")


    def get_rubric_id_to_total_pts(self, rubric_id_to_qkeys :dict)->dict[str, Union[int, float]]:
        """

        Args:
            rubric_id_to_qkeys: Dictionary mapping rubric IDs to question keys

        Returns: A dictionary mapping rubric ids
         to the total number of points possible (across all qkeys) for that rubric id

        """
        rubric_id_to_total_pts = {}
        for rubric_id in rubric_id_to_qkeys:
            rubric_id_to_total_pts[rubric_id] = 0
            for question_key in rubric_id_to_qkeys[rubric_id]:
                rubric_id_to_total_pts[rubric_id] += self._question_key_to_total_pts(question_key)
        return rubric_id_to_total_pts

    @property
    def select_rubric_id_to_qkeys(self)-> dict[str, dict]:
        """
        A minimal user interface that prompts the users for whether each of the
        subquestions for a given question correspond to a particular rubric outcome

        Returns: the rubric_id_to_qkeys for that assignment

        """
        rubric_url = f"{self.course.PAGE_URL}/courses/{self.course.COURSE_ID}/assignments/{self.assignment_id}?include[]=rubric&include[]=rubric_association"
        response = requests.get(rubric_url, headers=self.course.headers)
        response.raise_for_status()
        canvas_rubrics_data = response.json()
        rubric_id_to_rubric_data: dict[str, dict] = {}
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




    def compute_new_outcome(self, sid:str, student_name:str, submission_url:str, verbose:bool=False) -> dict:
        student_df = find_student_df_by_SID(self.score_df, sid, student_name = student_name)
        if student_name is None:
            return None

        new_outcome = {
            "rubric_assessment": {}}

        for rubric_id in self.rubric_id_to_qkeys:
            qkeys = self.rubric_id_to_qkeys[rubric_id]
            mastery_score = self.compute_mastery_score(rubric_id, qkeys, student_df)
            if mastery_score is not None:
                new_outcome["rubric_assessment"][str(rubric_id)] = {"points": mastery_score}
            else:
                print("Mastery score was None")
        if verbose:
            print(f"{student_name} new outcome: {new_outcome}")
        return new_outcome


    def compute_mastery_score(self, rubric_id:str, qkeys:list, student_df:pd.DataFrame):
        """

        Args:
            rubric_id: rubric_id corresponding to the outcome we want to calculate the score for
            qkeys: question keys from the df to use to calculate the mastery score
            student_df: Pandas DataFrame containing student data

        Returns:

        """
        total_mastery_score = 0
        for qkey in qkeys:
            if qkey not in student_df:
                print("Cannot find student data for key {qkey}")
            subscore = student_df[qkey]
            total_mastery_score += subscore
        score = total_mastery_score / self.rubric_id_to_total_pts[rubric_id]

        if "Homework 5" in self.name and rubric_id == "_3113":
            if score <= 1: #standard case
                return None

        mastery_score: int = self.score_to_rubric_score(score)
        return mastery_score

    @abstractmethod
    def infer_assignment_keys_from_df(self, student_df:pd.DataFrame) -> list:
        """
        :param student_df:
        :return: Infers which columns of the student_df correspond to
        the assignment based on self.name
        """
        raise NotImplementedError()

    def compute_total_question_score(self, sid:int, student_name:str) -> Union[float, int]:
        student_df = find_student_df_by_SID(self.score_df, sid, student_name)
        total_question_score = 0
        inferred_keys = self.infer_assignment_keys_from_df(student_df)
        for qkey in inferred_keys:
            total_question_score += student_df[qkey]
        if np.isnan(total_question_score):
            total_question_score = 0
        return total_question_score



class ExamQuestion(LoadFromCSVAssignment):
    def infer_assignment_keys_from_df(self, student_df:pd.DataFrame) -> list:
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
    def infer_assignment_keys_from_df(self, student_df:pd.DataFrame) -> list:
        assignment_keys = []
        for key in student_df.keys():
            if "pts" not in key:
                continue
            assignment_keys.append(key)
        return assignment_keys

class Lab(Assignment):

    @property
    def need_to_update_total_question_score(self)->bool:
        return False

    def compute_new_outcome(self, sid:str, student_name:str, submission_url:str):
        response = requests.get(submission_url, headers=self.course.headers)

        submission_data: dict = response.json()
        if "score" not in submission_data:
            raise StudentSubmissionNotFoundError(f"Could not find submission: {submission_url}")

        score = submission_data["score"]
        if score is None:
            raise StudentSubmissionNotFoundError(f"Could not find submission: {student_name}")

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


def make_assignment_from_name(assignment_name, assignment_id, course) -> Assignment:
    """

    Args:
        assignment_name: Name (must contain Lab, Homework Exam or Test as is on Canvas)
        assignment_id: Canvas assignment ID
        course: Course that contains the assignments

    Returns: Assignment object corresponding of the type inferred by the name

    """
    if "Exam" in assignment_name or "Test" in assignment_name:
        assignment_cls = ExamQuestion
    elif "Homework" in assignment_name:
        assignment_cls = Homework
    elif "Lab" in assignment_name:
        assignment_cls = Lab
    assignment = assignment_cls(assignment_name, assignment_id, course)
    return assignment
