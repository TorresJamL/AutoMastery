from gradescope import *

gs = Gradescope(username, pwd)

def get_course_by_name(courses, course_name):
    for course in courses:
        if course_name in course.full_name:
            print(course.full_name)
            return course
    raise ValueError(f"Could not find course name:  {course_name}")

def get_assignment_by_name(assignments, assignment_name):
    for assignment in assignments:
        if assignment_name in assignment.title:
            return assignment
    raise ValueError(f"Could not find assignment name:  {assignment_name}")

course_name = "115"
courses = gs.get_courses(role=Role.INSTRUCTOR)
course = get_course_by_name(courses, course_name)

assignments = gs.get_assignments(course)
assignment_name = "Test 2"
assignment = get_assignment_by_name(assignments, assignment_name)


# courses:
# [Course(
#    course_id=123456,
#    url='/courses/123456',
#    role='instructor',
#    term='Spring 2024',
#    short_name='Math 2B',
#    full_name='Math 2B: Calculus'
# ), ...]

# assignments:
# [Assignment(
#    assignment_id=654321,
#    assignment_type='assignment',
#    url='/courses/123456/assignments/654321',
#    title='Assignment 1',
#    container_id=None,
#    versioned=False,
#    version_index=None,
#    version_name=None,
#    total_points='100.0',
#    student_submission=True,
#    created_at='Apr 01',
#    release_date='2024-04-01T00:00',
#    due_date='2024-04-07T23:59',
#    hard_due_date='2024-04-10T23:59',
#    time_limit=None,
#    active_submissions=250,
#    grading_progress=100,
#    published=True,
#    regrade_requests_open=False,
#    regrade_requests_possible=True,
#    regrade_request_count=0,
#    due_or_created_at_date='2024-04-07T23:59'
# ), ...]

members = gs.get_members(courses[0])
# members:
# [Member(
#    member_id='112233',
#    full_name='Peter Anteater',
#    first_name='Peter',
#    last_name='Anteater',
#    role='0',
#    sid='1234567890',
#    email='uci.mascot@uci.edu'
# ), ...]

past_submissions = gs.get_past_submissions(courses[0], assignments[0], members[0])
# past_submissions:
# [Submission(
#    course_id=123456,
#    assignment_id=654321,
#    member_id='112233',
#    submission_id=987654321,
#    created_at='2024-04-07T12:34:56.655388-07:00',
#    score=55.55,
#    url='/courses/123456/assignments/654321/submissions/987654321'
# ), ...]

gradebook = gs.get_gradebook(courses[0], members[0])
save_json('./gradebook.json', gradebook, encoder=EnhancedJSONEncoder)

grades_csv = gs.get_assignment_grades(assignments[0])
save_csv('./assignment_grades.csv', grades_csv)

#gs.download_file('./submission.zip', past_submission[-1].get_file_url())
