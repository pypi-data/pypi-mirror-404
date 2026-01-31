import argparse
import canvasapi.course
import canvasapi.exceptions
import canvasapi.group
import canvaslms.cli
import canvaslms.cli.courses as courses
import canvaslms.hacks.canvasapi
import csv
import operator
import re
import sys


def add_users_command(subp):
    """Adds the users subcommand and its options to argparse subparser subp"""
    users_parser = subp.add_parser(
        "users",
        help="Lists users of a course",
        description="Lists users of a course(s). Output, CSV-format: "
        "<course> [<group>] [<Canvas ID>] <login ID> [<LADOK ID>] "
        "<name> [<email>]",
    )
    users_parser.set_defaults(func=users_command)
    courses.add_course_option(users_parser)
    add_group_option(users_parser)
    users_parser.add_argument(
        "-s", "--students", action="store_true", help="Include students."
    )
    users_parser.add_argument(
        "-a", "--assistants", action="store_true", help="Include teaching assistants."
    )
    users_parser.add_argument(
        "-i", "--canvas-id", action="store_true", help="Include Canvas identifier"
    )
    users_parser.add_argument(
        "-l", "--ladok", action="store_true", help="Include LADOK identifier"
    )
    users_parser.add_argument(
        "-S",
        "--split-name",
        action="store_true",
        help="Returns first and last names as separate fields, "
        "instead of one containing the full name.",
    )
    users_parser.add_argument(
        "-e", "--email", action="store_true", help="Include email address"
    )
    users_parser.add_argument(
        "regex",
        default=".*",
        nargs="?",
        help="Regex for filtering users, default: '.*'",
    )


def users_command(config, canvas, args):
    roles = []
    if args.students:
        roles.append("student")
    if args.assistants:
        roles.append("ta")
    output = csv.writer(sys.stdout, delimiter=args.delimiter)

    if args.group or args.category:
        rows = make_user_rows_w_groups(canvas, args, roles)
    else:
        rows = make_user_rows(canvas, args, roles)

    # Convert to list and check if empty
    rows = list(rows)
    if not rows:
        raise canvaslms.cli.EmptyListError("No users found matching the criteria")

    for row in rows:
        output.writerow(row)


def make_user_rows(canvas, args, roles):
    """Takes a list of courses and returns a list of users in those courses"""

    course_list = courses.process_course_option(canvas, args)

    users = filter_users(course_list, args.regex, roles)

    for user in users:
        try:
            row = []
            row.append(user.course.course_code)
            if args.canvas_id:
                row.append(user.id)
            try:
                row.append(user.login_id)
            except AttributeError:
                row.append(None)
            if args.ladok:
                try:
                    row.append(user.integration_id)
                except AttributeError:
                    row.append(None)
            if args.split_name:
                lastnames, firstnames = user.sortable_name.split(", ")
                row.append(firstnames.strip())
                row.append(lastnames.strip())
            else:
                row.append(user.name)
            if args.email:
                try:
                    row.append(user.email)
                except AttributeError:
                    row.append(None)
        except AttributeError as err:
            canvaslms.cli.warn(f"skipped {user}: {err}")
            continue

        yield row


def make_user_rows_w_groups(canvas, args, roles):
    """Takes a list of courses and returns a list of users in those courses,
    includes a group column"""

    groups = process_group_options(canvas, args)

    for group in groups:
        users = filter_users([group], args.regex, roles)

        for user in users:
            try:
                try:
                    row = [group.category.course.course_code]
                except AttributeError:
                    pass
                try:
                    row = [group.course.course_code]
                except AttributeError:
                    pass
                row.append(group.name)
                if args.canvas_id:
                    row.append(user.id)
                try:
                    row.append(user.login_id)
                except AttributeError:
                    row.append(None)
                if args.ladok:
                    try:
                        row.append(user.integration_id)
                    except AttributeError:
                        row.append(None)
                if args.split_name:
                    lastnames, firstnames = user.sortable_name.split(", ")
                    row.append(firstnames.strip())
                    row.append(lastnames.strip())
                else:
                    row.append(user.name)
                if args.email:
                    try:
                        row.append(user.email)
                    except AttributeError:
                        row.append(None)
            except AttributeError as err:
                canvaslms.cli.warn(f"skipped {user}: {err}")
                continue

            yield row


def add_groups_command(subp):
    """Adds the groups subcommand and its options to argparse subparser subp"""
    groups_parser = subp.add_parser(
        "groups",
        help="Lists groups of a course",
        description="Lists groups of a course(s). Output, CSV-format: "
        "<course code> <group category> <group name> <#members>",
    )
    groups_parser.set_defaults(func=groups_command)
    courses.add_course_option(groups_parser)
    add_group_category_option(groups_parser)
    groups_parser.add_argument(
        "regex",
        metavar="group_regex",
        default=".*",
        nargs="?",
        help="Regex for filtering groups, default: '.*'",
    )


def groups_command(config, canvas, args):
    course_list = courses.process_course_option(canvas, args)
    output = csv.writer(sys.stdout, delimiter=args.delimiter)
    if args.category:
        categories = filter_group_categories(course_list, args.category)
    else:
        categories = filter_group_categories(course_list, ".*")

    for category in categories:
        for group in filter_groups([category], args.regex):
            row = [
                category.course.course_code,
                category.name,
                group.name,
                group.members_count,
            ]
            output.writerow(row)


def filter_group_categories(course_list, regex):
    """
    Filters out the group categories whose names match regex
    in the courses in course_list
    """

    name = re.compile(regex or ".*")

    for course in course_list:
        for category in course.get_group_categories():
            if name.search(category.name):
                category.course = course
                yield category


def filter_groups(items, regex):
    """
    Items is a list of either courses or group categories,
    regex is a regular expression.
    Returns all groups whose name match regex.
    """

    name = re.compile(regex or ".*")

    for item in items:
        for group in item.get_groups():
            if name.search(group.name):
                if isinstance(item, canvasapi.course.Course):
                    group.course = item
                elif isinstance(item, canvasapi.group.GroupCategory):
                    group.category = item
                yield group


def list_users(courses, roles):
    """
    List users in courses with roles.

    Fetches all users from Canvas without enrollment_type filtering,
    then filters locally by role. This allows efficient caching:
    all users are fetched once and cached, then filtered in-memory
    for subsequent calls with different roles.
    """
    users = list()

    for course in courses:
        try:
            course_users = list(course.get_users(include=["enrollments"]))
            if roles:
                filtered_users = []
                for user in course_users:
                    if hasattr(user, "enrollments"):
                        for enrollment in user.enrollments:
                            enrollment_type = enrollment.get("type", "").lower()
                            if any(role.lower() in enrollment_type for role in roles):
                                filtered_users.append(user)
                                break
                course_users = filtered_users
        except canvasapi.exceptions.CanvasException as err:
            canvaslms.cli.warn(f"skipped {course}: {err}")
            continue

        for user in course_users:
            user.course = course
        users.extend(course_users)

    return users


def filter_users(course_list, regex, roles=[]):
    """
    Filter users in courses with roles based on regex. `regex` is matched on
    - Canvas ID (exact match),
    - name (regex),
    - login ID (regex),
    - integration id (exact match),
    - SIS user ID (exact match).
    """
    pattern = re.compile(regex or ".*", re.IGNORECASE)

    for user in list_users(course_list, roles):
        if str(user.id) == regex:
            yield user
            continue

        if pattern.search(user.name):
            yield user
            continue

        try:
            if pattern.search(user.login_id):
                yield user
                continue
        except AttributeError:
            canvaslms.cli.warn(f"{user} has no login_id")

        try:
            if user.integration_id == regex:
                yield user
                continue
        except AttributeError:
            canvaslms.cli.warn(f"{user} has no integration_id")

        try:
            if user.sis_user_id == regex:
                yield user
                continue
        except AttributeError:
            canvaslms.cli.warn(f"{user} has no sis_user_id")


def list_students(courses):
    """List users in courses with role student"""
    return list_users(courses, ["student"])


def list_teachers(courses):
    """List users in courses with role teacher"""
    return list_users(courses, ["teacher"])


def get_uid(user):
    """
    Takes a user object and returns a unique identifier.

    Returns one of login_id, integration_id, sis_user_id, id (Canvas ID); in that
    order of preference.
    """
    attributes = ["login_id", "integration_id", "sis_user_id", "id"]
    for attribute in attributes:
        try:
            return operator.attrgetter(attribute)(user)
        except AttributeError:
            pass

    raise AttributeError(f"no unique user attribute existed, tried: {attributes}")


def add_user_option_wo_depends(parser, required=False, suppress_help=False):
    """
    Adds the -u option to argparse parser, without adding
    other required options.

    Args:
      parser: The argparse parser to add options to
      required: Whether the user option should be required (default: False)
      suppress_help: If True, hide this option from help output (default: False)

    The `role` option allows specifying which roles to include, for instance
    students or TAs.
    """
    help = (
        "Filter users on Canvas ID, name, login ID, integration ID, or "
        "SIS ID by user_regex. "
        "Integration ID and SIS ID match exactly, not by regex. "
        "Note that for login ID, you should start with ^ and $ to avoid "
        "matching on unintended substrings; c.f. son@institution.tld and "
        "person@institution.tld, where the first will match both without "
        "leading ^. The regex allows matching using ^son@, thus skipping "
        "any domain in this case."
    )
    options = {"required": required}
    if not required:
        options["default"] = ".*"
        help += ", default: '.*'"
    else:
        help += ", required: use '.*' to match all students"

    parser.add_argument(
        "-u",
        "--user",
        metavar="user_regex",
        help=argparse.SUPPRESS if suppress_help else help,
        **options,
    )

    parser.add_argument(
        "-r",
        "--role",
        choices={"teacher", "student", "student_view", "ta", "observer", "designer"},
        default="student",
        help=(
            argparse.SUPPRESS
            if suppress_help
            else "Includes only users in this role, defaults to student."
        ),
    )


def add_user_option(parser, required=False):
    """Adds the -u option to argparse parser"""
    try:
        courses.add_course_option(parser)
    except argparse.ArgumentError:
        pass

    add_user_option_wo_depends(parser, required)


def process_user_option(canvas, args):
    """Processes the user option from command line, returns a list of users"""
    user_list = list(
        filter_users(
            courses.process_course_option(canvas, args), args.user, roles=args.role
        )
    )
    if not user_list:
        raise canvaslms.cli.EmptyListError("No users found matching the criteria")
    return user_list


def add_group_category_option_wo_depends(parser, suppress_help=False):
    """Adds the group category option, without adding required other options

    Args:
      parser: The argparse parser to add options to
      suppress_help: If True, hide this option from help output (default: False)
    """
    parser.add_argument(
        "-C",
        "--category",
        metavar="category_regex",
        required=False,
        help=(
            argparse.SUPPRESS
            if suppress_help
            else "Filters groups only from the group categories matching "
            "category_regex"
        ),
    )


def add_group_category_option(parser):
    """Adds the group category option, adds required options"""
    try:
        courses.add_course_option(parser)
    except argparse.ArgumentError:
        pass

    add_group_category_option_wo_depends(parser)


def add_group_option_wo_depends(parser, suppress_help=False):
    """
    Adds group filtering option to argparse parser,
    without adding required options

    Args:
      parser: The argparse parser to add options to
      suppress_help: If True, hide this option from help output (default: False)
    """
    try:
        add_group_category_option_wo_depends(parser, suppress_help=suppress_help)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-G",
        "--group",
        metavar="group_regex",
        required=False,
        help=(
            argparse.SUPPRESS
            if suppress_help
            else "Filters user groups whose name match group_regex"
        ),
    )


def add_group_option(parser):
    """Adds group filtering options to argparse parser,
    adds required other options"""
    try:
        courses.add_course_option(parser)
    except argparse.ArgumentError:
        pass

    add_group_option_wo_depends(parser)


def process_group_options(canvas, args):
    """Processes the group/group category options, returns a list of groups"""

    course_list = courses.process_course_option(canvas, args)

    if args.category:
        group_list = list(
            filter_groups(
                filter_group_categories(course_list, args.category), args.group
            )
        )
    else:
        group_list = list(filter_groups(course_list, args.group))

    if not group_list:
        raise canvaslms.cli.EmptyListError("No groups found matching the criteria")
    return group_list


def add_user_or_group_option(parser, required=False, suppress_help=False):
    """Adds user and group options as mutually exclusive options to parser

    Args:
      parser: The argparse parser to add options to
      required: Whether to require one of user/group options (default: False)
      suppress_help: If True, hide these options from help output (default: False)
    """
    try:
        courses.add_course_option(parser, suppress_help=suppress_help)
    except argparse.ArgumentError:
        pass

    parser = parser.add_mutually_exclusive_group(required=required)

    try:
        add_user_option_wo_depends(parser, suppress_help=suppress_help)
    except argparse.ArgumentError:
        pass

    try:
        add_group_option_wo_depends(parser, suppress_help=suppress_help)
    except argparse.ArgumentError:
        pass


def process_user_or_group_option(canvas, args):
    """Returns a list of users, filtered either by user regex or by groups"""
    if args.group or args.category:
        users = list()
        for group in process_group_options(canvas, args):
            users.extend(group.get_users())

        if not users:
            raise canvaslms.cli.EmptyListError("No users found in the specified groups")
        return users

    return process_user_option(canvas, args)


def add_command(subp):
    """Adds the subcommands users and groups to argparse subparser subp"""
    add_users_command(subp)
    add_groups_command(subp)
