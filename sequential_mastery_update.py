import argparse

from Assignment import Assignment
from CourseInfo import Course


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--course_id", help="Course ID", default=80807)
    parser.add_argument("-s", "--student_username",  help="")
    args = parser.parse_args()


    course = Course("https://sit.instructure.com/api/v1", args.course_id, overwrite_assignment_json=True)
    assignments_by_order = []
    for assignment_name in assignments_by_order:
        assignment_id = course.find_assignment_id_by_name(assignment_name)
        assignment = Assignment(args.assignment_name, assignment_id, course)
        assignment.update_mastery_scores(student_name_match=args.student_username)


if __name__ == "__main__":
    main()