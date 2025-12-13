import json
import numpy as np
import pandas as pd
import re
import os
from pathlib import Path

import requests

''' Class to hold data for an assignment, including questions and subquestions
    Note: Canvas assignments are one assignment per lab/HW/whatever, but PER QUESTION for each exam question.
'''
class Assignment():
    def __init__(self, name, id, course):
        self.name = name
        self.course = course
        self.assignment_id = id
        self.rubric_id_to_qkeys = self.load_rubric_id_to_qkeys() #load from a json file
        self.rubric_id_to_total_pts = self.get_rubric_id_to_total_pts(self.rubric_id_to_qkeys)
        if "Exam 1" in self.name:
            csv_name = "data/exam1all.csv"
        elif "Exam 2" in self.name:
            csv_name = "data/exam2all.csv"
        else:
            raise ValueError(f"Could not find csv file for {self.name}")

        self.score_df = pd.read_csv(csv_name)

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
        # TODO eventually this should open the GUI to get me to match these myself. For now just hardcode
        assert False
        q3_keys = ['3.1: ai.  why did the tests pass? (1.0 pts)',
                   '3.2: aii. test that would catch character going into wall (2.0 pts)',
                   '3.3: bi. stack trace interpretation table (3.0 pts)',
                   '3.4: bii. Stack trace description (2.0 pts)',
                   '3.5: biii. editing get_next_loc (1.0 pts)',
                   '3.6: c. debugging strategy (3.0 pts)']

        unit_test_key = q3_keys[1]
        stack_trace_key1 = q3_keys[2]
        stack_trace_key2 = q3_keys[3]
        fix_code_key = q3_keys[4]

        rubric_id_to_qkeys = {
            "_8079": (unit_test_key,),
            "_8474": (fix_code_key,),
            "_3453": (stack_trace_key1, stack_trace_key2)
        }
        return rubric_id_to_qkeys



    def score_to_rubric_score(self, score):
        """Returns the score on the rubric given an assignment score."""
        if score >= 0.95:
            return 4
        elif score >= 0.75:
            return 3
        elif score >= 0.5:
            return 2
        elif score >= 0.25:
            return 1
        else:
            return 0

    def update_mastery_score_for_student(self, sid, student_data_dict):
        # Prepare the request
        student_id = student_data_dict["id"]
        submission_url = f"{self.course.PAGE_URL}/courses/{self.course.COURSE_ID}/assignments/{self.assignment_id}/submissions/{student_id}"
        student_name = student_data_dict["short_name"]
        response = requests.get(submission_url, headers=self.course.headers)

        submission_data: dict = response.json()
        if sid not in list(self.score_df["SID"]):
            #raise RuntimeError(f"Could not find student: {student_name}")
            print(f"Could not find student: {student_name}")
            return

        student_df = self.score_df.loc[self.score_df["SID"] == sid].squeeze()

        new_outcome = {
            "rubric_assessment": {}}

        total_question_score = self.compute_total_question_score(student_df)

        for rubric_id in self.rubric_id_to_qkeys:
            qkeys = self.rubric_id_to_qkeys[rubric_id]
            mastery_score = self.compute_mastery_score(rubric_id, qkeys, student_df)
            new_outcome["rubric_assessment"][str(rubric_id)] = {"points": mastery_score}

        out_response = requests.put(submission_url, headers=self.course.headers, json=new_outcome,
                                    data={"submission[posted_grade]": int(total_question_score)})
        print(f"{student_name} new outcome: {new_outcome}")
        out_response.raise_for_status()

        # Check that nothing was overwritten

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

    def compute_total_question_score(self, student_df):
        total_question_score = 0
        inferred_keys = self.infer_assignment_keys_from_df(student_df)
        for qkey in inferred_keys:
            total_question_score += student_df[qkey]
        if np.isnan(total_question_score):
            total_question_score = 0
        return  total_question_score

    def update_mastery_scores(self, student_name_match=None):
        student_data_dict = self.course.student_data_dict #read only
        for sid in student_data_dict.keys():
            if student_name_match is not None:
                if student_name_match not in student_data_dict[sid]["name"]:
                    continue
            self.update_mastery_score_for_student(int(sid), student_data_dict[sid])




    def get_subquestions_from_csv(self, filename, foldername=None):
        '''For exams specifically -- Take one gradescope CSV file for a **specific section** (contains subquestions).
            Takes in a filename and optionally the foldername that its contained in, and assigns a list of Subquestions'''
        filepath = filename
        if foldername: # if provided a folder in parameters
            filepath = os.path.join(foldername, filename)
        with open(filepath, newline="") as f:
            data = f.read()
            # split into rows by newline, and then columns by comma
            header = data.splitlines()[0].split(",")
            subq_names = header[13:] # subquestions begin at index 13
            for s in subq_names:
                subq = Subquestion(s)
                self.subquestions.append(subq) # add OBJECTS to the subquestions list

    '''checks if assignment name, without any characters is the same as a Gradescope CSV filename. returns bool'''
    def same_as_csvfile(self, csvfilename):
        # remove scores.csv at the end by chopping off 10 characters
        csvfilename = csvfilename[:-10]
        # use regular expressions to remove non-letter characters including spaces
        clean_name = re.sub(r'[^A-Za-z0-9]', '', self.name).lower()
        clean_csvname = re.sub(r'[^A-Za-z0-9]', '', csvfilename).lower()
        return (clean_name == clean_csvname)

    ''' given a foldername containing all csv files for subquestions, assign subquestions from the correct csv file'''
    def find_my_subquestions(self, foldername):
        filepath = os.path.join(os.getcwd(), foldername)
        # assign subquestions when there is a match
        for file in os.listdir(filepath):
            if self.same_as_csvfile(file):
                print("matched "+file)
                self.get_subquestions_from_csv(file, foldername)

