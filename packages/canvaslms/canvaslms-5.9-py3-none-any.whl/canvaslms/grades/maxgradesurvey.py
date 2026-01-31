"""
Module that summarizes an assignment group by maximizing grade and date. This
module is the same as `canvaslms.grades.disjunctmax`, but also includes
ungraded surveys (for instance quiz with points, where the number of points is
ignored). Consequently all assignments must have a date.

This function also doen't fail when there is a grade other than A--F or P/F
present. Such grades are all treated as F.
"""

import datetime as dt
from canvaslms.grades.disjunctmax import grade_max
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
            grades.append("F")
            continue

        submission.assignment = assignment
        graders += results.all_graders(submission)

        grade = submission.grade

        if grade is None or grade not in "ABCDEPF":
            grade = "F"

        grades.append(grade)

        grade_date = submission.submitted_at or submission.graded_at

        if grade_date:
            grade_date = dt.date.fromisoformat(grade_date.split("T")[0])
            dates.append(grade_date)

    if len(dates) < len(grades):
        final_grade = "F"
    else:
        final_grade = grade_max(grades) or "F"

    if dates:
        final_date = max(dates)
    else:
        final_date = None
        final_grade = None

    return (final_grade, final_date, graders)


def summarize_group(assignments_list, users_list):
    """Summarizes a particular set of assignments (assignments_list) for all
    users in users_list"""

    for user in users_list:
        grade, grade_date, graders = summarize(user, assignments_list)
        yield [user, grade, grade_date, *graders]
