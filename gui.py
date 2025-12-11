from CourseInfo import Course
from MasteryInfo import Mastery
from Assignment import Assignment, Subquestion
import tkinter as tk
from tkinter import ttk
import pandas as pd
import os

# ===--------------------- action items ----------------------------------------
# do not display subquestions without an outcome (docstrings, autograder...)
# rubric_item_iter has the rubric id (WHICH IS NOT THE SAME AS THE OUTCOME)
# each assignment has rubric items, each rubric item has a dictionary that contains fields *id, *description (name)
# to update one score with a RUBRIC you make a new dictionary with <_id> : [<subquestions>]
#   save the new dictionary to a pickl or json
# found students by CSV. to update their score we can make a new row with their score for the question
##### Try to have minimum data saved.

# FOCUS: exams -- it will be in the same df
# maybe make other assignments into DataFrames

# NEXT MVP: can create and save a dictionary of mapping rubric id to subquestions/qkeys

# ------------ class to manage states of gui --------------------------
class Manager():
    # default constructor
    def __init__(self):
        self.course = Course("https://sit.instructure.com/api/v1", 80807) # this will hold a MasteryInfo inside
        self.all_assignments = self.course.get_assignment_pairs() # dictionary with id: name
        self.mg_assignments = [] # for storing Assignment objects of those that have been edited
        self.outcomes = self.course.get_all_outcomes() # dictionary with id : name
        self.dfs = [] # holds all exam DataFrames

        self.curr_assignment = "No assignment selected" # current assignment name
        self.curr_assignment_display = tk.StringVar()
        self.curr_assignment_display.set("No assignment selected") # default display value
        self.curr_aid = None # current assignment id
        # frame that any Manager functions act on where the frame needs to hold the order in which it was created
        self.curr_frame = None 

        self.output = tk.StringVar()
        
    ''' take one list of subquestions, and one Assignment object, assigns subquestions without returning anything'''
    def set_subquestions_to_assignment(self, subquestions, assignment):
        pass

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
            # create a new Assignment object to hold information and assign its subquestions from gradescope
            self.curr_assignment = Assignment(selection)
            self.curr_assignment.find_my_subquestions('gradescopeSubquestionCsvs') # OR ADD YOUR FOLDER NAME HERE
            self.display_subquestions(self.curr_frame, self.curr_assignment)

    ''' submit whatever's in the entry box and dropdown menu to the class for the current assignment'''
    def update_rubric(self, wrubric, sid): # sid being which widget submitted you
        out = "I did not update anything" # placeholder
        if wrubric.get():
            selection = wrubric.get()
            self.curr_assignment.subquestions[sid].outcome = selection[0] # set subquestion outcome
            out= "\nI added rubric outcome "+selection[0]+" to subquestion "+self.curr_assignment.subquestions[sid].name

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
        pass
        for id in self.course.get_assignments().keys():
            # specific use when given a name, it should be "Exam 1" or "Exam 2"
            # or whatever part is contained in each Canvas assignment title
            #if assignment.name in id and type(assignment) == Exam:
                assignment.canvas_ids.append(id)

    ''' Display a single subquestion with ability to assign rubric outcome '''
    def display_subquestions(self, frame, assignment):
        # delete any widgets from previous calls
        for widget in frame.winfo_children():
            widget.destroy()

        # check if subquestions exist
        if self.curr_assignment.subquestions == []:
            self.output.set("No subquestions for this assignment")
            #manual_assign_button = tk.Button(frame, text='assign manually', command=lambda:self.curr_assignment.get_subquestions_from_csv())
        else:
            # go through and create same widgets for each subquestion
            # start stop step
            for i in range(0, len(self.curr_assignment.subquestions)*2, 2):
                title = tk.Label(frame, text=self.curr_assignment.subquestions[i//2].name)
                title.grid(row=i, column=1)
                # rubric outcome selection for the subquestion
                explanation_rubric = tk.Label(frame, text="Rubric outcome\nfor this subquestion:")
                explanation_rubric.grid(row=i+1, column=0)
                rubric_dropdown = ttk.Combobox(frame, 
                                            height=10, 
                                            width=50, 
                                            values=list(self.outcomes.values()),
                                            state = "readonly")
                rubric_dropdown.grid(row=i+1, column=1)

                # button for submitting rubric outcome. Each widget passes its index to use on the subquestions list
                brubric = tk.Button(frame, text="submit", command=lambda r=rubric_dropdown, sid=i//2: self.update_rubric(r, sid))
                brubric.grid(row=i+1, column=2)


# main window
root = tk.Tk()
root.geometry("1000x500")
# main canvas (for scrollbar)
root_canvas = tk.Canvas(root)
root_canvas.pack(side="left", fill="both", expand=True)
root_frame = tk.Frame(root_canvas)

# scrollbar functionality
scrollbar = ttk.Scrollbar(root, orient="vertical", command=root_canvas.yview)
scrollbar.pack(side="right", fill="y")
root_canvas.configure(yscrollcommand=scrollbar.set)
canvas_window = root_canvas.create_window((0, 0), window=root_frame, anchor="nw")

# update scroll region on frame change
def on_frame_configure(event):
    root_canvas.configure(scrollregion=root_canvas.bbox("all"))
root_frame.bind("<Configure>", on_frame_configure)

# --------------------------------- gui stuff --------------------
mg = Manager()

# CURRENT ASSIGNMENT HEADER
header = tk.Frame(root_frame) # For assignment name, id
header.pack()
title = tk.Label(header, text="Select an Assignment\n(you can use arrow keys and hit enter or click and use the button):")
title.pack()

# DROPDOWN OF ASSIGNMENTS -- SELECT CURRENT ASSIGNMENT
adframe = tk.Frame(root_frame)
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
qframe = tk.Frame(root_frame) 
qframe.pack()
mg.curr_frame = qframe # default current frame

# PLACEHOLDER FOR TESTING PURPOSES
mg.output.set("output")
output = tk.Label(root_frame, 
                  textvariable=mg.output, 
                  font=("Papyrus", 16), 
                  fg="purple",
                  wraplength=850)
output.pack()

# run main window
root_frame.mainloop()
