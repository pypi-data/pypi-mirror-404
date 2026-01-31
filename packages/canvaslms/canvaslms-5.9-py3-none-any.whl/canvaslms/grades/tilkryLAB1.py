"""
Summarizes the assignments of LAB1 in the course DD2520 Applied Crypto at KTH.

There are some mandatory assignments graded P/F. They must all be P.

There are also some optional assigments. They're given scores between 0 and
2.5. The sum of the scores is used to determine the grade. If the sum is more
than 4, the grade is A.
"""

import datetime as dt
from canvaslms.cli import results
from canvasapi.exceptions import ResourceDoesNotExist
import logging
from math import ceil


def summarize(user, assignments_list):
    """
    Extracts user's submissions for assignments in assingments_list to summarize
    results into one grade and a grade date.

    Summarize according to tilkry grading scheme.
    """

    mandatory = []
    optional = []
    dates = []
    graders = []

    for assignment in assignments_list:
        try:
            submission = assignment.get_submission(user, include=["submission_history"])
        except ResourceDoesNotExist:
            if not is_optional(assignment):
                mandatory.append("F")
            continue

        submission.assignment = assignment
        graders += results.all_graders(submission)

        grade = submission.grade

        if is_optional(assignment):
            if grade is None:
                continue
            try:
                grade = float(grade)
                optional.append(grade)
            except ValueError:
                logging.warning(
                    f"Invalid grade {grade} for {user} in {assignment}, " "skipping."
                )
                continue
        else:
            if grade is None:
                grade = "F"
            elif grade == "P+":
                grade = "P"
            elif grade not in "PF":
                logging.warning(
                    f"Invalid grade {grade} for {user} in {assignment}, " "using F"
                )
                grade = "F"
            mandatory.append(grade)

        grade_date = submission.submitted_at or submission.graded_at

        if grade_date:
            grade_date = dt.date.fromisoformat(grade_date.split("T")[0])
            dates.append(grade_date)

    if not all(grade == "P" for grade in mandatory):
        final_grade = "F"
    else:
        if sum(optional) >= 4:
            final_grade = "A"
        elif ceil(sum(optional)) >= 3:
            final_grade = "B"
        elif ceil(sum(optional)) >= 2:
            final_grade = "C"
        elif ceil(sum(optional)) >= 1:
            final_grade = "D"
        else:
            final_grade = "E"

    if dates:
        final_date = max(dates)
    else:
        final_date = None
        final_grade = None

    return (final_grade, final_date, graders)


def is_optional(assignment):
    assignment_name = assignment.name.casefold()
    return assignment_name.startswith("optional:") or assignment_name.startswith(
        "(optional)"
    )


def summarize_group(assignments_list, users_list):
    """
    Summarizes a particular set of assignments (assignments_list) for all
    users in users_list
    """

    for user in users_list:
        grade, grade_date, graders = summarize(user, assignments_list)
        yield [user, grade, grade_date, *graders]
