import argparse
import arrow
import canvaslms.cli
import canvaslms.hacks.canvasapi
import csv
import datetime
import re
import sys


def courses_command(config, canvas, args):
    """Prints the users list of courses in CSV format to stdout"""
    output = csv.writer(sys.stdout, delimiter=args.delimiter)

    course_list = filter_courses(canvas, args.regex)

    if not args.all:
        is_current_course = (
            lambda x: x.start_at is None
            or (
                x.end_at is None
                and arrow.get(x.start_at) - arrow.now().shift(years=-1)
                > datetime.timedelta(0)
            )
            or x.end_at is not None
            and arrow.get(x.end_at) > arrow.now()
        )
        course_list = filter(is_current_course, course_list)

    # Convert to list and check if empty
    course_list = list(course_list)
    if not course_list:
        raise canvaslms.cli.EmptyListError("No courses found matching the criteria.")

    for course in course_list:
        row = []
        if args.id:
            row.append(course.id)
        if args.ladok:
            row.append(course.sis_course_id)
        row.extend([course.course_code, course.name, course.start_at, course.end_at])
        output.writerow(row)


def filter_courses(canvas, regex):
    courses = canvas.get_courses()
    p = re.compile(regex)
    for course in courses:
        if p.search(course.name):
            yield course
        elif p.search(course.course_code):
            yield course
        elif p.search(str(course.id)):
            yield course


def add_course_option(parser, required=False, suppress_help=False):
    """Adds the -c option to argparse parser to filter out courses

    Args:
      parser: The argparse parser to add options to
      required: Whether the course option should be required
      suppress_help: If True, hide this option from help output (default: False)
    """
    parser.add_argument(
        "-c",
        "--course",
        required=required,
        default=".*",
        help=(
            argparse.SUPPRESS
            if suppress_help
            else "Regex matching courses on title, course code or Canvas ID, "
            "default: '.*'"
        ),
    )


def process_course_option(canvas, args):
    """Processes -c option, returns a list of courses"""
    course_list = filter_courses(canvas, args.course)
    course_list = list(course_list)
    if not course_list:
        raise canvaslms.cli.EmptyListError("No courses found matching the criteria.")
    return course_list


def add_command(subp):
    """Adds the subcomand and its options to argparse subparser subp"""
    courses_parser = subp.add_parser(
        "courses",
        help="Lists your courses",
        description="Lists your courses. Output, CSV-format: "
        "<canvas ID>* <SIS course ID>* <course-code> <course-name> \
         <start-time> <end-time>",
    )
    courses_parser.set_defaults(func=courses_command)
    courses_parser.add_argument(
        "regex",
        default=".*",
        nargs="?",
        help="Regex for filtering courses, default: '.*'",
    )
    courses_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        default=False,
        help="List all courses, by default list only current courses.",
    )
    courses_parser.add_argument(
        "-i",
        "--id",
        action="store_true",
        default=False,
        help="Include Canvas ID of the course as first column.",
    )
    courses_parser.add_argument(
        "-l",
        "--ladok",
        action="store_true",
        default=False,
        help="Include LADOK ID (integration ID) of the course as "
        "first (or second, with -i) column.",
    )
