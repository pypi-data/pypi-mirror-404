"""
Module that summarizes an assignment group by conjunctive average.

Conjunctive average means:

  1) We need all assignments to have a non-F grade. The grade "incomplete" is
     translated to F.

  2) If there are A--F assignments present, we will compute the average of
     those grades. For instance; an A and a C will result in a B; an A and a B
     will result in an A, but an A with two Bs will become a B (standard
     rounding).
"""

import datetime as dt
from canvaslms.cli import results
from canvasapi.exceptions import ResourceDoesNotExist


def summarize(user, assignments_list):
    """
    Extracts user's submissions for assignments in assingments_list to summarize
    results into one grade and a grade date. Summarize by conjunctive average.
    """

    pf_grades = []
    a2e_grades = []
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

        if grade in ["A", "B", "C", "D", "E"]:
            a2e_grades.append(grade)
        elif grade in ["P", "F"]:
            pf_grades.append(grade)
        elif grade.casefold() == "complete":
            pf_grades.append("P")
        elif grade.casefold() == "incomplete":
            pf_grades.append("F")
        else:
            raise ValueError(f"Unknown grade {grade} for assignment {assignment}.")
        grade_date = submission.submitted_at or submission.graded_at

        if grade_date:
            grade_date = dt.date.fromisoformat(grade_date.split("T")[0])
            dates.append(grade_date)

    if all(map(lambda x: x == "P", pf_grades)):
        final_grade = "P"
        if a2e_grades:
            final_grade = a2e_average(a2e_grades)
    else:
        final_grade = "F"

    if dates:
        final_date = max(dates)
    else:
        final_date = None
        final_grade = None

    return (final_grade, final_date, graders)


def a2e_average(grades):
    """
    Takes a list of A--E grades, returns the average.
    """
    num_grades = map(grade_to_int, grades)
    avg_grade = round(sum(num_grades) / len(grades))
    return int_to_grade(avg_grade)


def grade_to_int(grade):
    grade_map = {"E": 1, "D": 2, "C": 3, "B": 4, "A": 5}
    return grade_map[grade]


def int_to_grade(int_grade):
    grade_map_inv = {1: "E", 2: "D", 3: "C", 4: "B", 5: "A"}
    return grade_map_inv[int_grade]


def summarize_group(assignments_list, users_list):
    """
    Summarizes a particular set of assignments (assignments_list) for all
    users in users_list.
    """

    for user in users_list:
        grade, grade_date, graders = summarize(user, assignments_list)
        yield [user, grade, grade_date, *graders]
