"""A command-line interface for the Canvas LMS."""

import appdirs
import argcomplete, argparse
from canvasapi import Canvas
import canvaslms.cli.login
import json
import logging
import os
import pathlib
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import canvaslms.cli.login
import canvaslms.cli.courses
import canvaslms.cli.modules
import canvaslms.cli.users
import canvaslms.cli.assignments
import canvaslms.cli.submissions
import canvaslms.cli.grade
import canvaslms.cli.results
import canvaslms.cli.calendar
import canvaslms.cli.discussions
import canvaslms.cli.quizzes
import canvaslms.cli.pages
import canvaslms.cli.cache

logger = logging.getLogger(__name__)
dirs = appdirs.AppDirs("canvaslms", "dbosk@kth.se")


class EmptyListError(Exception):
    """Exception raised when a process function returns an empty list"""

    pass


def err(rc, msg):
    """Logs error msg and exits with rc as return code"""
    logger.error(f"{sys.argv[0]}: {msg}")
    sys.exit(rc)


def warn(msg):
    """Logs warning msg"""
    logger.warning(f"{sys.argv[0]}: {msg}")


def read_configuration(config_file):
    """Returns a dictionary containing the configuration"""
    config = {}

    try:
        with open(config_file, "r") as file:
            config.update(json.load(file))
    except FileNotFoundError:
        pass
    except json.decoder.JSONDecodeError as err:
        warn(f"config file is malformed: {err}")
    if "canvas" not in config:
        config["canvas"] = {}

    if "CANVAS_SERVER" in os.environ:
        config["canvas"]["host"] = os.environ["CANVAS_SERVER"]

    if "CANVAS_TOKEN" in os.environ:
        config["canvas"]["access_token"] = os.environ["CANVAS_TOKEN"]

    return config


def update_config_file(config, config_file):
    """Updates the config file by writing the config dictionary back to it"""
    try:
        with open(config_file, "w") as fd:
            json.dump(config, fd)
    except FileNotFoundError:
        os.makedirs(pathlib.PurePath(config_file).parent)
        with open(config_file, "w") as fd:
            json.dump(config, fd)


def main():
    argp = argparse.ArgumentParser(
        description="Scriptable Canvas LMS",
        epilog="Copyright (c) 2020--2026 Daniel Bosk. Licensed under the MIT License.\n"
        "Web: https://github.com/dbosk/canvaslms",
    )

    subp = argp.add_subparsers(title="commands", dest="command", required=True)

    argp.add_argument(
        "-f",
        "--config-file",
        default=f"{dirs.user_config_dir}/config.json",
        help="Path to configuration file "
        f"(default: {dirs.user_config_dir}/config.json) "
        "or set CANVAS_SERVER and CANVAS_TOKEN environment variables.",
    )
    argp.add_argument(
        "-d",
        "--delimiter",
        default="\t",
        help="Sets the delimiter for CSV output, the default is the tab character",
    )
    argp.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Decrease verbosity: -q=ERROR only, -qq=CRITICAL only, -qqq=silent",
    )
    argp.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity: -v=INFO, -vv=DEBUG, -vvv=all library debug",
    )
    canvaslms.cli.login.add_command(subp)
    canvaslms.cli.courses.add_command(subp)
    canvaslms.cli.modules.add_command(subp)
    canvaslms.cli.users.add_command(subp)
    canvaslms.cli.assignments.add_command(subp)
    canvaslms.cli.submissions.add_command(subp)
    canvaslms.cli.grade.add_command(subp)
    canvaslms.cli.results.add_command(subp)
    canvaslms.cli.calendar.add_command(subp)
    canvaslms.cli.discussions.add_command(subp)
    canvaslms.cli.quizzes.add_command(subp)
    canvaslms.cli.pages.add_command(subp)
    canvaslms.cli.cache.add_command(subp)

    argcomplete.autocomplete(argp)
    args = argp.parse_args()

    net_verbosity = args.verbose - args.quiet

    if net_verbosity <= -3:
        # -qqq or more: completely silent
        level = logging.CRITICAL + 1
    elif net_verbosity == -2:
        # -qq: critical only
        level = logging.CRITICAL
    elif net_verbosity == -1:
        # -q: errors and critical
        level = logging.ERROR
    elif net_verbosity == 0:
        # default: warnings and above
        level = logging.WARNING
    elif net_verbosity == 1:
        # -v: info and above
        level = logging.INFO
    elif net_verbosity == 2:
        # -vv: debug and above
        level = logging.DEBUG
    else:  # net_verbosity >= 3
        # -vvv or more: everything including library debug messages
        level = logging.NOTSET
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")

    config = read_configuration(args.config_file)

    if (
        args.func == canvaslms.cli.login.login_command
        or (args.func == canvaslms.cli.quizzes.analyse_command and args.csv)
        or args.func == canvaslms.cli.cache.clear_command
    ):
        canvas = None
    else:
        hostname, token = canvaslms.cli.login.load_credentials(config)

        if not (hostname and token):
            err(1, "No hostname or token, run `canvaslms login`")

        if "://" not in hostname:
            hostname = f"https://{hostname}"

        canvas = canvaslms.cli.cache.load_canvas_cache(token, hostname)

        if not canvas:
            canvas = Canvas(hostname, token)
            retry_strategy = Retry(
                total=10,
                backoff_factor=2,
                backoff_max=256,
                backoff_jitter=0.3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=[
                    "HEAD",
                    "GET",
                    "PUT",
                    "DELETE",
                    "OPTIONS",
                    "TRACE",
                    "POST",
                ],
                respect_retry_after_header=True,
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            canvas._Canvas__requester._session.mount("https://", adapter)
            canvas._Canvas__requester._session.mount("http://", adapter)

    if args.func:
        try:
            args.func(config, canvas, args)
            if canvas:
                canvaslms.cli.cache.save_canvas_cache(canvas, token, hostname)
        except EmptyListError as e:
            if args.quiet == 0:
                err(1, str(e))
            else:
                sys.exit(1)
