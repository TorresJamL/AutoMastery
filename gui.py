from CourseInfo import Course
from MasteryInfo import Mastery
from Assignment import Assignment, Exam
import tkinter as tk
from tkinter import ttk

# ------------ class to manage states of gui --------------------------
class Manager():
    # default constructor
    def __init__(self):
        self.course = Course("https://sit.instructure.com/api/v1", 80807) # this will hold a MasteryInfo inside
        self.all_assignments = self.course.get_assignment_pairs() # dictionary with id: name
        self.mg_assignments = [] # for storing Assignment objects of those that have been edited
        self.outcomes = self.course.get_all_outcomes() # dictionary with id : name

        self.curr_assignment = "No assignment selected" # current assignment name
        self.curr_assignment_display = tk.StringVar()
        self.curr_assignment_display.set("No assignment selected") # default display value
        self.curr_aid = None # current assignment id
        # frame that any Manager functions act on where the frame needs to hold the order in which it was created
        self.curr_frame = None 

        self.output = tk.StringVar()

    ''' Add items from an iterable into the dropdown menu called listbox to the bottom of the dropdown'''
    def set_values_in_dropdown(self, listbox, values):
        for v in values:
            # add to the BOTTOM of the dropdown
            listbox.insert(tk.END, v) 

    ''' returns the item that was selected in the dropdown menu 
        can be used by pressing enter on a selected item, for convenience'''
    def submit_assignment_selection(self, listbox):
        if listbox.curselection():
            selection = listbox.get(listbox.curselection()[0])
            self.curr_assignment_display.set(selection)
            # create a new Assignment object to hold information
            self.curr_assignment = Assignment(selection, self.get_id_by_name(selection, self.outcomes))
            self.display_assignments(self.curr_frame, self.curr_assignment)

    ''' submit whatever's in the entry box and dropdown menu to the class for the current assignment'''
    def update_rubric_and_score(self, wscore, wrubric):
        out = "I did not update anything" # PLACEHOLDER?
        if wscore.get():
            try:
                selection = int(wscore.get())
                self.curr_assignment.mastery_score = selection
                out = "I added mastery score "+str(selection)+" to assignment "+self.curr_assignment.name # PLACEHOLDER
            except:
                self.output.set("Input a number to mastery score")
    
        if wrubric.get():
            selection = wrubric.get()
            self.curr_assignment.rubric_outcome = selection
            out+= "\nI added rubric outcome "+selection[0]+" to assignment "+self.curr_assignment.name

        self.output.set(out) # update debugger/success message

    ''' reverse lookup a dictionary (e.g. assignment_pairs) to get id from name'''
    def get_id_by_name(self, name, dictt):
        for v in dictt.values():
            if v == name:
                return dictt.keys()[dictt.index(v)] 

    ''' Save all Canvas assignment ids for an exam since there are assignments
        per question on Canvas
    '''
    def get_ids(self, assignment):
        for id in self.course.get_assignments().keys():
            # specific use when given a name, it should be "Exam 1" or "Exam 2"
            # or whatever part is contained in each Canvas assignment title
            if assignment.name in id and type(assignment) == Exam:
                assignment.canvas_ids.append(id)

    ''' Display selected assignment '''
    def display_assignments(self, frame, assignment):
        # delete any widgets from previous calls
        for widget in frame.winfo_children():
            widget.destroy()

        title = tk.Label(frame, textvariable=self.curr_assignment_display)
        title.grid(row=0, column=1)
        # mastery score for the student (placeholder: imagine there is a student)
        explanation_score = tk.Label(frame, text="Student's overall\nmastery score\nfor this assignment: ")
        explanation_score.grid(row=1, column=0)
        escore = tk.Entry(frame)
        escore.grid(row=1, column=1)
        # rubric outcome selection for assignment
        explanation_rubric = tk.Label(frame, text="Rubric outcome\nfor this assignment:")
        explanation_rubric.grid(row=2, column=0)
        rubric_dropdown = ttk.Combobox(frame, 
                                       height=10, 
                                       width=50, 
                                       values=list(self.outcomes.values()),
                                       state = "readonly")
        rubric_dropdown.grid(row=2, column=1)

        # button for submitting mastery score and rubric outcome
        brubric = tk.Button(frame, text="submit all", command=lambda: self.update_rubric_and_score(escore, rubric_dropdown))
        brubric.grid(row=2, column=2)


# main window
root = tk.Tk()
root.geometry("1000x500")

# --------------------------------- gui stuff --------------------
mg = Manager()

# CURRENT ASSIGNMENT HEADER
header = tk.Frame(root) # For assignment name, id
header.pack()
title = tk.Label(header, text="Select an Assignment\n(you can use arrow keys and hit enter or click and use the button):")
title.pack()

# DROPDOWN OF ASSIGNMENTS -- SELECT CURRENT ASSIGNMENT
adframe = tk.Frame(root)
adframe.pack()
assignment_dropdown = tk.Listbox(adframe, height=10, width=100)
assignment_dropdown.pack()
# allows user to hit enter on selected item (KEYBIND)
assignment_dropdown.bind("<Return>", lambda event: mg.submit_assignment_selection(event.widget)) 
mg.set_values_in_dropdown(assignment_dropdown, mg.all_assignments.values())
# alternatively, press a BUTTON to submit your selection
adbutton = tk.Button(adframe, text="Submit", command = lambda: mg.submit_assignment_selection(assignment_dropdown))
adbutton.pack(side="right")

# LAYOUT OF QUESTIONS -- ONCE AN ASSIGNMENT IS SELECTED, YOU CAN ASSIGN SCORES/RUBRIC OUTCOME
qframe = tk.Frame(root) 
qframe.pack()
mg.curr_frame = qframe # default current frame

# PLACEHOLDER FOR TESTING PURPOSES
mg.output.set("output")
output = tk.Label(root, 
                  textvariable=mg.output, 
                  font=("Papyrus", 16), 
                  fg="purple",
                  wraplength=850)
output.pack()

# run main window
root.mainloop()
