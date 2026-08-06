import os
from pathlib import Path
import pandas as pd
# Eventually this goes into a single json file per assignment
def assignment_match_to_csv_name(name):
    if "Exam 1" in name:
        csv_name = "exam1bestof.csv"
    elif "Exam 2" in name:
        csv_name = "exam2bestof.csv"
    elif "Exam 3" in name:
        csv_name = "exam3bestof.csv"
    elif "Homework 2" in name:
        csv_name = "Homework_2_Morse_Code_scores.csv"
    elif "Homework 3" in name:
        csv_name = "Homework_3_Navigating_a_City_Grid_scores.csv"
    elif "Homework 4" in name:
        csv_name = "Homework_4_ASCII_Image_Rendering_scores.csv"
    elif "Homework 5" in name:
        csv_name = "Homework_5_Robots_versus_Zombies_Object_Oriented_Programming__scores.csv"
    elif "Test 1" in name:
        csv_name =  "Test_1_scores.csv"
    else:
        raise ValueError(f"Could not find csv file for {name}")
    return Path("data") / csv_name

def find_student_df_by_SID(df, sid, student_name ="Student name not included"):
    assert pd.api.types.is_integer_dtype(df["SID"])
    if int(sid) not in list(df["SID"]):
        raise StudentNotFoundError(f"Could not find student: {student_name}")
    student_df = df.loc[df["SID"] == int(sid)].squeeze()
    return student_df

def find_csv_in_dir(dir):
    for file in os.listdir(dir):
        if file.endswith(".csv"):
            file_path = os.path.join(dir, file)
            return file_path
    else:
        raise ValueError(f"Could not find csv file for {dir}")

class StudentNotFoundError(RuntimeError):
    pass

class RubricNotFoundError(RuntimeError):
    def __str__(self):
        return f"Could not find Rubric on Canvas for {self}. Please add one to the Canvas assignment and add at least one outcome"

class StudentSubmissionNotFoundError(RuntimeError):
    pass
