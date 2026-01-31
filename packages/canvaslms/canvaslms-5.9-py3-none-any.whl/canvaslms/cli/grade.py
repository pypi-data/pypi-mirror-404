from canvaslms.cli import submissions


def add_command(subp):
    """Adds grade command to the argparse subparser subp as an alias"""
    grade_parser = subp.add_parser(
        "grade",
        help="Grade submissions, hic sunt dracones! " "(alias for 'submissions grade')",
        description="Grades submissions. ***Hic sunt dracones [here be dragons]***: "
        "the regex matching is very powerful, "
        "be certain that you match what you think!",
    )
    grade_parser.set_defaults(func=submissions.submissions_grade_command)
    submissions.add_submission_options(grade_parser, required=True)
    submissions.add_grading_options(grade_parser)
