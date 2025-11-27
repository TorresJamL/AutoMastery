''' Class to hold data for an assignment, including questions and subquestions
    Note: Canvas assignments are one assignment per lab/HW/whatever, but PER QUESTION for each exam question.
'''
class Assignment():
    # constructor with no id for Exams since they are by question on canvas
    def __init__(self, name, eid):
        self.name = name 
        self.id = eid
        self.mastery_score = 0 # placeholder
        self.rubric_outcome = None

class Exam(Assignment):
    def __init__(self, name):
        super().__init__(name) # we will be using the name for personal id purposes
        self.questions = []
        # since exam questions are stored separately on Canvas, let's group all IDs together
        self.canvas_ids = []

    ''' Add sub questions from Gradescope CSV to self attribute.'''
    def assign_questions(self, df):
        for col in df[14:]: # index 14 is where the questions start
            self.questions.append(col)
