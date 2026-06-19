import requests

from Assignment import Assignment, make_assignment_from_name
from pathlib import Path
import pandas as pd
import argparse
from CourseInfo import Course
from data_utils import find_student_df_by_SID, StudentNotFoundError


def load_participation_tracking():
    participation_fn = "Participation tracking - Sheet1.csv"
    participation_grade_csv_path = Path("data")/ participation_fn
    participation_df = pd.read_csv(participation_grade_csv_path)
    participation_df.rename(columns={"ID": "SID"}, inplace=True)
    participation_df["SID"] = pd.to_numeric(participation_df["SID"], errors="coerce").astype("Int64")
    return participation_df

def load_exam_alternative():
    exam_grade_csv = Path("data")/ "exam3all.csv"
    exam_df = pd.read_csv(exam_grade_csv)
    return exam_df

def get_participation_grade(student_participation_df):
    return student_participation_df["Inputted grade"]

def get_exam_grade_percentage(student_exam_df):
    return student_exam_df["Total Score"]/student_exam_df["Max Points"]

def get_participation_or_exam_grade_for_student(sid, student_data_dict, participation_df, exam_df):
    student_participation_df = find_student_df_by_SID(participation_df, sid, student_data_dict["name"])
    participation_points = 5 # should probably be in a config file somewhere
    participation_selection = student_participation_df["Graded?"]
    if not pd.isna(participation_selection) and "Part" in participation_selection:
        participation_grade = get_participation_grade(student_participation_df)
        print(participation_grade)
        if not pd.isna(participation_grade) and participation_grade is not None:
            assert participation_grade <= participation_points
            print("Using participation grade")
            return participation_grade
        else:
            student_name = student_data_dict["name"]
            print(f"Could not find participation grade for student {student_name}")
    try:
        student_exam_df = find_student_df_by_SID(exam_df, sid, student_data_dict["name"])
    except StudentNotFoundError:
        return 0
    exam_score = get_exam_grade_percentage(student_exam_df)
    print("Using exam grade")
    return round(participation_points * exam_score, 0)


def update_participation_grade_for_student(course, sid, student_data_dict, participation_df, exam_df):
    score = get_participation_or_exam_grade_for_student(sid, student_data_dict, participation_df, exam_df)
    assignment_id = course.find_assignment_id_by_name("Participation grade or Exam 3 scaled to 5")
    student_id = student_data_dict["id"]
    submission_url = f"{course.PAGE_URL}/courses/{course.COURSE_ID}/assignments/{assignment_id}/submissions/{student_id}"
    #bulk_url = f"{course.PAGE_URL}/courses/{course.COURSE_ID}/assignments/{assignment_id}/submissions/update_grades"

    #payload = {
    #    f"grade_data[{student_id}][posted_grade]": str(score)
    #}

    #resp = requests.post(
    #    bulk_url,
    #    headers=course.headers,
    #    data=payload
    #)
    #resp.raise_for_status()
    #print(resp.json())

    student_name = student_data_dict["short_name"]
    #print(f"Would update score for {student_name} to {score}")
    empty_dict = {}#{"rubric_assessment": {}}
    out_response = requests.put(submission_url, headers=course.headers, json=empty_dict)
    out_response.raise_for_status()

    out_response = requests.put(submission_url, headers=course.headers,json=empty_dict,
                                data={"submission[posted_grade]": str(int(score))})
    res = str(int(score))
    out_response.raise_for_status()
    print(out_response.text)

def main(args):
    course = Course("https://sit.instructure.com/api/v1", args.course_id, overwrite_assignment_json=True)
    participation_df = load_participation_tracking()
    exam_df = load_exam_alternative()
    student_data_dict = course.student_data_dict  # read only
    for sid in student_data_dict.keys():
        if args.student_name_match is not None:
            if args.student_name_match not in student_data_dict[sid]["name"]:
                continue
        update_participation_grade_for_student(course,
                                               sid,
                                               student_data_dict[sid],
                                               participation_df,
                                               exam_df)



    # Find student from Canvas

    # find student on the datasheet
    # Find student's score based on Exam 3 and participation



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--course_id", help="Course ID", default=80807)
    parser.add_argument("-s", "--student_name_match",  help="")
    args = parser.parse_args()
    main(args)

