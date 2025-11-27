import pandas as pd
import os

''' Takes in a list of folder names that should be in same level as this file
    and returns a dict of (we can change this btw) "exam1", "exam2"... to 
    properly formatted CSV's for each one
    The CSV's include subquestions merged over all sections
'''
def get_exams(folders):
    for folder in folders:
        folder_path = os.path.join(os.getcwd(), "exam2")

        dfs = []
        ungraded = []

        # read filenames from each csv and append a DataFrame to dfs
        for f in folder_path:
            print(f)
            temp = pd.read_csv(f) # join path from folder
            # Chop off all students whose exams are "not graded" (because they're in a diff section)
            temp = temp[temp['Status'] != 'Missing'] 
            dfs.append(temp) 

        # append all sections together
        df = pd.concat(dfs, axis=0, join='inner', ignore_index=True)







# Let's not do this for now
# add in the students with ungraded exams
#df = pd.concat([df, ungraded], axis=0, join='outer', ignore_index=True)
