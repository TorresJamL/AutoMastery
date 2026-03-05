import pandas as pd
from pathlib import Path
import os

def merge_exams(match):
    """
    Saves an examNall.csv from an input CSV that matches a particular string, match
    corresponding to Test or Exam N

    Designed for when there are multiple CSVs for a single test.

    Args:
    match: The name of the exam to match in the original CSV file

    Does not return anything
    """
    folder_path = Path("data")
    dfs = []

    # read filenames from each csv and append a DataFrame to dfs
    for f in os.listdir(folder_path):
        if match not in f:
            continue
        if "all" in f:
            continue
        if not f.endswith(".csv"):
            continue
        print(f)
        temp = pd.read_csv(folder_path / f) # join path from folder
        # Chop off all students whose exams are "not graded" (because they're in a diff section)
        temp = temp[temp['Status'] != 'Missing']
        dfs.append(temp)

    # append all sections together
    df = pd.concat(dfs, axis=0, join='inner', ignore_index=True)
    if "Exam_1" in match:
        df.to_csv(os.path.join("data", "exam1all.csv"))
    elif "Test_2" in match:
        df.to_csv(os.path.join("data", "exam2all.csv"))
    elif "Test_3" in match:
        df.to_csv(os.path.join("data", "exam3all.csv"))
    else:
        raise ValueError("Count not find file for match")




if __name__ == "__main__":
    exams_to_merge = ["Exam_1", "Test_2", "Test_3"]


