"""
Summarizes participation assignments using conjunctive P/F grading.
All assignments must have 'complete' or '100' for P, otherwise F.
"""

import datetime as dt
from canvaslms.cli import results
from canvasapi.exceptions import ResourceDoesNotExist


def is_passing_grade(grade):
    """
    Returns True if the grade indicates passing (complete or 100).
    """
    if grade is None:
        return False
    if isinstance(grade, str):
        if grade.casefold() == "complete":
            return True
        if grade == "100":
            return True
    return False


def summarize(user, assignments_list):
    """
    Extracts user's submissions for all participation assignments.
    Returns (grade, date, graders) where grade is P if all passed, F otherwise.
    """
    passed = []
    dates = []
    graders = []

    for assignment in assignments_list:
        try:
            submission = assignment.get_submission(user, include=["submission_history"])
        except ResourceDoesNotExist:
            passed.append(False)
            continue

        submission.assignment = assignment
        grade = submission.grade
        passed.append(is_passing_grade(grade))
        graders += results.all_graders(submission)
        grade_date = submission.submitted_at or submission.graded_at
        if grade_date:
            grade_date = dt.date.fromisoformat(grade_date.split("T")[0])
            dates.append(grade_date)

    if dates:
        final_date = max(dates)
        if all(passed):
            final_grade = "P"
        else:
            final_grade = "F"
    else:
        final_date = None
        final_grade = None

    return (final_grade, final_date, graders)


def summarize_group(assignments_list, users_list):
    """
    Summarizes participation assignments using conjunctive P/F grading.
    All assignments must have 'complete' or '100' for P, otherwise F.
    """
    for user in users_list:
        grade, grade_date, graders = summarize(user, assignments_list)
        yield [user, grade, grade_date, *graders]
