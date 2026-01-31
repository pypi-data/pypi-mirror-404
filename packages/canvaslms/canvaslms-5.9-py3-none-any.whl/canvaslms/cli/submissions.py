import canvasapi.exceptions
import canvasapi.file
import canvasapi.submission

import canvaslms.cli
import canvaslms.cli.assignments as assignments
import canvaslms.cli.users as users
import canvaslms.cli.utils
import canvaslms.hacks.canvasapi
import canvaslms.hacks.attachment_cache as attachment_cache

import argparse
import csv

try:
    import patiencediff as difflib
except ImportError:
    import difflib
import json
import logging
import os
import pathlib
import subprocess
import pypandoc
import re
import rich.console
import rich.markdown
import rich.json
import shlex
import sys
import tempfile
import textwrap
import urllib.request
import webbrowser

logger = logging.getLogger(__name__)

choices_for_shells = ["shell", "docker"]
DEFAULT_DIFF_THRESHOLD_FIXED = 30
DEFAULT_DIFF_THRESHOLD_PERCENT = 60


def submissions_list_command(config, canvas, args):
    assignment_list = assignments.process_assignment_option(canvas, args)
    to_include = []
    if args.history:
        to_include += ["submission_history"]

    if args.ungraded:
        submissions = list_ungraded_submissions(assignment_list, include=to_include)
    else:
        submissions = list_submissions(assignment_list, include=to_include)
    if args.user or args.category or args.group:
        user_list = users.process_user_or_group_option(canvas, args)
        submissions = filter_submissions(submissions, user_list)
    if args.history:
        submissions = list(submissions)
        historical_submissions = []
        for submission in submissions:
            for prev_submission in submission.submission_history:
                prev_submission = canvasapi.submission.Submission(
                    submission._requester, prev_submission
                )
                prev_submission.assignment = submission.assignment
                prev_submission.user = submission.user
                historical_submissions.append(prev_submission)

        submissions = historical_submissions
    output = csv.writer(sys.stdout, delimiter=args.delimiter)

    # Convert to list and check if empty
    submissions = list(submissions)
    if not submissions:
        raise canvaslms.cli.EmptyListError("No submissions found matching the criteria")

    for submission in submissions:
        if args.login_id:
            output.writerow(format_submission_short_unique(submission))
        else:
            output.writerow(format_submission_short(submission))


def speedgrader(submission):
    """Returns the SpeedGrader URL of the submission"""
    try:
        speedgrader_url = submission.preview_url
    except AttributeError:
        return None

    speedgrader_url = re.sub(
        "assignments/", "gradebook/speed_grader?assignment_id=", speedgrader_url
    )

    speedgrader_url = re.sub("/submissions/", "&student_id=", speedgrader_url)

    speedgrader_url = re.sub(r"\?preview.*$", "", speedgrader_url)

    return speedgrader_url


def submissions_view_command(config, canvas, args):
    if args.diff:
        args.history = True

    submission_list = process_submission_options(canvas, args)

    console = rich.console.Console()
    if args.output_dir:
        tmpdir = pathlib.Path(args.output_dir)
    else:
        tmpdir = pathlib.Path(tempfile.mkdtemp())
    for submission in submission_list:
        if args.sort_order == "student":
            subdir = (
                f"{submission.user.login_id}"
                f"/{submission.assignment.course.course_code}"
                f"/{submission.assignment.name}"
            )
        else:
            subdir = (
                f"{submission.assignment.course.course_code}"
                f"/{submission.assignment.name}"
                f"/{submission.user.login_id}"
            )

        (tmpdir / subdir).mkdir(parents=True, exist_ok=True)
        output = format_submission(
            submission,
            history=args.history,
            tmpdir=tmpdir / subdir,
            json_format=args.json,
            diff=args.diff,
            diff_threshold_fixed=args.diff_threshold_fixed,
            diff_threshold_percent=args.diff_threshold_percent,
        )

        if args.json:
            filename = "metadata.json"
            output = json.dumps(output, indent=2)
        else:
            filename = "metadata.md"
        with open(tmpdir / subdir / filename, "w") as f:
            f.write(output)

        if args.open == "open":
            subprocess.run(["open", tmpdir / subdir])
        elif args.open == "all":
            for file in (tmpdir / subdir).iterdir():
                subprocess.run(["open", file])

        if args.open in choices_for_shells:
            if args.open == "shell":
                print(
                    f"---> Spawning a shell ({os.environ['SHELL']}) in {tmpdir/subdir}"
                )

                subprocess.run(
                    ["sh", "-c", f"cd '{tmpdir/subdir}' && exec {os.environ['SHELL']}"]
                )

                print(
                    f"<--- canvaslms submission shell terminated.\n"
                    f"---- Files left in {tmpdir/subdir}."
                )
            elif args.open == "docker":
                print(f"---> Running a Docker container, files mounted in /mnt.")

                cmd = ["docker", "run", "-it", "--rm"]
                if args.docker_args:
                    cmd += args.docker_args
                cmd += [
                    "-v",
                    f"{tmpdir/subdir}:/mnt",
                    args.docker_image,
                    args.docker_cmd,
                ]

                subprocess.run(cmd)

                print(
                    f"<--- canvaslms submission Docker container terminated.\n"
                    f"---- Files left in {tmpdir/subdir}.\n"
                    f"---- To rerun the container, run:\n"
                    f"`{' '.join(map(shlex.quote, cmd))}`"
                )
        elif args.output_dir:
            pass
        elif sys.stdout.isatty():
            pager = ""
            if "MANPAGER" in os.environ:
                pager = os.environ["MANPAGER"]
            elif "PAGER" in os.environ:
                pager = os.environ["PAGER"]

            styles = False
            if "less" in pager and ("-R" in pager or "-r" in pager):
                styles = True
            with console.pager(styles=styles):
                if args.json:
                    console.print(rich.json.JSON(output))
                else:
                    console.print(rich.markdown.Markdown(output, code_theme="manni"))
        else:
            print(output)


def add_submission_options(parser, required=False, suppress_help=False):
    """Adds submission selection options to argparse parser

    Args:
      parser: The argparse parser to add options to
      required: Whether to require submission filter options (default: False)
      suppress_help: If True, hide these options from help output (default: False)
    """
    try:
        assignments.add_assignment_option(
            parser, required=required, suppress_help=suppress_help
        )
    except argparse.ArgumentError:
        pass

    try:
        users.add_user_or_group_option(
            parser, required=required, suppress_help=suppress_help
        )
    except argparse.ArgumentError:
        pass

    submissions_parser = parser.add_argument_group("filter submissions")
    try:  # to protect from this option already existing in add_assignment_option
        submissions_parser.add_argument(
            "-U",
            "--ungraded",
            action="store_true",
            help=argparse.SUPPRESS if suppress_help else "Only ungraded submissions.",
        )
    except argparse.ArgumentError:
        pass


def add_grading_options(parser):
    """Adds grading options to argparse parser

    These options are shared between 'submissions grade' and 'grade' commands.

    Args:
      parser: The argparse parser to add options to
    """
    grade_options = parser.add_argument_group(
        "arguments to set the grade and/or comment, " "if none given, opens SpeedGrader"
    )
    grade_options.add_argument(
        "-g", "--grade", help="The grade to set for the submissions"
    )
    grade_options.add_argument("-m", "--message", help="A comment to the student")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Prints information about what is being graded",
    )


def add_view_options(parser):
    """Adds submission viewing options to argparse parser

    These options are shared between 'submissions view' and 'submission' commands.

    Args:
      parser: The argparse parser to add options to
    """
    parser.add_argument(
        "-o",
        "--output-dir",
        required=False,
        default=None,
        help="Write output to files in directory the given directory. "
        "If not specified, print to stdout. "
        "If specified, do not print to stdout.",
    )

    parser.add_argument(
        "--json",
        required=False,
        action="store_true",
        default=False,
        help="Print output as JSON, otherwise Markdown.",
    )

    parser.add_argument(
        "-H", "--history", action="store_true", help="Include submission history."
    )

    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diffs between submission versions. Automatically enables --history.",
    )

    parser.add_argument(
        "--diff-threshold-fixed",
        type=int,
        default=DEFAULT_DIFF_THRESHOLD_FIXED,
        metavar="N",
        help="Fixed edit distance threshold for matching renamed files. "
        "Files with distance <= N will match. Default: %(default)s",
    )

    parser.add_argument(
        "--diff-threshold-percent",
        type=int,
        default=DEFAULT_DIFF_THRESHOLD_PERCENT,
        metavar="PCT",
        help="Percentage threshold for matching renamed files. "
        "Files with distance <= PCT%% of filename length will match. "
        "Default: %(default)s",
    )

    parser.add_argument(
        "--open",
        required=False,
        nargs="?",
        default=None,
        const="open",
        choices=["open", "all"] + choices_for_shells,
        help="Open the directory containing the files using "
        "the default file manager (`open`). "
        "With `open`, the pager will be used to display the output as usual. "
        "With `all`, all files (not the directory containing them) will be "
        "opened in the default application for the file type. "
        "With `shell`, we just drop into the shell (as set by $SHELL), "
        "the output can be found in the metadata.{json,md} file in "
        "the shell's working directory. "
        "With `docker`, we run a Docker container with the "
        "directory mounted in the container. "
        "This way we can run the code in the submission in a "
        "controlled environment. "
        "Note that this requires Docker to be installed and running. "
        "Default: %(const)s",
    )

    parser.add_argument(
        "--sort-order",
        required=False,
        choices=["student", "course"],
        default="student",
        help="Determines the order in which directories are created "
        "in `output_dir`. `student` results in `student/course/assignment` "
        "and `course` results in `course/assignment/student`. "
        "Default: %(default)s",
    )

    parser.add_argument(
        "--docker-image",
        required=False,
        default="ubuntu",
        help="The Docker image to use when running a Docker container. "
        "This is used with the `docker` option for `--open`. "
        "Default: %(default)s",
    )

    parser.add_argument(
        "--docker-cmd",
        required=False,
        default="bash",
        help="The command to run in the Docker container. "
        "This is used with the `docker` option for `--open`. "
        "Default: %(default)s",
    )

    parser.add_argument(
        "--docker-args",
        required=False,
        default=[],
        nargs=argparse.REMAINDER,
        help="Any additional arguments to pass to the Docker command. "
        "This is used with the `docker` option for `--open`. "
        "Note that this must be the last option on the command line, it takes "
        "the rest of the line as arguments for Docker.",
    )


def process_submission_options(canvas, args):
    assignment_list = assignments.process_assignment_option(canvas, args)
    user_list = users.process_user_or_group_option(canvas, args)

    if args.ungraded:
        submissions = list_ungraded_submissions(
            assignment_list,
            include=["submission_history", "submission_comments", "rubric_assessment"],
        )
    else:
        submissions = list_submissions(
            assignment_list,
            include=["submission_history", "submission_comments", "rubric_assessment"],
        )

    submission_list = list(filter_submissions(submissions, user_list))
    if not submission_list:
        raise canvaslms.cli.EmptyListError("No submissions found matching the criteria")
    return submission_list


def list_submissions(assignments, include=["submission_comments"]):
    for assignment in assignments:
        submissions = assignment.get_submissions(include=include)
        for submission in submissions:
            submission.assignment = assignment
            yield submission


def list_ungraded_submissions(assignments, include=["submisson_comments"]):
    for assignment in assignments:
        submissions = assignment.get_submissions(bucket="ungraded", include=include)
        for submission in submissions:
            if submission.submitted_at and (
                submission.graded_at is None
                or not submission.grade_matches_current_submission
            ):
                submission.assignment = assignment
                yield submission


def filter_submissions(submission_list, user_list):
    user_list = set(user_list)

    for submission in submission_list:
        for user in user_list:
            if submission.user_id == user.id:
                submission.user = user
                yield submission
                break


def format_submission_short(submission):
    return [
        submission.assignment.course.course_code,
        submission.assignment.name,
        submission.user.name,
        submission.grade,
        canvaslms.cli.utils.format_local_time(submission.submitted_at),
        canvaslms.cli.utils.format_local_time(submission.graded_at),
    ]


def format_submission_short_unique(submission):
    uid = users.get_uid(submission.user)

    return [
        submission.assignment.course.course_code,
        submission.assignment.name,
        uid,
        submission.grade,
        canvaslms.cli.utils.format_local_time(submission.submitted_at),
        canvaslms.cli.utils.format_local_time(submission.graded_at),
    ]


def format_submission(
    submission,
    history=False,
    json_format=False,
    md_title_level="#",
    tmpdir=None,
    diff=False,
    diff_threshold_fixed=DEFAULT_DIFF_THRESHOLD_FIXED,
    diff_threshold_percent=DEFAULT_DIFF_THRESHOLD_PERCENT,
):
    """
    Formats submission for printing to stdout. Returns a string.

    If history is True, include all submission versions from history.

    If json_format is True, return a JSON string, otherwise Markdown.

    `md_title_level` is the level of the title in Markdown, by default `#`. This
    is used to create a hierarchy of sections in the output.

    `tmpdir` is the directory to store all the submission files. Defaults to None,
    which creates a temporary directory.

    `diff` is a boolean indicating whether to show diffs between submission versions
    instead of showing each version in full. Only works when `history` is True.
    `diff_threshold_fixed` and `diff_threshold_percent` control the matching
    sensitivity for renamed files (see [[match_renamed_files]] for details).
    """
    student = submission.assignment.course.get_user(submission.user_id)

    if json_format:
        formatted_submission = {}
    else:
        formatted_submission = ""

    metadata = {
        "course": submission.assignment.course.course_code,
        "assignment": submission.assignment.name,
        "student": str(student),
        "submission_id": submission.id,
        "submitted_at": canvaslms.cli.utils.format_local_time(submission.submitted_at),
        "graded_at": canvaslms.cli.utils.format_local_time(submission.graded_at),
        "grade": submission.grade,
        "graded_by": str(resolve_grader(submission)),
        "speedgrader": speedgrader(submission),
    }

    if json_format:
        formatted_submission.update(
            format_section(
                "metadata", metadata, json_format=True, md_title_level=md_title_level
            )
        )
    else:
        formatted_submission += format_section(
            "Metadata", metadata, md_title_level=md_title_level
        )
    try:
        if submission.rubric_assessment:
            if json_format:
                formatted_submission.update(
                    format_section(
                        "rubric_assessment", format_rubric(submission, json_format=True)
                    ),
                    json_format=True,
                )
            else:
                formatted_submission += format_section(
                    "Rubric assessment", format_rubric(submission)
                )
    except AttributeError:
        pass
    try:
        if submission.submission_comments:
            if json_format:
                formatted_submission.update(
                    format_section(
                        "comments", submission.submission_comments, json_format=True
                    )
                )
            else:
                body = ""
                for comment in submission.submission_comments:
                    created_at = canvaslms.cli.utils.format_local_time(
                        comment["created_at"]
                    )
                    body += f"{comment['author_name']} ({created_at}):\n\n"
                    body += comment["comment"] + "\n\n"
                formatted_submission += format_section("Comments", body)
    except AttributeError:
        pass
    if history:
        if diff:
            try:
                submission_history = submission.submission_history
            except AttributeError:
                pass
            else:
                if submission_history:
                    if json_format:
                        formatted_submission.update(
                            format_section(
                                "submission_diffs",
                                "Diffs not supported in JSON format",
                                json_format=True,
                                md_title_level=md_title_level,
                            )
                        )
                    else:
                        diff_output = ""
                        prev_content = None

                        for version, curr_submission_data in enumerate(
                            submission.submission_history
                        ):
                            curr_submission = canvasapi.submission.Submission(
                                submission._requester, curr_submission_data
                            )
                            curr_submission.assignment = submission.assignment

                            curr_content = extract_submission_text(
                                curr_submission, tmpdir / f"version-{version}"
                            )

                            if version == 0:
                                version_dir = tmpdir / f"version-{version}"
                                version_0_formatted = format_submission(
                                    curr_submission,
                                    tmpdir=version_dir,
                                    json_format=json_format,
                                    md_title_level=md_title_level + "##",
                                    diff=diff,
                                    diff_threshold_fixed=diff_threshold_fixed,
                                    diff_threshold_percent=diff_threshold_percent,
                                )
                                diff_output += format_section(
                                    f"Version {version} (Full Content)",
                                    version_0_formatted,
                                    md_title_level=md_title_level + "#",
                                )
                            else:
                                version_diff = generate_diff(
                                    prev_content,
                                    curr_content,
                                    f"Version {version-1}",
                                    f"Version {version}",
                                    diff_threshold_fixed,
                                    diff_threshold_percent,
                                )
                                if version_diff:
                                    diff_output += format_section(
                                        f"Version {version} "
                                        f"(Changes from Version {version-1})",
                                        version_diff,
                                        md_title_level=md_title_level + "#",
                                    )
                                else:
                                    diff_output += format_section(
                                        f"Version {version} "
                                        f"(Changes from Version {version-1})",
                                        "No textual differences found from "
                                        "previous version.",
                                        md_title_level=md_title_level + "#",
                                    )

                            prev_content = curr_content

                        if diff_output:
                            formatted_submission += format_section(
                                "Submission History with Diffs",
                                diff_output,
                                md_title_level=md_title_level,
                            )
                        else:
                            formatted_submission += format_section(
                                "Submission History with Diffs",
                                "No submission history found.",
                                md_title_level=md_title_level,
                            )
        else:
            try:
                submission_history = submission.submission_history
            except AttributeError:
                pass
            else:
                if submission_history:
                    versions = {}
                    for version, prev_submission in enumerate(
                        submission.submission_history
                    ):
                        version = str(version)
                        version_dir = tmpdir / f"version-{version}"

                        prev_submission = canvasapi.submission.Submission(
                            submission._requester, prev_submission
                        )
                        prev_submission.assignment = submission.assignment

                        prev_metadata = format_submission(
                            prev_submission,
                            tmpdir=version_dir,
                            json_format=json_format,
                            md_title_level=md_title_level + "#",
                            diff=diff,
                            diff_threshold_fixed=diff_threshold_fixed,
                            diff_threshold_percent=diff_threshold_percent,
                        )

                        versions[version] = prev_metadata
                        if json_format:
                            with open(version_dir / "metadata.json", "w") as f:
                                json.dump(prev_metadata, f, indent=2)
                        else:
                            with open(version_dir / "metadata.md", "w") as f:
                                f.write(prev_metadata)

                    if json_format:
                        formatted_submission.update(
                            format_section(
                                "submission_history",
                                versions,
                                json_format=True,
                                md_title_level=md_title_level,
                            )
                        )
                    else:
                        formatted_versions = ""
                        for version, prev_metadata in versions.items():
                            formatted_versions += format_section(
                                f"Version {version}",
                                prev_metadata,
                                md_title_level=md_title_level + "#",
                            )
                        formatted_submission += format_section(
                            "Submission history",
                            formatted_versions,
                            md_title_level=md_title_level,
                        )
    else:
        try:
            if submission.body:
                if json_format:
                    formatted_submission.update(
                        format_section(
                            "body",
                            submission.body,
                            json_format=True,
                            md_title_level=md_title_level,
                        )
                    )
                else:
                    formatted_submission += format_section(
                        "Body", submission.body, md_title_level=md_title_level
                    )
        except AttributeError:
            pass
        try:
            if submission.submission_data:
                if json_format:
                    formatted_submission.update(
                        format_section(
                            "quiz_answers",
                            submission.submission_data,
                            json_format=True,
                            md_title_level=md_title_level,
                        )
                    )
                else:
                    formatted_submission += format_section(
                        "Quiz answers",
                        json.dumps(submission.submission_data, indent=2),
                        md_title_level=md_title_level,
                    )
        except AttributeError:
            pass
        try:
            tmpdir = pathlib.Path(tmpdir or tempfile.mkdtemp())
            tmpdir.mkdir(parents=True, exist_ok=True)
            if json_format:
                attachments = {}
            for attachment in submission.attachments:
                contents = convert_to_md(attachment, tmpdir)
                formatted_attachment = format_section(
                    attachment.filename,
                    contents,
                    json_format=json_format,
                    md_title_level=md_title_level + "#",
                )

                if json_format:
                    attachments.update(formatted_attachment)
                else:
                    formatted_submission += formatted_attachment

            if json_format and attachments:
                formatted_submission.update(
                    format_section(
                        "attachments",
                        attachments,
                        json_format=True,
                        md_title_level=md_title_level,
                    )
                )
        except AttributeError:
            pass

    return formatted_submission


def format_section(title, body, json_format=False, md_title_level="#"):
    """
    In the case of Markdown (default), we format the title as a header and the body
    as a paragraph. If we don't do JSON, but receive a dictionary as the body, we
    format it as a list of key-value pairs.

    `md_title_level` is the level of the title in Markdown, by default `#`.
    We'll use this to create a hierarchy of sections in the output.

    In the case of JSON, we return a dictionary with the title as the key and the
    body as the value.
    """
    if json_format:
        return {title: body}

    if isinstance(body, dict):
        return "\n".join(
            [
                f" - {key.capitalize().replace('_', ' ')}: {value}"
                for key, value in body.items()
            ]
        )

    return f"\n{md_title_level} {title}\n\n{body}\n\n"


def resolve_grader(submission):
    """
    Returns a user object if the submission was graded by a human.
    Otherwise returns None if ungraded or a descriptive string.
    """
    try:
        if submission.grader_id is None:
            return None
    except AttributeError:
        return None

    if submission.grader_id < 0:
        return "autograded"

    try:
        return submission.assignment.course.get_user(submission.grader_id)
    except canvasapi.exceptions.ResourceDoesNotExist:
        return f"unknown grader {submission.grader_id}"


def convert_to_md(attachment: canvasapi.file.File, tmpdir: pathlib.Path) -> str:
    """
    Converts `attachment` to Markdown. Returns the Markdown string.

    Store a file version in `tmpdir`.
    """
    outfile = tmpdir / attachment.filename
    cached_path = attachment_cache.get_cached_attachment(attachment.id)

    if cached_path:
        # Use cached file - copy to temporary directory for processing
        import shutil

        shutil.copy(cached_path, outfile)
    else:
        # Download and cache for future use
        attachment.download(outfile)
        attachment_cache.cache_attachment(
            attachment.id,
            outfile,
            {
                "filename": attachment.filename,
                "size": getattr(attachment, "size", 0),
                "content_type": getattr(
                    attachment, "content-type", "application/octet-stream"
                ),
            },
        )
    content_type = getattr(attachment, "content-type")
    try:
        md_type = text_to_md(content_type)
        with open(outfile, "r") as f:
            contents = f.read()
        return f"```{md_type}\n{contents}\n```"
    except ValueError:
        pass
    if content_type.endswith("pdf"):
        try:
            return subprocess.check_output(["pdf2txt", str(outfile)], text=True)
        except subprocess.CalledProcessError:
            pass
    try:
        return pypandoc.convert_file(outfile, "markdown")
    except Exception as err:
        return (
            f"Cannot convert this file. " f"The file is located at\n\n  {outfile}\n\n"
        )


def text_to_md(content_type):
    """
    Takes a text-based content type, returns Markdown code block type.
    Raises ValueError if not possible.
    """
    if content_type.startswith("text/"):
        content_type = content_type[len("text/") :]
    else:
        raise ValueError(f"Not text-based content type: {content_type}")

    if content_type.startswith("x-"):
        content_type = content_type[2:]
    if content_type == "python-script":
        content_type = "python"

    return content_type


def extract_submission_text(submission, tmpdir):
    """
    Extracts text content from a submission for diff comparison.
    Returns a dictionary with keys for different content types.
    """
    content = {}

    try:
        if submission.body:
            content["body"] = submission.body
    except AttributeError:
        pass
    try:
        if submission.submission_data:
            content["quiz_answers"] = json.dumps(
                submission.submission_data, indent=2, sort_keys=True
            )
    except AttributeError:
        pass
    try:
        if submission.attachments:
            tmpdir = pathlib.Path(tmpdir)
            tmpdir.mkdir(parents=True, exist_ok=True)
            attachment_texts = {}

            for attachment in submission.attachments:
                try:
                    attachment_content = convert_to_md(attachment, tmpdir)
                    # Remove markdown code block markers for cleaner diff
                    lines = attachment_content.split("\n")
                    if (
                        len(lines) > 2
                        and lines[0].startswith("```")
                        and lines[-1].endswith("```")
                    ):
                        attachment_content = "\n".join(lines[1:-1])
                    attachment_texts[attachment.filename] = attachment_content
                except Exception:
                    attachment_texts[attachment.filename] = (
                        "[Could not convert attachment to text]"
                    )

            if attachment_texts:
                content["attachments"] = attachment_texts
    except AttributeError:
        pass

    return content


def generate_diff(
    prev_content,
    curr_content,
    prev_label,
    curr_label,
    diff_threshold_fixed=DEFAULT_DIFF_THRESHOLD_FIXED,
    diff_threshold_percent=DEFAULT_DIFF_THRESHOLD_PERCENT,
):
    """
    Generates a unified diff between two content dictionaries. Each key
    represents a part of the submission (body, quiz_answers, attachments).
    The attachments key contains itself a dictionary of filename to content.

    The diff_threshold parameters control renamed file matching sensitivity.

    Returns a string with the diff output, or None if no differences.
    """
    diff_lines = []

    all_keys = (set(prev_content.keys()) | set(curr_content.keys())) - {"attachments"}

    for key in sorted(all_keys):
        prev_text = prev_content.get(key, "")
        curr_text = curr_content.get(key, "")

        if prev_text != curr_text:
            content_diff = list(
                difflib.unified_diff(
                    prev_text.splitlines(keepends=True) if prev_text else [],
                    curr_text.splitlines(keepends=True) if curr_text else [],
                    fromfile=f"{prev_label}/{key}",
                    tofile=f"{curr_label}/{key}",
                    lineterm="",
                )
            )
            if content_diff:
                diff_lines.extend(content_diff)
                diff_lines.append("\n")
    prev_attachments = prev_content.get("attachments", {})
    curr_attachments = curr_content.get("attachments", {})

    # Dictionary to track original filenames for matched files
    # Maps current filename -> original filename in previous version
    filename_mapping = {}

    # Find renamed files using edit distance matching
    filename_mapping = match_renamed_files(
        prev_attachments, curr_attachments, diff_threshold_fixed, diff_threshold_percent
    )

    # Rename files in prev_attachments to match current names
    for curr_filename, prev_filename in filename_mapping.items():
        prev_attachments[curr_filename] = prev_attachments.pop(prev_filename)

    all_files = set(prev_attachments.keys()) | set(curr_attachments.keys())

    for filename in sorted(all_files):
        prev_file_content = prev_attachments.get(filename, "")
        curr_file_content = curr_attachments.get(filename, "")

        if prev_file_content != curr_file_content:
            # Use original filename if this file was matched despite name difference
            prev_filename_for_diff = filename_mapping.get(filename, filename)

            file_diff = list(
                difflib.unified_diff(
                    prev_file_content.splitlines(keepends=True),
                    curr_file_content.splitlines(keepends=True),
                    fromfile=f"{prev_label}/{prev_filename_for_diff}",
                    tofile=f"{curr_label}/{filename}",
                    lineterm="",
                )
            )
            if file_diff:
                diff_lines.extend(file_diff)
                diff_lines.append("\n")

    if diff_lines:
        # Ensure each line ends with a newline for proper rendering
        formatted_lines = []
        for line in diff_lines:
            if line == "\n":
                formatted_lines.append(line)
            elif not line.endswith("\n"):
                formatted_lines.append(line + "\n")
            else:
                formatted_lines.append(line)
        return "```diff\n" + "".join(formatted_lines) + "```"
    return None


def get_file_extension(filename):
    """
    Extract file extension from filename.
    Returns extension including the dot (e.g., '.py') or empty string if none.
    """
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1]
    return ""


def get_file_base(filename):
    """
    Extract base filename without extension.
    """
    if "." in filename:
        return filename.rsplit(".", 1)[0]
    return filename


def compute_edit_distance(str1, str2):
    """
    Compute Levenshtein edit distance between two strings.

    Returns the minimum number of single-character edits (insertions,
    deletions, or substitutions) needed to transform str1 into str2.
    """
    m, n = len(str1), len(str2)

    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Base cases
    for i in range(m + 1):
        dp[i][0] = i  # Delete all characters from str1
    for j in range(n + 1):
        dp[0][j] = j  # Insert all characters from str2

    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                # Characters match, no edit needed
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # Take minimum of insert, delete, substitute
                dp[i][j] = 1 + min(
                    dp[i - 1][j],  # Delete from str1
                    dp[i][j - 1],  # Insert from str2
                    dp[i - 1][j - 1],  # Substitute
                )

    return dp[m][n]


def match_renamed_files(
    prev_attachments,
    curr_attachments,
    fixed_threshold=DEFAULT_DIFF_THRESHOLD_FIXED,
    percent_threshold=DEFAULT_DIFF_THRESHOLD_PERCENT,
):
    """
    Match files across versions using edit distance.

    Args:
      prev_attachments: Dictionary of previous version's attachments
      curr_attachments: Dictionary of current version's attachments
      fixed_threshold: Maximum edit distance for a match
                      (default: DEFAULT_DIFF_THRESHOLD_FIXED)
      percent_threshold: Maximum distance as percentage of filename length
                        (default: DEFAULT_DIFF_THRESHOLD_PERCENT)

    Returns a dictionary mapping current filename -> previous filename
    for files that appear to be renames.
    """
    candidates = []

    for curr_filename in curr_attachments:
        curr_ext = get_file_extension(curr_filename)
        curr_base = get_file_base(curr_filename)

        for prev_filename in prev_attachments:
            # Only match files with same extension
            prev_ext = get_file_extension(prev_filename)
            if prev_ext != curr_ext or not prev_ext:
                continue

            # Skip if names are identical (will be matched automatically later)
            if curr_filename == prev_filename:
                continue

            prev_base = get_file_base(prev_filename)
            distance = compute_edit_distance(prev_base, curr_base)

            candidates.append((distance, curr_filename, prev_filename))
    filename_mapping = {}
    matched_prev = set()
    matched_curr = set()

    # Sort by distance (ascending)
    candidates.sort(key=lambda x: x[0])

    for distance, curr_filename, prev_filename in candidates:
        # Skip if either file already matched
        if curr_filename in matched_curr or prev_filename in matched_prev:
            continue

        # Conservative threshold: distance <= fixed or <= percent% of base length
        curr_base = get_file_base(curr_filename)
        prev_base = get_file_base(prev_filename)
        max_base_len = max(len(curr_base), len(prev_base))
        threshold = max(fixed_threshold, int(percent_threshold / 100.0 * max_base_len))

        if distance <= threshold:
            filename_mapping[curr_filename] = prev_filename
            matched_curr.add(curr_filename)
            matched_prev.add(prev_filename)

    return filename_mapping


def format_rubric(submission, json_format=False):
    """
    Format the rubric assessment of the `submission` in readable form.

    If `json_format` is True, return a JSON string, otherwise Markdown.
    """

    if json_format:
        result = {}
    else:
        result = ""

    for crit_id, rating_data in submission.rubric_assessment.items():
        criterion = get_criterion(crit_id, submission.assignment.rubric)
        rating = get_rating(rating_data["rating_id"], criterion)
        try:
            comments = rating_data["comments"]
        except KeyError:
            comments = ""

        if json_format:
            result[criterion["description"]] = {
                "rating": rating["description"] if rating else None,
                "points": rating["points"] if rating else None,
                "comments": comments,
            }
        else:
            result += f"- {criterion['description']}: "
            if rating:
                result += f"{rating['description']} ({rating['points']})"
            else:
                result += "-"
            result += "\n"
            if comments:
                result += textwrap.indent(textwrap.fill(f"- Comment: {comments}"), "  ")
                result += "\n"

        if not json_format:
            result += "\n"

    return result.strip()


def get_criterion(criterion_id, rubric):
    """Returns criterion with ID `criterion_id` from rubric `rubric`"""
    for criterion in rubric:
        if criterion["id"] == criterion_id:
            return criterion

    return None


def get_rating(rating_id, criterion):
    """Returns rating with ID `rating_id` from rubric criterion `criterion`"""
    for rating in criterion["ratings"]:
        if rating["id"] == rating_id:
            return rating

    return None


def submissions_grade_command(config, canvas, args):
    submission_list = process_submission_options(canvas, args)
    results = {}
    if args.grade:
        results["submission"] = {"posted_grade": args.grade}
    if args.message:
        results["comment"] = {"text_comment": args.message}
    if not args.grade and not args.message:
        for submission in submission_list:
            webbrowser.open(speedgrader(submission))
    else:
        for submission in submission_list:
            logger.info(
                f"Grading {submission.assignment.course.course_code} "
                f"{submission.assignment.name} for {submission.user.name}"
            )
            if args.grade:
                logger.info(f"  Setting grade to: {args.grade}")
            if args.message:
                logger.info(f"  Adding comment: {args.message}")
            try:
                submission.edit(**results)
            except canvasapi.exceptions.Forbidden as err:
                canvaslms.cli.err(
                    1,
                    f"Permission denied when grading {submission.assignment.name} "
                    f"for {submission.user}. "
                    f"Hint: The assignment may not be published yet, or you may not have "
                    f"permission to grade this assignment. "
                    f"Canvas error: {err}",
                )
            except canvasapi.exceptions.Unauthorized as err:
                canvaslms.cli.err(
                    1,
                    f"Unauthorized to grade {submission.assignment.name} "
                    f"for {submission.user}. "
                    f"Hint: Check your Canvas permissions or verify your authentication token. "
                    f"Canvas error: {err}",
                )
            except canvasapi.exceptions.CanvasException as err:
                canvaslms.cli.err(
                    1,
                    f"Canvas API error when grading {submission.assignment.name} "
                    f"for {submission.user}. "
                    f"Canvas error: {err}",
                )


def add_command(subp):
    """Adds the submissions command with subcommands to argparse parser subp"""
    add_submissions_command(subp)
    add_submission_command(subp)


def add_submissions_command(subp):
    """Adds the submissions command with subcommands to argparse parser subp"""
    submissions_parser = subp.add_parser(
        "submissions",
        help="Submission management commands",
        description="Commands for managing submissions: list, view, and grade.",
    )

    # Create subparsers for submissions subcommands
    # Set required=False to allow bare "submissions" command to default to list
    submissions_subp = submissions_parser.add_subparsers(
        title="submissions subcommands", dest="submissions_subcommand", required=False
    )

    # Set default function for bare "submissions" command (defaults to list)
    submissions_parser.set_defaults(func=submissions_list_command)

    # Add arguments for the default list behavior to main parser
    # These are needed when submissions is invoked without a subcommand
    # We suppress help to keep the help output focused on subcommands
    assignments.add_assignment_option(submissions_parser, suppress_help=True)
    add_submission_options(submissions_parser, suppress_help=True)
    submissions_parser.add_argument(
        "-H", "--history", action="store_true", help=argparse.SUPPRESS
    )
    submissions_parser.add_argument(
        "-l", "--login-id", default=False, action="store_true", help=argparse.SUPPRESS
    )

    # Add list subcommand (was the old "submissions" command)
    list_parser = submissions_subp.add_parser(
        "list",
        help="List submissions of an assignment",
        description="Lists submissions of assignment(s). Output format: "
        "<course code> <assignment name> <user> <grade> "
        "<submission date> <grade date>",
    )
    list_parser.set_defaults(func=submissions_list_command)
    assignments.add_assignment_option(list_parser)
    add_submission_options(list_parser)
    list_parser.add_argument(
        "-H", "--history", action="store_true", help="Include submission history."
    )
    list_parser.add_argument(
        "-l",
        "--login-id",
        help="Print login ID instead of name.",
        default=False,
        action="store_true",
    )
    # Add view subcommand (was the old "submission" command)
    view_parser = submissions_subp.add_parser(
        "view",
        help="View information about a submission",
        description="""
  Prints data about matching submissions, including submission and grading time, 
  and any text-based attachments.

  We also need the corresponding function.
  For now, we only print the most relevant data of a submission.
  Uses MANPAGER or PAGER environment variables for the pager to page output. If 
  the `-r` or `-R` flag is passed to `less`, it uses colours in the output. That 
  is, set `PAGER=less -r` or `PAGER=less -R` to get coloured output from this 
  command.

  """,
    )
    view_parser.set_defaults(func=submissions_view_command)
    add_submission_options(view_parser)
    add_view_options(view_parser)
    # Add grade subcommand (was the old "grade" command)
    grade_parser = submissions_subp.add_parser(
        "grade",
        help="Grade submissions (hic sunt dracones!)",
        description="Grades submissions. ***Hic sunt dracones [here be dragons]***: "
        "the regex matching is very powerful, "
        "be certain that you match what you think!",
    )
    grade_parser.set_defaults(func=submissions_grade_command)
    add_submission_options(grade_parser, required=True)
    add_grading_options(grade_parser)


def add_submission_command(subp):
    """Adds the submission (singular) command as an alias for submissions view"""
    submission_parser = subp.add_parser(
        "submission",
        help="View information about a submission (alias for 'submissions view')",
        description="""
  Prints data about matching submissions, including submission and grading time, 
  and any text-based attachments.

  We also need the corresponding function.
  For now, we only print the most relevant data of a submission.
  Uses MANPAGER or PAGER environment variables for the pager to page output. If 
  the `-r` or `-R` flag is passed to `less`, it uses colours in the output. That 
  is, set `PAGER=less -r` or `PAGER=less -R` to get coloured output from this 
  command.

  """,
    )
    submission_parser.set_defaults(func=submissions_view_command)
    add_submission_options(submission_parser)
    add_view_options(submission_parser)
