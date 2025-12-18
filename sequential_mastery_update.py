import argparse

from Assignment import Assignment, make_assignment_from_name
from CourseInfo import Course


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--course_id", help="Course ID", default=80807)
    parser.add_argument("-s", "--student_name_match",  help="")
    args = parser.parse_args()


    course = Course("https://sit.instructure.com/api/v1", args.course_id, overwrite_assignment_json=True)
    assignments_by_order = [
           #"Lab 2",
           #"Lab 3",
           #"Homework 2",
           "Lab 4",
           "Exam 1 Question 1",
           "Exam 1 Question 2",
           "Exam 1 Question 3",
           "Exam 1 Question 4",
           "Lab 5",
        "Lab 6",
        "Lab 7",
        "Homework 4",
        "Lab 8",
        #"Exam 2 Question 1",
        "Exam 2 Question 2",
        "Exam 2 Question 4",
        "Exam 2 Question 5",
        "Exam 2 Question 3",
        "Lab 9",
        "Lab 10",
        "Homework 5",
        "Lab 11",
        "Exam 3 Question 1",
        "Exam 3 Question 2",
        "Exam 3 Question 3",
    ]
    for assignment_name in assignments_by_order:
        assignment_id = course.find_assignment_id_by_name(assignment_name)
        assignment = make_assignment_from_name(assignment_name, assignment_id, course)
        print(f"Updating assignment {assignment_name}")

        assignment.update_mastery_scores(student_name_match=args.student_name_match)
        print(f"Updated mastery scores for assignment {assignment_name}")


if __name__ == "__main__":
    main()
