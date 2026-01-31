import canvaslms.cli
from canvaslms.cli import assignments, courses, modules, submissions, users
import canvaslms.cli.utils
import canvaslms.hacks.canvasapi

import argparse
import csv
import canvasapi.submission
import datetime as dt
import importlib
import importlib.machinery
import importlib.util
import os
import pathlib
import pkgutil
import re
import sys

PASSING_REGEX = r"^([A-EP]|complete)$"
ALL_GRADES_REGEX = r"^([A-FP]x?|(in)?complete)$"


def results_command(config, canvas, args):
    output = csv.writer(sys.stdout, delimiter=args.delimiter)

    if args.assignment_group != "":
        results = summarize_assignment_groups(canvas, args)
    elif hasattr(args, "module") and args.module != "":
        results = summarize_modules(canvas, args)
    else:
        results = summarize_assignments(canvas, args)

    # Convert to list and check if empty
    results = list(results)
    if not results:
        raise canvaslms.cli.EmptyListError("No results found matching the criteria")

    for result in results:
        output.writerow(result)


def filter_grade(grade, regex):
    """
    Returns True if the grade matches the regex.
    """
    return re.search(regex, grade)


def summarize_assignments(canvas, args):
    """
    Turn submissions into results:
    - canvas is a Canvas object,
    - args is the command-line arguments, as parsed by argparse.
    """

    assignments_list = assignments.process_assignment_option(canvas, args)
    users_list = users.process_user_or_group_option(canvas, args)

    submissions_list = submissions.filter_submissions(
        submissions.list_submissions(assignments_list, include=["submission_history"]),
        users_list,
    )

    for submission in submissions_list:
        if submission.grade is not None:
            if filter_grade(submission.grade, args.filter_grades):
                yield [
                    submission.assignment.course.course_code,
                    submission.assignment.name,
                    submission.user.integration_id,
                    submission.grade,
                    round_to_day(submission.submitted_at or submission.graded_at),
                    *all_graders(submission),
                ]


def round_to_day(timestamp):
    """
    Takes a Canvas timestamp and returns the corresponding datetime.date object.
    """
    return dt.date.fromisoformat(timestamp.split("T")[0])


def all_graders(submission):
    """
    Returns a list of everyone who participated in the grading of the submission.
    I.e. also those who graded previous submissions, when submission history is
    available.
    """
    graders = []

    for prev_submission in submission.submission_history:
        prev_submission = canvasapi.submission.Submission(
            submission._requester, prev_submission
        )
        prev_submission.assignment = submission.assignment
        grader = submissions.resolve_grader(prev_submission)
        if grader:
            graders.append(grader)

    return graders


def summarize_assignment_groups(canvas, args):
    """
    Summarize assignment groups into a single grade:
    - canvas is a Canvas object,
    - args is the command-line arguments, as parsed by argparse.
    """

    courses_list = courses.process_course_option(canvas, args)
    all_assignments = list(assignments.process_assignment_option(canvas, args))
    users_list = set(users.process_user_or_group_option(canvas, args))

    for course in courses_list:
        ag_list = assignments.filter_assignment_groups(course, args.assignment_group)

        for assignment_group in ag_list:
            assignments_list = list(
                assignments.filter_assignments_by_group(
                    assignment_group, all_assignments
                )
            )
            if args.missing:
                if args.missing:
                    try:
                        missing = load_module(args.missing)
                    except Exception as err:
                        canvaslms.cli.err(
                            1,
                            f"Error loading missing module " f"'{args.missing}': {err}",
                        )
                if missing.missing_assignments == missing_assignments:
                    missing_results = missing.missing_assignments(
                        assignments_list,
                        users_list,
                        passing_regex=args.filter_grades,
                        optional_assignments=args.optional_assignments,
                    )
                else:
                    missing_results = missing.missing_assignments(
                        assignments_list, users_list
                    )
                for user, assignment, reason in missing_results:
                    yield [
                        course.course_code,
                        assignment_group.name,
                        user.login_id,
                        assignment.name,
                        reason,
                    ]
            else:
                try:
                    summary = load_module(args.summary_module)
                except Exception as err:
                    canvaslms.cli.err(
                        1,
                        f"Error loading summary module "
                        f"'{args.summary_module}': {err}",
                    )
                for user, grade, grade_date, *graders in summary.summarize_group(
                    assignments_list, users_list
                ):
                    if (
                        grade is None
                        or grade_date is None
                        or not filter_grade(grade, args.filter_grades)
                    ):
                        continue
                    yield [
                        course.course_code,
                        assignment_group.name,
                        user.integration_id,
                        grade,
                        grade_date,
                        *graders,
                    ]


def summarize_modules(canvas, args):
    """
    Summarize modules into a single grade:
    - canvas is a Canvas object,
    - args is the command-line arguments, as parsed by argparse.
    """

    courses_list = courses.process_course_option(canvas, args)
    all_assignments = list(assignments.process_assignment_option(canvas, args))
    users_list = set(users.process_user_or_group_option(canvas, args))

    for course in courses_list:
        module_list = modules.filter_modules(course, args.module)

        for module in module_list:
            assignments_list = list(
                modules.filter_assignments_by_module(module, all_assignments)
            )
            if args.missing:
                if args.missing:
                    try:
                        missing = load_module(args.missing)
                    except Exception as err:
                        canvaslms.cli.err(
                            1,
                            f"Error loading missing module " f"'{args.missing}': {err}",
                        )
                if missing.missing_assignments == missing_assignments:
                    missing_results = missing.missing_assignments(
                        assignments_list,
                        users_list,
                        passing_regex=args.filter_grades,
                        optional_assignments=args.optional_assignments,
                    )
                else:
                    missing_results = missing.missing_assignments(
                        assignments_list, users_list
                    )
                for user, assignment, reason in missing_results:
                    yield [
                        course.course_code,
                        module.name,
                        user.login_id,
                        assignment.name,
                        reason,
                    ]
            else:
                try:
                    summary = load_module(args.summary_module)
                except Exception as err:
                    canvaslms.cli.err(
                        1,
                        f"Error loading summary module "
                        f"'{args.summary_module}': {err}",
                    )
                for user, grade, grade_date, *graders in summary.summarize_group(
                    assignments_list, users_list
                ):
                    if (
                        grade is None
                        or grade_date is None
                        or not filter_grade(grade, args.filter_grades)
                    ):
                        continue
                    yield [
                        course.course_code,
                        module.name,
                        user.integration_id,
                        grade,
                        grade_date,
                        *graders,
                    ]


def list_grading_modules():
    """
    Discover available grading modules in canvaslms.grades package.
    Returns a list of (module_name, description) tuples.
    """
    import canvaslms.grades

    modules = []
    # These are internal modules, not user-facing grading strategies
    excluded = {"__init__", "grades"}

    for importer, modname, ispkg in pkgutil.iter_modules(canvaslms.grades.__path__):
        if modname in excluded:
            continue
        try:
            module = importlib.import_module(f"canvaslms.grades.{modname}")
            doc = module.__doc__
            if doc:
                # Take only the first line of the docstring
                first_line = doc.strip().split("\n")[0]
            else:
                first_line = "(no description)"
            modules.append((modname, first_line))
        except ImportError:
            continue

    return sorted(modules)


def format_grading_modules_help():
    """Format the list of grading modules for help text display."""
    modules = list_grading_modules()
    if not modules:
        return "  (no modules found)"

    lines = []
    for name, desc in modules:
        lines.append(f"  canvaslms.grades.{name}: {desc}")
    return "\n\n".join(lines)


def format_results_epilog():
    """
    Build the epilog for results command help.

    We construct the epilog by joining lines explicitly rather than using a
    triple-quoted string. This avoids indentation issues when black formats
    the generated Python code---triple-quoted strings in function arguments
    get continuation-line indentation that RawDescriptionHelpFormatter
    would preserve literally.
    """
    parts = [
        "If you specify an assignment group, the results of the assignments in that",
        "group will be summarized. You can supply your own function for summarizing",
        "grades through the -S option.",
        "",
        "Available grading modules:",
        format_grading_modules_help(),
        "",
        "You can also provide a path to your own Python file with a summarize_group",
        "function.",
    ]
    return "\n".join(parts)


def load_module(module_name):
    """
    Load a module from the file system or a built-in module.
    """
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        module_path = pathlib.Path.cwd() / module_name
        module = module_path.stem

        loader = importlib.machinery.SourceFileLoader(module, str(module_path))
        spec = importlib.util.spec_from_loader(module, loader)
        module_obj = importlib.util.module_from_spec(spec)
        loader.exec_module(module_obj)
        return module_obj


def missing_assignments(
    assignments_list,
    users_list,
    passing_regex=PASSING_REGEX,
    optional_assignments=None,
):
    """
    Returns tuples of missing assignments.

    For each assignment that a student is not done with, we yield a tuple of the
    user, the assignment and the reason why the assignment is missing.

    The reason can be "not submitted" or "not graded" or "not a passing grade".

    The only reason to use a different module is if you have optional assignments.
    We only want to remind the students of the things they need to pass the course.
    We don't want to make it sound like an optional assignment is mandatory.
    """
    for user in users_list:
        for assignment in assignments_list:
            if optional_assignments:
                if any(
                    re.search(optional, assignment.name)
                    for optional in optional_assignments
                ):
                    continue
            try:
                submission = assignment.get_submission(user)
            except canvasapi.exceptions.ResourceDoesNotExist:
                continue

            if submission is None:
                yield user, assignment, "not submitted"
            elif submission.grade is None:
                if hasattr(submission, "submitted_at") and submission.submitted_at:
                    yield user, assignment, f"submitted on {canvaslms.cli.utils.format_local_time(submission.submitted_at)}, but not graded"
                else:
                    yield user, assignment, "not done"
            elif not filter_grade(submission.grade, passing_regex):
                if (
                    hasattr(submission, "submitted_at")
                    and submission.submitted_at
                    and hasattr(submission, "graded_at")
                    and submission.graded_at
                    and submission.submitted_at > submission.graded_at
                ):
                    yield user, assignment, f"not a passing grade ({submission.grade}), resubmission not graded"
                else:
                    yield user, assignment, f"not a passing grade ({submission.grade})"


def add_command(subp):
    """Adds the results command to argparse parser subp"""
    results_parser = subp.add_parser(
        "results",
        help="Lists results of a course",
        description="""Lists results of a course for export, for instance to the `ladok report` 
                     command. Output format, CSV:

                       <course code> <component code> <student ID> <grade> <grade date> <graders ...>

                     Can also export a list of missing assignment results (--missing option) that 
                     prevent the student from getting a grade. Output format, CSV:

                       <course code> <component code> <student ID> <missing assignment> <reason>

                     The reason can be "not submitted" or "not graded".""",
        epilog=format_results_epilog(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    results_parser.set_defaults(func=results_command)
    assignments.add_assignment_option(results_parser, ungraded=False)
    users.add_user_or_group_option(results_parser)
    results_parser.add_argument(
        "-F",
        "--filter-grades",
        required=False,
        action="store",
        nargs="?",
        const=ALL_GRADES_REGEX,
        default=PASSING_REGEX,
        help=f"Filter grades. By default we only output "
        f"A--Es and Ps ({PASSING_REGEX}. "
        f"If you want to include Fs ({ALL_GRADES_REGEX}), use this option. "
        f"You can also supply an optional regex to this option "
        f"to filter grades based on that.",
    )
    default_summary_module = "canvaslms.grades.conjunctavg"
    results_parser.add_argument(
        "-S",
        "--summary-module",
        required=False,
        default=default_summary_module,
        help=f"""Name of Python module or file to load with a custom summarization function.
             Default: `{default_summary_module}`. Available modules: """
        + ", ".join(m[0] for m in list_grading_modules())
        + """. \
             Or provide a path to your own Python file.""",
    )
    default_missing_module = "canvaslms.cli.results"
    results_parser.add_argument(
        "--missing",
        required=False,
        nargs="?",
        const=default_missing_module,
        default=None,
        help="Produce a list of missing assignments instead of grades. "
        "You can supply a custom module to this option, the module must "
        "contain a "
        "function `missing_assignments(assignments_list, users_list). "
        "The default module checks if all things are graded or submitted. "
        "This option only has effect when working with assignment groups.",
    )
    results_parser.add_argument(
        "-O",
        "--optional-assignments",
        required=False,
        nargs="+",
        default=[
            "^Optional:",
        ],
        help="List of regexes matching optional assignments. The default missing "
        "assignments will treat matching assignments as optional.",
    )
