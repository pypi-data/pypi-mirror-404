import argparse
import arrow
import canvasapi
import canvaslms.cli
import canvaslms.cli.content
import canvaslms.cli.courses as courses
import canvaslms.cli.modules as modules
import canvaslms.cli.utils
import canvaslms.hacks.canvasapi
import csv
from datetime import datetime
import json
import logging
import os
import pypandoc
import re
import rich.console
import rich.markdown
import rich.syntax
import sys

logger = logging.getLogger(__name__)


def add_assignment_option(parser, ungraded=True, required=False, suppress_help=False):
    """Adds assignment selection options to argparse parser

    Args:
      parser: The argparse parser to add options to
      ungraded: Whether to include the --ungraded option (default: True)
      required: Whether to require one of the filter options (default: False)
      suppress_help: If True, hide these options from help output (default: False)
    """
    try:
        courses.add_course_option(
            parser, required=required, suppress_help=suppress_help
        )
    except argparse.ArgumentError:
        pass

    if ungraded:
        parser.add_argument(
            "-U",
            "--ungraded",
            action="store_true",
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Filter only assignments with ungraded submissions."
            ),
        )

    if required:
        # Required mode: allow combining filters; we just validate later that at least one was provided.
        parser.add_argument(
            "-a",
            "--assignment",
            required=False,
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Regex matching assignment title or Canvas identifier"
            ),
        )
        parser.add_argument(
            "-A",
            "--assignment-group",
            required=False,
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Regex matching assignment group title or Canvas identifier"
            ),
        )
        parser.add_argument(
            "-M",
            "--module",
            required=False,
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Regex matching module title or Canvas identifier"
            ),
        )
    else:
        parser.add_argument(
            "-a",
            "--assignment",
            required=False,
            default=".*",
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Regex matching assignment title or Canvas identifier, "
                "default: '.*'. Can be combined with -A and -M for AND filtering."
            ),
        )
        parser.add_argument(
            "-A",
            "--assignment-group",
            required=False,
            default="",
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Regex matching assignment group title or Canvas identifier. "
                "Can be combined with -a and -M for AND filtering."
            ),
        )
        parser.add_argument(
            "-M",
            "--module",
            required=False,
            default="",
            help=(
                argparse.SUPPRESS
                if suppress_help
                else "Regex matching module title or Canvas identifier. "
                "Can be combined with -a and -A for AND filtering."
            ),
        )


def process_assignment_option(canvas, args):
    course_list = courses.process_course_option(canvas, args)
    # If required filters were requested (set-dates passes required=True), ensure at least one provided.
    if (
        hasattr(args, "assignment")
        and hasattr(args, "assignment_group")
        and hasattr(args, "module")
    ):
        if (
            (args.assignment is None or args.assignment == "")
            and (args.assignment_group is None or args.assignment_group == "")
            and (args.module is None or args.module == "")
        ):
            raise canvaslms.cli.EmptyListError(
                "At least one of -a, -A or -M must be specified"
            )
    assignments_list = []

    for course in course_list:
        try:
            ungraded = args.ungraded
        except AttributeError:
            ungraded = False
        filtered_assignments = list(
            filter_assignments([course], args.assignment, ungraded=ungraded)
        )

        try:
            assignm_grp_regex = args.assignment_group
        except AttributeError:
            assignm_grp_regex = ""

        try:
            module_regex = args.module
        except AttributeError:
            module_regex = ""
        if assignm_grp_regex:
            assignment_groups = filter_assignment_groups(course, assignm_grp_regex)
            filtered_assignments = list(
                filter_assignments_by_group_list(
                    assignment_groups, filtered_assignments
                )
            )
        if module_regex:
            course_modules = modules.filter_modules(course, module_regex)
            filtered_assignments = list(
                modules.filter_assignments_by_module_list(
                    course_modules, filtered_assignments
                )
            )
        assignments_list += filtered_assignments
    assignments_list = list(assignments_list)
    if not assignments_list:
        raise canvaslms.cli.EmptyListError("No assignments found matching the criteria")
    return assignments_list


def assignments_list_command(config, canvas, args):
    output = csv.writer(sys.stdout, delimiter=args.delimiter)
    assignment_list = process_assignment_option(canvas, args)

    for assignment in assignment_list:
        # Get assignment group name safely
        if hasattr(assignment, "assignment_group") and assignment.assignment_group:
            group_name = assignment.assignment_group.name
        elif (
            hasattr(assignment, "assignment_group_id")
            and assignment.assignment_group_id
        ):
            # Fallback: try to get group from course if available
            try:
                group = assignment.course.get_assignment_group(
                    assignment.assignment_group_id
                )
                group_name = group.name
            except:
                group_name = f"Group {assignment.assignment_group_id}"
        else:
            group_name = "No Group"

        output.writerow(
            [
                assignment.course.course_code,
                group_name,
                assignment.name,
                canvaslms.cli.utils.format_local_time(assignment.due_at),
                canvaslms.cli.utils.format_local_time(assignment.unlock_at),
                canvaslms.cli.utils.format_local_time(assignment.lock_at),
            ]
        )


def filter_assignment_groups(course, regex):
    """Returns all assignment groups of course whose name matches regex"""
    name = re.compile(regex)
    return filter(lambda group: name.search(group.name), course.get_assignment_groups())


def filter_assignments_by_group(assignment_group, assignments):
    """Returns elements in assignments that are part of assignment_group"""
    for assignment in assignments:
        if assignment.assignment_group_id == assignment_group.id:
            assignment.assignment_group = assignment_group
            yield assignment


def filter_assignments_by_group_list(assignment_groups, assignments):
    """Returns elements in assignments that belong to any of the assignment_groups"""
    group_ids = {group.id for group in assignment_groups}

    for assignment in assignments:
        if assignment.assignment_group_id in group_ids:
            for group in assignment_groups:
                if assignment.assignment_group_id == group.id:
                    assignment.assignment_group = group
                    break
            yield assignment


def assignments_view_command(config, canvas, args):
    console = rich.console.Console()

    assignment_list = process_assignment_option(canvas, args)
    for assignment in assignment_list:
        if sys.stdout.isatty():
            if args.html:
                header = f"# {assignment.name}\n\n"
                header += f"## Metadata\n\n"
                header += f"- Course: {assignment.course.course_code}\n"
                header += f"- Unlocks: {canvaslms.cli.utils.format_local_time(assignment.unlock_at) if assignment.unlock_at else 'None'}\n"
                header += f"- Due: {canvaslms.cli.utils.format_local_time(assignment.due_at) if assignment.due_at else 'None'}\n"
                header += f"- Locks: {canvaslms.cli.utils.format_local_time(assignment.lock_at) if assignment.lock_at else 'None'}\n"
                header += f"- URL: {assignment.html_url}\n"
                header += "\n## Description (HTML)\n\n"

                with console.pager(styles=True):
                    console.print(rich.markdown.Markdown(header))
                    if hasattr(assignment, "description") and assignment.description:
                        syntax = rich.syntax.Syntax(
                            assignment.description,
                            "html",
                            theme="monokai",
                            word_wrap=True,
                        )
                        console.print(syntax)
                    else:
                        console.print("(No description)")
            else:
                output = format_assignment(assignment)
                pager = ""
                if "MANPAGER" in os.environ:
                    pager = os.environ["MANPAGER"]
                elif "PAGER" in os.environ:
                    pager = os.environ["PAGER"]

                styles = False
                if "less" in pager and ("-R" in pager or "-r" in pager):
                    styles = True
                with console.pager(styles=styles, links=True):
                    console.print(rich.markdown.Markdown(output, code_theme="manni"))
        else:
            if args.html:
                assignment_modules = modules.get_item_modules(
                    assignment.course, "Assignment", assignment.id
                )
                assignment_rubric = None
                if hasattr(assignment, "rubric") and assignment.rubric:
                    assignment_rubric = assignment.rubric
                output = canvaslms.cli.content.render_to_html(
                    assignment,
                    canvaslms.cli.content.ASSIGNMENT_SCHEMA,
                    content_attr="description",
                    extra_attributes={
                        "modules": assignment_modules,
                        "rubric": assignment_rubric,
                    },
                )
                print(output)
            else:
                assignment_modules = modules.get_item_modules(
                    assignment.course, "Assignment", assignment.id
                )
                assignment_rubric = None
                if hasattr(assignment, "rubric") and assignment.rubric:
                    assignment_rubric = assignment.rubric
                output = canvaslms.cli.content.render_to_markdown(
                    assignment,
                    canvaslms.cli.content.ASSIGNMENT_SCHEMA,
                    content_attr="description",
                    extra_attributes={
                        "modules": assignment_modules,
                        "rubric": assignment_rubric,
                    },
                )
                print(output)


def format_assignment(assignment):
    """Returns an assignment formatted for the terminal"""
    text = f"""
# {assignment.name}

## Metadata

- Unlocks: {canvaslms.cli.utils.format_local_time(assignment.unlock_at) if assignment.unlock_at else None}
- Due:     {canvaslms.cli.utils.format_local_time(assignment.due_at) if assignment.due_at else None}
- Locks:   {canvaslms.cli.utils.format_local_time(assignment.lock_at) if assignment.lock_at else None}
- Ungraded submissions: {assignment.needs_grading_count}
- Submission type: {assignment.submission_types}
- URL: {assignment.html_url}
- Submissions: {assignment.submissions_download_url}

"""

    if hasattr(assignment, "description") and assignment.description:
        instruction = pypandoc.convert_text(assignment.description, "md", format="html")
        text += f"## Instruction\n\n{instruction}\n\n"
        try:
            text += f"## Rubric\n\n{format_rubric(assignment.rubric)}\n\n"
        except AttributeError:
            pass
    else:
        try:
            text += f"## Rubric\n\n{format_rubric(assignment.rubric)}\n\n"
        except AttributeError:
            pass
        text += f"## Assignment data\n\n```json\n{format_json(assignment)}\n```\n"

    return text


def format_rubric(rubric):
    """
    Returns a markdown representation of the rubric
    """
    if not rubric:
        return "No rubric set."

    text = ""
    for criterion in rubric:
        text += f"- {criterion['description']}\n"
        text += f"  - Points: {criterion['points']}\n"
        text += f"  - Ratings: "
        text += (
            "; ".join(
                [
                    f"{rating['description'].strip()} ({rating['points']})"
                    for rating in criterion["ratings"]
                ]
            )
            + "\n"
        )
        text += f"\n```\n{criterion['long_description']}\n```\n\n"

    return text


def format_json(assignment):
    """Returns a JSON representation of the assignment"""
    return json.dumps(
        {
            key: str(value)
            for key, value in assignment.__dict__.items()
            if not key.startswith("_")
        },
        indent=2,
    )


def list_assignments(assignments_containers, ungraded=False):
    """Lists all assignments in all assignments containers (courses or
    assignement groups)"""
    for container in assignments_containers:
        if isinstance(container, canvasapi.course.Course):
            course = container
        elif isinstance(container, canvasapi.assignment.AssignmentGroup):
            assignment_group = container
            course = assignment_group.course

        if ungraded:
            assignments = container.get_assignments(bucket="ungraded")
        else:
            assignments = container.get_assignments()

        for assignment in assignments:
            try:
                assignment.course = course
            except NameError:
                pass

            try:
                assignment.assignment_group = assignment_group
            except NameError:
                pass

            yield assignment


def list_ungraded_assignments(assignments_containers):
    return list_assignments(assignments_containers, ungraded=True)


def filter_assignments(assignments_containers, regex, ungraded=False):
    """Returns all assignments from assignments_container whose
    title matches regex.

    We normalize a missing regex (None or empty string) to '.*' to match all.
    This handles required-filter contexts where -M/-A are used without -a.
    """
    if regex is None or regex == "":
        regex = ".*"
    p = re.compile(regex)
    for assignment in list_assignments(assignments_containers, ungraded=ungraded):
        if p.search(assignment.name):
            yield assignment
        elif p.search(str(assignment.id)):
            yield assignment


def assignments_set_dates_command(config, canvas, args):
    assignment_list = process_assignment_option(canvas, args)
    assignment_data = {}

    if args.due_at is not None:
        try:
            assignment_data["due_at"] = canvaslms.cli.utils.parse_date(args.due_at)
        except ValueError as e:
            logger.error(f"Error parsing due date: {e}")
            return
    if args.unlock_at is not None:
        try:
            assignment_data["unlock_at"] = canvaslms.cli.utils.parse_date(
                args.unlock_at
            )
        except ValueError as e:
            logger.error(f"Error parsing unlock date: {e}")
            return
    if args.lock_at is not None:
        try:
            assignment_data["lock_at"] = canvaslms.cli.utils.parse_date(args.lock_at)
        except ValueError as e:
            logger.error(f"Error parsing lock date: {e}")
            return

    if not assignment_data:
        logger.error(
            "No date options provided. Use --due-at, --unlock-at, or --lock-at."
        )
        return

    # Wrap the assignment data in the structure Canvas expects
    updates = {"assignment": assignment_data}
    for assignment in assignment_list:
        logger.info(f"Updating assignment '{assignment.name}' (ID: {assignment.id})")
        for field, value in assignment_data.items():
            if value is None:
                logger.info(f"  Clearing {field}")
            else:
                logger.info(f"  Setting {field} to {value}")

        try:
            assignment.edit(**updates)
            assignment._fetched_at = datetime.now()
            if hasattr(assignment.course, "assignment_cache"):
                assignment.course.assignment_cache[assignment.id] = (assignment, {})
            logger.info(f"Updated dates for assignment '{assignment.name}'")
        except Exception as e:
            logger.error(
                f"Error updating assignment '{assignment.name}' (ID: {assignment.id}): {e}"
            )


def assignments_edit_command(config, canvas, args):
    """Edit assignment content interactively or from file."""
    if args.file:
        try:
            # body_content is Markdown or HTML depending on args.html
            attributes, body_content = canvaslms.cli.content.read_content_from_file(
                args.file
            )
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            print(f"Error reading file: {e}", file=sys.stderr)
            return

        errors = canvaslms.cli.content.validate_attributes(
            attributes, canvaslms.cli.content.ASSIGNMENT_SCHEMA
        )
        if errors:
            for error in errors:
                print(f"Validation error: {error}", file=sys.stderr)
            return
        if args.html:
            html_content = body_content  # Already HTML, no conversion needed
        else:
            html_content = pypandoc.convert_text(body_content, "html", format="md")

        if "id" in attributes and attributes["id"]:
            assignment_id = attributes["id"]
            course_list = courses.process_course_option(canvas, args)
            if not course_list:
                print("Error: No courses found matching criteria", file=sys.stderr)
                return

            course = course_list[0]
            try:
                assignment = course.get_assignment(assignment_id)
                assignment.course = course
                update_data = {
                    "assignment": {
                        "name": attributes.get("name", assignment.name),
                        "description": html_content,
                    }
                }

                if "due_at" in attributes and attributes["due_at"] is not None:
                    update_data["assignment"]["due_at"] = attributes["due_at"]
                if "unlock_at" in attributes and attributes["unlock_at"] is not None:
                    update_data["assignment"]["unlock_at"] = attributes["unlock_at"]
                if "lock_at" in attributes and attributes["lock_at"] is not None:
                    update_data["assignment"]["lock_at"] = attributes["lock_at"]
                if (
                    "points_possible" in attributes
                    and attributes["points_possible"] is not None
                ):
                    update_data["assignment"]["points_possible"] = attributes[
                        "points_possible"
                    ]
                if "published" in attributes:
                    update_data["assignment"]["published"] = attributes["published"]

                try:
                    assignment.edit(**update_data)
                    assignment._fetched_at = datetime.now()
                    if hasattr(assignment.course, "assignment_cache"):
                        assignment.course.assignment_cache[assignment.id] = (
                            assignment,
                            {},
                        )
                    logger.info(f"Updated assignment: {assignment.name}")
                    if "modules" in attributes:
                        module_regexes = attributes["modules"]
                        added, removed = modules.update_item_modules(
                            assignment.course,
                            "Assignment",
                            assignment.id,
                            module_regexes,
                        )
                        if added:
                            print(
                                f"  Added to modules: {', '.join(added)}",
                                file=sys.stderr,
                            )
                        if removed:
                            print(
                                f"  Removed from modules: {', '.join(removed)}",
                                file=sys.stderr,
                            )
                except Exception as e:
                    logger.error(f"Error updating assignment '{assignment.name}': {e}")
                    print(
                        f"Error updating assignment '{assignment.name}': {e}",
                        file=sys.stderr,
                    )
            except Exception as e:
                if args.create:
                    create_params = {
                        "name": attributes.get("name", "Untitled Assignment"),
                        "description": html_content,
                    }
                    if "due_at" in attributes and attributes["due_at"] is not None:
                        create_params["due_at"] = attributes["due_at"]
                    if (
                        "unlock_at" in attributes
                        and attributes["unlock_at"] is not None
                    ):
                        create_params["unlock_at"] = attributes["unlock_at"]
                    if "lock_at" in attributes and attributes["lock_at"] is not None:
                        create_params["lock_at"] = attributes["lock_at"]
                    if (
                        "points_possible" in attributes
                        and attributes["points_possible"] is not None
                    ):
                        create_params["points_possible"] = attributes["points_possible"]
                    if "published" in attributes:
                        create_params["published"] = attributes["published"]

                    try:
                        new_assignment = course.create_assignment(
                            assignment=create_params
                        )
                        new_assignment.course = course
                        print(
                            f"Created assignment: {new_assignment.name} (id: {new_assignment.id})",
                            file=sys.stderr,
                        )
                        if "modules" in attributes:
                            module_regexes = attributes["modules"]
                            added, removed = modules.update_item_modules(
                                new_assignment.course,
                                "Assignment",
                                new_assignment.id,
                                module_regexes,
                            )
                            if added:
                                print(
                                    f"  Added to modules: {', '.join(added)}",
                                    file=sys.stderr,
                                )
                    except Exception as e:
                        logger.error(f"Error creating assignment: {e}")
                        print(f"Error creating assignment: {e}", file=sys.stderr)
                else:
                    print(
                        f"Error: Assignment with ID '{assignment_id}' not found. "
                        f"Use --create to create a new assignment.",
                        file=sys.stderr,
                    )
                    return
        else:
            assignment_list = process_assignment_option(canvas, args)

            for assignment in assignment_list:
                update_data = {
                    "assignment": {
                        "name": attributes.get("name", assignment.name),
                        "description": html_content,
                    }
                }

                if "due_at" in attributes and attributes["due_at"] is not None:
                    update_data["assignment"]["due_at"] = attributes["due_at"]
                if "unlock_at" in attributes and attributes["unlock_at"] is not None:
                    update_data["assignment"]["unlock_at"] = attributes["unlock_at"]
                if "lock_at" in attributes and attributes["lock_at"] is not None:
                    update_data["assignment"]["lock_at"] = attributes["lock_at"]
                if (
                    "points_possible" in attributes
                    and attributes["points_possible"] is not None
                ):
                    update_data["assignment"]["points_possible"] = attributes[
                        "points_possible"
                    ]
                if "published" in attributes:
                    update_data["assignment"]["published"] = attributes["published"]

                try:
                    assignment.edit(**update_data)
                    assignment._fetched_at = datetime.now()
                    if hasattr(assignment.course, "assignment_cache"):
                        assignment.course.assignment_cache[assignment.id] = (
                            assignment,
                            {},
                        )
                    logger.info(f"Updated assignment: {assignment.name}")
                    if "modules" in attributes:
                        module_regexes = attributes["modules"]
                        added, removed = modules.update_item_modules(
                            assignment.course,
                            "Assignment",
                            assignment.id,
                            module_regexes,
                        )
                        if added:
                            print(
                                f"  Added to modules: {', '.join(added)}",
                                file=sys.stderr,
                            )
                        if removed:
                            print(
                                f"  Removed from modules: {', '.join(removed)}",
                                file=sys.stderr,
                            )
                except Exception as e:
                    logger.error(f"Error updating assignment '{assignment.name}': {e}")
                    print(
                        f"Error updating assignment '{assignment.name}': {e}",
                        file=sys.stderr,
                    )
    else:
        try:
            assignment_list = process_assignment_option(canvas, args)
        except canvaslms.cli.EmptyListError as e:
            print(f"Error: {e}", file=sys.stderr)
            return
        print(f"Will edit {len(assignment_list)} assignment(s):", file=sys.stderr)
        for assignment in assignment_list:
            course_code = (
                assignment.course.course_code if hasattr(assignment, "course") else "?"
            )
            print(f"  - {course_code}: {assignment.name}", file=sys.stderr)

        try:
            confirm = input("Continue? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            return

        if confirm not in ["y", "yes"]:
            print("Cancelled.", file=sys.stderr)
            return
        updated_count = 0
        skipped_count = 0

        for assignment in assignment_list:
            course_code = (
                assignment.course.course_code if hasattr(assignment, "course") else "?"
            )
            print(f"\nEditing: {course_code}: {assignment.name}", file=sys.stderr)

            current_attrs = canvaslms.cli.content.extract_attributes_from_object(
                assignment, canvaslms.cli.content.ASSIGNMENT_SCHEMA
            )
            assignment_modules = modules.get_item_modules(
                assignment.course, "Assignment", assignment.id
            )
            assignment_rubric = None
            if hasattr(assignment, "rubric") and assignment.rubric:
                assignment_rubric = assignment.rubric
            result = canvaslms.cli.content.get_content_from_editor(
                canvaslms.cli.content.ASSIGNMENT_SCHEMA,
                current_attrs,
                content_attr="description",
                extra_attributes={
                    "modules": assignment_modules,
                    "rubric": assignment_rubric,
                },
                html_mode=args.html,
            )
            if result is None:
                print("Editor cancelled. Skipping this assignment.", file=sys.stderr)
                skipped_count += 1
                continue

            # body_content is Markdown or HTML depending on args.html
            attributes, body_content = result
            title = attributes.get("name", assignment.name)
            result = canvaslms.cli.content.interactive_confirm_and_edit(
                title,
                body_content,
                attributes,
                canvaslms.cli.content.ASSIGNMENT_SCHEMA,
                "Assignment",
                content_attr="description",
            )

            if result is None:
                print("Discarded changes for this assignment.", file=sys.stderr)
                skipped_count += 1
                continue

            final_attrs, final_content = result
            if args.html:
                html_content = final_content
            else:
                try:
                    html_content = pypandoc.convert_text(
                        final_content, "html", format="md"
                    )
                except Exception as e:
                    logger.warning(f"Failed to convert markdown to HTML: {e}")
                    html_content = final_content

            update_data = {
                "assignment": {
                    "name": final_attrs.get("name", assignment.name),
                    "description": html_content,
                }
            }

            # Add optional attributes
            if "due_at" in final_attrs and final_attrs["due_at"] is not None:
                update_data["assignment"]["due_at"] = final_attrs["due_at"]
            if "unlock_at" in final_attrs and final_attrs["unlock_at"] is not None:
                update_data["assignment"]["unlock_at"] = final_attrs["unlock_at"]
            if "lock_at" in final_attrs and final_attrs["lock_at"] is not None:
                update_data["assignment"]["lock_at"] = final_attrs["lock_at"]
            if (
                "points_possible" in final_attrs
                and final_attrs["points_possible"] is not None
            ):
                update_data["assignment"]["points_possible"] = final_attrs[
                    "points_possible"
                ]
            if "published" in final_attrs:
                update_data["assignment"]["published"] = final_attrs["published"]

            try:
                assignment.edit(**update_data)
                assignment._fetched_at = datetime.now()
                if hasattr(assignment.course, "assignment_cache"):
                    assignment.course.assignment_cache[assignment.id] = (assignment, {})
                logger.info(f"Updated assignment: {assignment.name}")
                if "modules" in final_attrs:
                    module_regexes = final_attrs["modules"]
                    added, removed = modules.update_item_modules(
                        assignment.course, "Assignment", assignment.id, module_regexes
                    )
                    if added:
                        print(
                            f"  Added to modules: {', '.join(added)}", file=sys.stderr
                        )
                    if removed:
                        print(
                            f"  Removed from modules: {', '.join(removed)}",
                            file=sys.stderr,
                        )
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating assignment '{assignment.name}': {e}")
                print(
                    f"Error updating assignment '{assignment.name}': {e}",
                    file=sys.stderr,
                )
                skipped_count += 1
        print(
            f"\nDone. Updated {updated_count}/{len(assignment_list)} assignment(s).",
            file=sys.stderr,
        )
        if skipped_count > 0:
            print(f"Skipped {skipped_count} assignment(s).", file=sys.stderr)


def add_command(subp):
    """Adds the assignments command with subcommands to argparse parser subp"""
    add_assignments_command(subp)
    add_assignment_command(subp)


def add_assignments_command(subp):
    """Adds the assignments command with subcommands to argparse parser subp"""
    assignments_parser = subp.add_parser(
        "assignments",
        help="Assignment management commands",
        description="Commands for managing assignments: list, show, and set dates.",
    )

    # Create subparsers for assignments subcommands
    # Set required=False to allow bare "assignments" command to default to list
    assignments_subp = assignments_parser.add_subparsers(
        title="assignments subcommands", dest="assignments_subcommand", required=False
    )

    # Set default function for bare "assignments" command (defaults to list)
    assignments_parser.set_defaults(func=assignments_list_command)

    # Add arguments for the default list behavior to main parser
    # We suppress help to keep the help output focused on subcommands
    add_assignment_option(assignments_parser, suppress_help=True)

    # Add list subcommand (was the old "assignments" command)
    list_parser = assignments_subp.add_parser(
        "list",
        help="List assignments of a course",
        description="Lists assignments of a course. "
        "Output, CSV-format: "
        "<course> <assignment group> <assignment name> "
        "<due date> <unlock at> <lock at>",
    )
    list_parser.set_defaults(func=assignments_list_command)
    add_assignment_option(list_parser)
    # Add view subcommand (was the old "assignment" command)
    view_parser = assignments_subp.add_parser(
        "view",
        help="View assignment details",
        description="Views detailed information about assignments. "
        "Use --html to preserve HTML instead of converting to Markdown.",
    )
    view_parser.set_defaults(func=assignments_view_command)
    add_assignment_option(view_parser)
    view_parser.add_argument(
        "--html",
        action="store_true",
        help="Output raw HTML instead of converting to Markdown",
    )
    # Add set-dates subcommand (was the old "set-dates" command)
    set_dates_parser = assignments_subp.add_parser(
        "set-dates",
        help="Set assignment dates",
        description="Set assignment dates: due date, unlock date, and lock date. "
        "Dates can be provided in various human-readable formats.",
    )
    set_dates_parser.set_defaults(func=assignments_set_dates_command)
    add_assignment_option(set_dates_parser, ungraded=False, required=True)
    date_group = set_dates_parser.add_argument_group("date options")
    date_group.add_argument(
        "--due-at",
        help="Set the due date (when assignment is due). "
        "Use 'none' or 'clear' to remove the due date.",
    )
    date_group.add_argument(
        "--unlock-at",
        help="Set the unlock date (when assignment becomes available). "
        "Use 'none' or 'clear' to remove the unlock date.",
    )
    date_group.add_argument(
        "--lock-at",
        help="Set the lock date (when assignment is no longer available). "
        "Use 'none' or 'clear' to remove the lock date.",
    )
    set_dates_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Print information about what is being updated",
    )
    edit_parser = assignments_subp.add_parser(
        "edit",
        help="Edit assignment content interactively or from a file",
        description="Edit assignment content. Without -f, opens each matching "
        "assignment in your editor for interactive editing with preview. "
        "With -f, reads from a Markdown file with YAML front matter and updates "
        "directly (script-friendly). If the YAML contains an 'id' field, the "
        "command uses it to identify the assignment; use --create to create a new "
        "assignment if the ID is not found. Use --html to read/edit HTML directly "
        "without Markdown conversion.",
    )
    edit_parser.set_defaults(func=assignments_edit_command)
    add_assignment_option(edit_parser, ungraded=False, required=True)
    canvaslms.cli.content.add_file_option(edit_parser)
    edit_parser.add_argument(
        "--create",
        action="store_true",
        help="Create a new assignment if the ID in the YAML is not found",
    )
    edit_parser.add_argument(
        "--html",
        action="store_true",
        help="Read file as HTML instead of converting from Markdown. "
        "In interactive mode, edit HTML directly.",
    )


def add_assignment_command(subp):
    """Adds the assignment (singular) command as an alias for assignments view"""
    assignment_parser = subp.add_parser(
        "assignment",
        help="View assignment details (alias for 'assignments view')",
        description="Views detailed information about assignments",
    )
    assignment_parser.set_defaults(func=assignments_view_command)
    add_assignment_option(assignment_parser)
