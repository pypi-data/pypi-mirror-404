import argparse
import canvasapi.exceptions
import canvaslms.cli
import canvaslms.cli.courses as courses
import canvaslms.cli.utils as utils
import csv
import datetime
import json
import sys
import arrow
import re
import textwrap


def format_canvas_time(iso_ts):
    """
    Parses an ISO timestamp string as local time and converts to UTC ISO format.
    """
    if not iso_ts:
        return None
    try:
        if isinstance(iso_ts, datetime.datetime):
            # Already a datetime object
            dt = iso_ts
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=arrow.now().tzinfo)
            return (
                dt.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            )
        elif isinstance(iso_ts, datetime.date):
            # Date only, interpret as start of day in local timezone
            dt = datetime.datetime.combine(iso_ts, datetime.time(0, 0))
            dt = dt.replace(tzinfo=arrow.now().tzinfo)
            return (
                dt.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            )
        elif isinstance(iso_ts, arrow.Arrow):
            return iso_ts.to("utc").isoformat().replace("+00:00", "Z")
        elif isinstance(iso_ts, str):
            return (
                arrow.get(iso_ts, tzinfo="local")
                .to("utc")
                .isoformat()
                .replace("+00:00", "Z")
            )
    except Exception as e:
        raise ValueError(f"Invalid date/time format: {e}")


def add_calendar_list_command(subp):
    """Adds the calendar list subcommand and its options to argparse subparser subp"""
    calendar_list_parser = subp.add_parser(
        "list",
        help="Lists calendar events",
        description="Lists calendar events. Output, CSV-format: "
        "<event-id> <title> <start-time> <end-time> <context-type> <context-name>",
    )
    calendar_list_parser.set_defaults(func=calendar_list_command)
    courses.add_course_option(calendar_list_parser)
    calendar_list_parser.add_argument(
        "--delimiter",
        "-D",
        default="\t",
        help="Delimiter for CSV output (default: tab)",
    )
    calendar_list_parser.add_argument(
        "--type", choices=["event", "assignment"], help="Filter by event type"
    )
    add_time_filtering_arguments(calendar_list_parser)
    calendar_list_parser.add_argument(
        "--bookings",
        "-b",
        action="store_true",
        default=False,
        help="Output one line per booked student and one line for free slots "
        "(only for appointment group events)",
    )


def calendar_list_command(config, canvas, args):
    """Lists calendar events in CSV format to stdout"""
    output = csv.writer(sys.stdout, delimiter=args.delimiter)

    course_list = courses.process_course_option(canvas, args)
    if args.on:
        try:
            start_time = arrow.get(args.on, "YYYY-MM-DD HH:mm").to("utc")
            end_time = start_time
        except Exception:
            try:
                start_time = arrow.get(args.on, "YYYY-MM-DD").to("utc")
                end_time = start_time.shift(days=1)
            except Exception as e:
                canvaslms.cli.err(1, f"Invalid date format for --on: {e}")

        start_time = start_time.format()
        end_time = end_time.format()
    else:
        try:
            start_time = (
                arrow.get(args.start_time, "YYYY-MM-DD HH:mm").to("utc").format()
            )
        except:
            try:
                start_time = arrow.get(args.start_time, "YYYY-MM-DD").to("utc").format()
            except Exception as e:
                canvaslms.cli.err(1, f"Invalid date format for --start-time: {e}")
        try:
            end_time = arrow.get(args.end_time, "YYYY-MM-DD HH:mm").to("utc").format()
        except:
            try:
                end_time = arrow.get(args.end_time, "YYYY-MM-DD").to("utc").format()
            except Exception as e:
                canvaslms.cli.err(1, f"Invalid date format for --end-time: {e}")

    start_time = utils.format_canvas_time(start_time)
    end_time = utils.format_canvas_time(end_time)
    try:
        events = get_calendar_events(
            canvas,
            course_list=course_list,
            start_time=start_time,
            end_time=end_time,
            event_type=args.type,
        )

        for event in events:
            start_at = canvaslms.cli.utils.format_local_time(
                getattr(event, "start_at", None)
            )
            end_at = canvaslms.cli.utils.format_local_time(
                getattr(event, "end_at", None)
            )

            try:
                num_booked = event.participants_per_appointment - event.available_slots
                participants = f"{num_booked}/{event.participants_per_appointment}"
            except AttributeError:
                participants = ""

            if args.bookings:
                try:
                    slots = event.child_events
                except AttributeError:
                    pass
                else:
                    if event.available_slots:
                        output.writerow(
                            [
                                event.title,
                                start_at,
                                end_at,
                                f"{event.available_slots} free slots",
                            ]
                        )
                    if slots:
                        for slot in slots:
                            user_name = slot["user"]["name"]
                            user_uname = slot["user"]["login_id"]
                            output.writerow(
                                [
                                    slot["title"],
                                    canvaslms.cli.utils.format_local_time(
                                        slot["start_at"]
                                    ),
                                    canvaslms.cli.utils.format_local_time(
                                        slot["end_at"]
                                    ),
                                    f"{user_name} ({user_uname})",
                                ]
                            )
            else:
                output.writerow(
                    [
                        event.title,
                        start_at,
                        end_at,
                        participants,
                    ]
                )

    except canvasapi.exceptions.CanvasException as e:
        canvaslms.cli.err(1, f"Failed to get calendar events: {e}")


def add_time_filtering_arguments(parser):
    """Adds time filtering arguments to the given argparse parser"""
    parser.add_argument(
        "--on",
        help="Single date (YYYY-MM-DD) or time (YYYY-MM-DD HH:mm ) "
        "to search on (overrides start/end times)",
    )
    parser.add_argument(
        "--start-time",
        default=arrow.now().format("YYYY-MM-DD HH:mm"),
        help="Start date for search (YYYY-MM-DD [HH:mm], default: now)",
    )
    parser.add_argument(
        "--end-time",
        default=arrow.now().shift(weeks=1).format("YYYY-MM-DD HH:mm"),
        help="End date for search (YYYY-MM-DD [HH:mm], " "default: one week from now.)",
    )


def get_calendar_events(
    canvas, course_list=None, start_time=None, end_time=None, event_type=None
):
    """Fetches calendar events from Canvas with optional filters"""
    params = {}
    if course_list:
        context_codes = [f"course_{course.id}" for course in course_list]
    else:
        context_codes = None
    if context_codes:
        params["context_codes"] = context_codes
    if start_time:
        params["start_date"] = start_time
    if end_time:
        params["end_date"] = end_time
    if event_type:
        params["type"] = event_type

    return canvas.get_calendar_events(**params)


def add_calendar_show_command(subp):
    """Adds the calendar show subcommand and its options to argparse subparser subp"""
    calendar_show_parser = subp.add_parser(
        "show",
        help="Shows details of upcoming calendar events by regex/date",
        description="Shows details of one or more calendar events matched "
        "by regex and/or dates. Defaults to the first event in "
        "the coming week.",
    )
    calendar_show_parser.set_defaults(func=calendar_show_command)
    # Regex to match course
    courses.add_course_option(calendar_show_parser)
    # Regex to match against event title/description
    calendar_show_parser.add_argument(
        "--match",
        help="Regular expression to match against event title and description",
    )
    calendar_show_parser.add_argument(
        "--title", "-t", help="Regular expression to match against event title"
    )
    calendar_show_parser.add_argument(
        "--description",
        "-d",
        help="Regular expression to match against event description",
    )
    calendar_show_parser.add_argument(
        "--ignore-case",
        "-i",
        action="store_true",
        help="Make the regex case-insensitive",
    )

    add_time_filtering_arguments(calendar_show_parser)

    # How many events to print
    calendar_show_parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1,
        help="Number of matching events to show (default: 1), "
        "set to 0 to show all matches",
    )
    calendar_show_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output matching events as JSON",
    )


def calendar_show_command(config, canvas, args):
    """Shows details of one or more calendar events matched by regex/date"""
    if args.on:
        try:
            start_time = arrow.get(args.on, "YYYY-MM-DD HH:mm").to("utc")
            end_time = start_time
        except Exception:
            try:
                start_time = arrow.get(args.on, "YYYY-MM-DD").to("utc")
                end_time = start_time.shift(days=1)
            except Exception as e:
                canvaslms.cli.err(1, f"Invalid date format for --on: {e}")

        start_time = start_time.format()
        end_time = end_time.format()
    else:
        try:
            start_time = (
                arrow.get(args.start_time, "YYYY-MM-DD HH:mm").to("utc").format()
            )
        except:
            try:
                start_time = arrow.get(args.start_time, "YYYY-MM-DD").to("utc").format()
            except Exception as e:
                canvaslms.cli.err(1, f"Invalid date format for --start-time: {e}")
        try:
            end_time = arrow.get(args.end_time, "YYYY-MM-DD HH:mm").to("utc").format()
        except:
            try:
                end_time = arrow.get(args.end_time, "YYYY-MM-DD").to("utc").format()
            except Exception as e:
                canvaslms.cli.err(1, f"Invalid date format for --end-time: {e}")

    start_time = utils.format_canvas_time(start_time)
    end_time = utils.format_canvas_time(end_time)
    pattern = None
    if args.match:
        try:
            flags = re.IGNORECASE if args.ignore_case else 0
            pattern = re.compile(args.match, flags)
        except re.error as e:
            canvaslms.cli.err(1, f"Invalid regex for --match: {e}")

    title_pattern = None
    if args.title:
        try:
            flags = re.IGNORECASE if args.ignore_case else 0
            title_pattern = re.compile(args.title, flags)
        except re.error as e:
            canvaslms.cli.err(1, f"Invalid regex for --title: {e}")

    desc_pattern = None
    if args.description:
        try:
            flags = re.IGNORECASE if args.ignore_case else 0
            desc_pattern = re.compile(args.description, flags)
        except re.error as e:
            canvaslms.cli.err(1, f"Invalid regex for --description: {e}")

    # Prepare parameters for API call
    params = {}

    # Process course option
    context_codes = []
    course_list = courses.process_course_option(canvas, args)
    if course_list:
        context_codes = [f"course_{course.id}" for course in course_list]
    if context_codes:
        params["context_codes"] = context_codes

    if start_time:
        params["start_date"] = start_time
    if end_time:
        params["end_date"] = end_time

    try:
        events = canvas.get_calendar_events(**params)
    except canvasapi.exceptions.CanvasException as e:
        canvaslms.cli.err(1, f"Failed to get calendar events: {e}")

    def matches(event):
        if not (pattern or title_pattern or desc_pattern):
            return True

        title = getattr(event, "title", "") or ""
        desc = getattr(event, "description", "") or ""
        text = f"{title}\n{desc}"

        if title_pattern and title_pattern.search(title):
            return True
        if desc_pattern and desc_pattern.search(desc):
            return True
        if pattern and pattern.search(text):
            return True

        return False

    filtered = [e for e in events if matches(e)]

    # Sort by start time ascending
    def start_key(ev):
        ts = getattr(ev, "start_at", None)
        try:
            return arrow.get(ts).float_timestamp
        except Exception:
            return float("inf")

    filtered.sort(key=start_key)

    # Take the top N
    if args.count == 0:
        count = len(filtered)  # Show all matches
    else:
        count = max(1, args.count)

    selected = filtered[:count]

    if not selected:
        canvaslms.cli.err(1, "No matching events found in the specified date range")

    if args.json:
        print(repr(selected))
    else:
        # Print each event's details
        for idx, event in enumerate(selected):
            print_event_details(event)
            if idx != len(selected) - 1:
                print()


def print_event_details(event):
    """Formats and prints details of a calendar event"""
    print(f"Title:    {getattr(event, 'title', 'N/A')}")

    print(
        f"Start:    {canvaslms.cli.utils.format_local_time(getattr(event, 'start_at', None))}"
    )
    print(
        f"End:      {canvaslms.cli.utils.format_local_time(getattr(event, 'end_at', None))}"
    )

    description = getattr(event, "description", "N/A")
    if description and description != "N/A":
        # Split description into lines and wrap each line individually
        lines = description.split("\n")
        first_line = True

        for line in lines:
            if first_line:
                # First line gets "Description: " prefix
                if line.strip():  # Non-empty line
                    wrapped = textwrap.fill(
                        line,
                        width=80,
                        initial_indent="Description: ",
                        subsequent_indent="             ",
                    )
                    print(wrapped)
                else:
                    print("Description: ")
                first_line = False
            else:
                # Subsequent lines get proper indentation
                if line.strip():  # Non-empty line
                    wrapped = textwrap.fill(
                        line,
                        width=80,
                        initial_indent="             ",
                        subsequent_indent="             ",
                    )
                    print(wrapped)
                else:
                    print("             ")  # Preserve empty lines with indentation
    else:
        print(f"Description: {description}")

    print(f"Location: {getattr(event, 'location_name', 'N/A')}")
    try:
        num_booked = event.participants_per_appointment - event.available_slots
        print(f"Participants: " f"{num_booked} / {event.participants_per_appointment}")
    except AttributeError:
        pass  # Not an appointment group event

    try:
        for slot in event.child_events:
            user_name = slot["user"]["name"]
            user_uname = slot["user"]["login_id"]
            print(f"  {user_name} ({user_uname})")
    except AttributeError:
        pass  # Not an appointment group event

    print(f"URL:      {getattr(event, 'html_url', 'N/A')}")


def add_calendar_create_command(subp):
    """Adds the calendar create subcommand and its options to argparse subparser subp"""
    calendar_create_parser = subp.add_parser(
        "create",
        help="Creates a new calendar event",
        description="Creates a new calendar event or appointment group for bookable time slots",
    )
    calendar_create_parser.set_defaults(func=calendar_create_command)
    courses.add_course_option(calendar_create_parser)
    calendar_create_parser.add_argument("title", help="Title of the calendar event")
    calendar_create_parser.add_argument(
        "--start-time", required=True, help="Start time (ISO format: YYYY-MM-DD HH:mm)"
    )
    calendar_create_parser.add_argument(
        "--end-time", help="End time (ISO format: YYYY-MM-DD HH:mm)"
    )
    calendar_create_parser.add_argument(
        "--description", help="Description of the event"
    )
    calendar_create_parser.add_argument("--location", help="Location of the event")
    calendar_create_parser.add_argument(
        "--event-type",
        choices=["event", "appointment_group"],
        default="event",
        help="Type of calendar event to create (default: event)",
    )
    calendar_create_parser.add_argument(
        "--time-slot-duration",
        type=int,
        help="Duration in minutes for each bookable time slot (only for appointment_group type)",
    )
    calendar_create_parser.add_argument(
        "--max-appointments",
        type=int,
        default=1,
        help="Maximum appointments per time slot (only for appointment_group type, default: 1)",
    )


def calendar_create_command(config, canvas, args):
    """Creates a new calendar event"""
    try:
        start_time = utils.format_canvas_time(
            arrow.get(args.start_time, tzinfo="local")
        )
        end_time = utils.format_canvas_time(arrow.get(args.end_time, tzinfo="local"))
    except Exception as e:
        canvaslms.cli.err(
            1,
            f"Invalid date/time format: {e} " f"(did you write 8:15 instead of 08:15?)",
        )

    if end_time < start_time:
        canvaslms.cli.err(1, "End time cannot be before start time.")

    try:
        if args.event_type == "appointment_group":
            params = {
                "appointment_group": {
                    "title": args.title,
                    "participants_per_appointment": args.max_appointments,
                    "max_appointments_per_participant": 1,
                    "min_appointments_per_participant": 1,
                    "publish": True,
                }
            }

            if args.description:
                params["appointment_group"]["description"] = args.description
            if args.location:
                params["appointment_group"]["location_name"] = args.location

            if not args.time_slot_duration:
                canvaslms.cli.err(
                    1, "--time-slot-duration is required for appointment groups"
                )

            params["appointment_group"]["new_appointments"] = {}

            slot_duration = datetime.timedelta(minutes=args.time_slot_duration)
            current_start = arrow.get(start_time)
            end = arrow.get(end_time)

            slot_num = 0
            while current_start + slot_duration <= end:
                slot = [
                    utils.format_canvas_time(current_start),
                    utils.format_canvas_time(current_start + slot_duration),
                ]
                params["appointment_group"]["new_appointments"][str(slot_num)] = slot
                current_start += slot_duration
                slot_num += 1

            # Set context if course is specified
            if hasattr(args, "course") and args.course:
                course_list = courses.process_course_option(canvas, args)
                for course in course_list:
                    try:
                        params["appointment_group"]["context_codes"].append(
                            f"course_{course.id}"
                        )
                    except KeyError:
                        params["appointment_group"]["context_codes"] = [
                            f"course_{course.id}"
                        ]

            appointment_group = canvas.create_appointment_group(**params)
        else:
            params = {
                "calendar_event": {
                    "title": args.title,
                    "start_at": start_time,
                }
            }

            if args.end_time:
                params["calendar_event"]["end_at"] = end_time
            if args.description:
                params["calendar_event"]["description"] = args.description
            if args.location:
                params["calendar_event"]["location_name"] = args.location

            # Set context if course is specified
            if hasattr(args, "course") and args.course:
                course_list = courses.process_course_option(canvas, args)
                for course in course_list:
                    params["calendar_event"]["context_code"] = f"course_{course.id}"
                    event = canvas.create_calendar_event(**params)
            else:
                event = canvas.create_calendar_event(**params)
    except canvasapi.exceptions.CanvasException as e:
        canvaslms.cli.err(1, f"Failed to create calendar event: {e}")


def add_command(subp):
    """Adds the calendar command with subcommands to argparse subparser subp"""
    calendar_parser = subp.add_parser(
        "calendar",
        help="Calendar-related commands",
        description="Calendar-related commands for Canvas LMS",
    )

    calendar_subp = calendar_parser.add_subparsers(
        title="calendar subcommands", dest="calendar_command", required=True
    )

    add_calendar_list_command(calendar_subp)
    add_calendar_show_command(calendar_subp)
    add_calendar_create_command(calendar_subp)
