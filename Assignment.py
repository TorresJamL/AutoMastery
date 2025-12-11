import re
import os

''' Class to hold data for an assignment, including questions and subquestions
    Note: Canvas assignments are one assignment per lab/HW/whatever, but PER QUESTION for each exam question.
'''
class Assignment():
    # constructor with no id for Exams since they are by question on canvas
    def __init__(self, name):
        self.name = name 
        #self.id = eid
        self.mastery_score = 0 # placeholder
        self.rubric_outcomes = []
        self.subquestions = []

    '''For exams specifically -- Take one gradescope CSV file for a **specific section** (contains subquestions).
        Takes in a filename and optionally the foldername that its contained in, and assigns a list of Subquestions'''
    def get_subquestions_from_csv(self, filename, foldername=None):
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

class Subquestion():
    def __init__(self, name):
        self.name = name
        self.outcome = None # default value
