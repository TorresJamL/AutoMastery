import argparse

from Assignment import Assignment, make_assignment_from_name
from CourseInfo import Course


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--course_id", help="Course ID", default=80807)
    parser.add_argument( "-a", "--assignment_name", help="assignment to update")
    parser.add_argument("-s", "--student_username",  help="")
    args = parser.parse_args()


    course = Course("https://sit.instructure.com/api/v1", args.course_id, overwrite_assignment_json=True)
    assignment_id = course.find_assignment_id_by_name(args.assignment_name)
    assignment = make_assignment_from_name(args.assignment_name, assignment_id, course)
    assignment.update_mastery_scores(student_name_match=args.student_username)


if __name__ == "__main__":
    main()