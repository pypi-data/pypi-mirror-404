"""
Module that summarizes an assignment group by disjunctive maximum.

Disjunctive maximum means:

  1) At least one assignment must have a non-F grade.
  2) If there are more than one assignment with a non-F grade, we take the
     maximum as the grade. A--E are valued higher than P. The grade F is valued
     the lowest.

We fail if there is an assignment which doesn't have A--F or P/F grading
scales.

This way of summarizing a grade is useful when there is an exam assignment, and
for each opportunity to take the exam there is a separate copy of the
assignment.
"""

import datetime as dt
from canvaslms.cli import results
from canvasapi.exceptions import ResourceDoesNotExist


def summarize(user, assignments_list):
    """Extracts user's submissions for assignments in assingments_list to
    summarize results into one grade and a grade date. Summarize by disjunctive
    maximum."""

    grades = []
    dates = []
    graders = []

    for assignment in assignments_list:
        try:
            submission = assignment.get_submission(user, include=["submission_history"])
        except ResourceDoesNotExist:
            pf_grades.append("F")
            continue

        submission.assignment = assignment
        graders += results.all_graders(submission)

        grade = submission.grade

        if grade is None:
            grade = "F"

        grades.append(grade)

        grade_date = submission.submitted_at or submission.graded_at

        if grade_date:
            grade_date = dt.date.fromisoformat(grade_date.split("T")[0])
            dates.append(grade_date)

    if grades:
        final_grade = grade_max(grades) or "F"
    else:
        final_grade = "F"

    if dates:
        final_date = max(dates)
    else:
        final_date = None
        final_grade = None

    return (final_grade, final_date, graders)


def grade_max(grades):
    """Takes a list of A--E/P--F grades, returns the maximum."""
    num_grades = list(map(grade_to_int, grades))

    if num_grades:
        max_grade = max(num_grades)
        return int_to_grade(max_grade)

    return None


def grade_to_int(grade):
    grade_map = {"F": -2, "Fx": -1, "P": 0, "E": 1, "D": 2, "C": 3, "B": 4, "A": 5}
    return grade_map[grade]


def int_to_grade(int_grade):
    grade_map_inv = {-2: "F", -1: "Fx", 0: "P", 1: "E", 2: "D", 3: "C", 4: "B", 5: "A"}
    return grade_map_inv[int_grade]


def summarize_group(assignments_list, users_list):
    """Summarizes a particular set of assignments (assignments_list) for all
    users in users_list"""

    for user in users_list:
        grade, grade_date, graders = summarize(user, assignments_list)
        yield [user, grade, grade_date, *graders]
