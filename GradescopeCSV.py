import pandas as pd
from pathlib import Path
import os

''' Takes in a list of folder names that should be in same level as this file
    and returns a dict of (we can change this btw) "exam1", "exam2"... to 
    properly formatted CSV's for each one
    The CSV's include subquestions merged over all sections
'''
def merge_exams(match):
    folder_path = Path("data")

    dfs = []
    ungraded = []

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
    else:
        df.to_csv(os.path.join("data", "exam2all.csv"))




if __name__ == "__main__":
    #merge_exams("Test_2")
    merge_exams("Exam_1")




# Let's not do this for now
# add in the students with ungraded exams
#df = pd.concat([df, ungraded], axis=0, join='outer', ignore_index=True)
