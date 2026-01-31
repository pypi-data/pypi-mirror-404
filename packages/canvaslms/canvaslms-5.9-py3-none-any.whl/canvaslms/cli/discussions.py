import os
import re
import subprocess
import sys
import tempfile
import csv
import logging
import pypandoc
import rich.console
import rich.markdown
import arrow
import yaml
import canvaslms.cli.courses
import canvaslms.cli.utils
import canvaslms.cli.calendar
import canvaslms.cli.content

logger = logging.getLogger(__name__)


def add_edit_command(subp):
    """Adds the edit subcommand"""
    edit_parser = subp.add_parser(
        "edit",
        help="Edit existing announcements",
        description="Edit existing announcements in a course. "
        "Supports interactive editing and file-based updates.",
    )
    edit_parser.set_defaults(func=discussions_edit_command)
    edit_parser.add_argument(
        "-c",
        "--course",
        required=True,
        help="Regex matching courses on title, course code or Canvas ID",
    )
    edit_parser.add_argument(
        "-t",
        "--title",
        help="Regex matching announcement title or ID (default: match all)",
    )
    edit_parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Make the title regex case-insensitive",
    )
    canvaslms.cli.content.add_file_option(edit_parser)
    edit_parser.add_argument(
        "--html",
        action="store_true",
        help="Read file as HTML instead of converting from Markdown. "
        "In interactive mode, edit HTML directly.",
    )


def announce_command(config, canvas, args):
    """Posts announcements to matching courses"""

    # Get list of matching courses
    course_list = list(canvaslms.cli.courses.filter_courses(canvas, args.course))

    if not course_list:
        canvaslms.cli.err(1, f"No courses found matching pattern: {args.course}")

    # Get the message content and attributes based on mode
    if args.file:
        try:
            attributes, message = canvaslms.cli.content.read_content_from_file(
                args.file
            )
        except FileNotFoundError:
            canvaslms.cli.err(1, f"File not found: {args.file}")
        except Exception as e:
            canvaslms.cli.err(1, f"Error reading file: {e}")
        title = attributes.get("title", args.title)
        if not title:
            canvaslms.cli.err(
                1,
                "Title is required. Set it in YAML front matter or provide as argument.",
            )
    elif args.message:
        if not args.title:
            canvaslms.cli.err(1, "Title is required when using -m/--message")
        title = args.title
        message = args.message
        attributes = {}
    else:
        initial_attrs = {"title": args.title} if args.title else None
        result = canvaslms.cli.content.get_content_from_editor(
            canvaslms.cli.content.ANNOUNCEMENT_SCHEMA,
            initial_attrs,
            content_attr="message",
        )
        if result is None:
            canvaslms.cli.err(1, "Editor cancelled or failed.")

        attributes, message = result
        title = attributes.get("title", args.title)

        while not title:
            print("Error: Title is required but not provided.", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print("  [e] Return to editor to add title", file=sys.stderr)
            print("  [d] Discard and cancel", file=sys.stderr)

            try:
                choice = input("Your choice (e/d): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(0)

            if choice in ["e", "edit"]:
                # Pass message in attributes for re-editing
                edit_attrs = attributes.copy()
                edit_attrs["message"] = message
                result = canvaslms.cli.content.get_content_from_editor(
                    canvaslms.cli.content.ANNOUNCEMENT_SCHEMA,
                    edit_attrs,
                    content_attr="message",
                )
                if result is None:
                    canvaslms.cli.err(1, "Editor cancelled or failed.")
                attributes, message = result
                title = attributes.get("title")
            elif choice in ["d", "discard", "cancel"]:
                print("Cancelled.", file=sys.stderr)
                sys.exit(0)
            else:
                print(
                    f"Invalid choice '{choice}'. Please enter 'e' or 'd'.",
                    file=sys.stderr,
                )
        print(
            f"Will post announcement '{title}' to {len(course_list)} course(s):",
            file=sys.stderr,
        )
        for course in course_list:
            print(f"  - {course.course_code}: {course.name}", file=sys.stderr)

        result = canvaslms.cli.content.interactive_confirm_and_edit(
            title,
            message,
            attributes,
            canvaslms.cli.content.ANNOUNCEMENT_SCHEMA,
            "Announcement",
            content_attr="message",
        )
        if result is None:
            print("Cancelled.", file=sys.stderr)
            sys.exit(0)
        attributes, message = result
        title = attributes.get("title", title)

    if not message.strip():
        canvaslms.cli.err(1, "Message cannot be empty")

    try:
        html_message = pypandoc.convert_text(message, "html", format="md")
    except Exception as e:
        logger.warning(
            f"Failed to convert markdown to HTML: {e}. Using raw content instead."
        )
        html_message = message

    success_count = 0
    failed_count = 0
    for course in course_list:
        try:
            kwargs = {
                "title": title,
                "message": html_message,
                "is_announcement": True,
            }

            if "published" in attributes:
                kwargs["published"] = attributes["published"]
            else:
                kwargs["published"] = True

            for attr in ["delayed_post_at", "lock_at"]:
                parsed = parse_date_attribute(attributes, attr)
                if parsed:
                    kwargs[attr] = parsed
            for attr in [
                "require_initial_post",
                "allow_rating",
                "only_graders_can_rate",
                "sort_by_rating",
            ]:
                if attr in attributes:
                    kwargs[attr] = attributes[attr]

            discussion_topic = course.create_discussion_topic(**kwargs)
            success_count += 1
        except Exception as e:
            logger.error(
                f"Failed to post to {course.course_code}: {course.name} - {str(e)}"
            )
            failed_count += 1

    if failed_count > 0:
        print(f"Posted to {success_count}/{len(course_list)} courses.", file=sys.stderr)
        sys.exit(1)


def discussions_edit_command(config, canvas, args):
    """Edit existing announcements interactively or from file."""
    if args.file:
        try:
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

        # Validate that at least title is provided (required for announcements)
        if not attributes.get("title"):
            print("Error: Title is required in YAML front matter", file=sys.stderr)
            return
        if args.html:
            html_content = body_content
        else:
            try:
                html_content = pypandoc.convert_text(body_content, "html", format="md")
            except Exception as e:
                logger.warning(
                    f"Failed to convert markdown to HTML: {e}. Using raw content."
                )
                html_content = body_content

        if "id" in attributes and attributes["id"]:
            announcement_id = attributes["id"]
            course_list = list(
                canvaslms.cli.courses.filter_courses(canvas, args.course)
            )
            if not course_list:
                print(
                    f"Error: No courses found matching pattern: {args.course}",
                    file=sys.stderr,
                )
                return

            # Try to find the announcement in any of the matching courses
            announcement = None
            announcement_course = None
            for course in course_list:
                try:
                    announcement = course.get_discussion_topic(announcement_id)
                    announcement_course = course
                    break
                except Exception:
                    continue

            if announcement is None:
                print(
                    f"Error: Announcement with ID '{announcement_id}' not found.",
                    file=sys.stderr,
                )
                return

            update_kwargs = {
                "title": attributes.get("title", announcement.title),
                "message": html_content,
            }

            if "published" in attributes:
                update_kwargs["published"] = attributes["published"]

            # Process date attributes
            for attr in ["delayed_post_at", "lock_at"]:
                parsed = parse_date_attribute(attributes, attr)
                if parsed:
                    update_kwargs[attr] = parsed

            # Process boolean attributes
            for attr in [
                "require_initial_post",
                "allow_rating",
                "only_graders_can_rate",
                "sort_by_rating",
            ]:
                if attr in attributes and attributes[attr] is not None:
                    update_kwargs[attr] = attributes[attr]

            try:
                announcement.update(**update_kwargs)
                print(
                    f"Updated announcement: {attributes.get('title', announcement.title)}",
                    file=sys.stderr,
                )
            except Exception as e:
                logger.error(f"Error updating announcement: {e}")
                print(f"Error updating announcement: {e}", file=sys.stderr)
        else:
            course_list = list(
                canvaslms.cli.courses.filter_courses(canvas, args.course)
            )
            if not course_list:
                print(
                    f"Error: No courses found matching pattern: {args.course}",
                    file=sys.stderr,
                )
                return

            # Find announcements matching the title regex
            title_pattern = attributes.get("title", "")
            matched_announcements = get_matching_announcements(
                course_list, title_pattern, ignore_case=args.ignore_case
            )

            if not matched_announcements:
                print(
                    f"Error: No announcements found matching title: {title_pattern}",
                    file=sys.stderr,
                )
                return

            if len(matched_announcements) > 1:
                print(
                    f"Warning: Multiple announcements match. Using first match.",
                    file=sys.stderr,
                )

            announcement, announcement_course = matched_announcements[0]
            update_kwargs = {
                "title": attributes.get("title", announcement.title),
                "message": html_content,
            }

            if "published" in attributes:
                update_kwargs["published"] = attributes["published"]

            # Process date attributes
            for attr in ["delayed_post_at", "lock_at"]:
                parsed = parse_date_attribute(attributes, attr)
                if parsed:
                    update_kwargs[attr] = parsed

            # Process boolean attributes
            for attr in [
                "require_initial_post",
                "allow_rating",
                "only_graders_can_rate",
                "sort_by_rating",
            ]:
                if attr in attributes and attributes[attr] is not None:
                    update_kwargs[attr] = attributes[attr]

            try:
                announcement.update(**update_kwargs)
                print(
                    f"Updated announcement: {attributes.get('title', announcement.title)}",
                    file=sys.stderr,
                )
            except Exception as e:
                logger.error(f"Error updating announcement: {e}")
                print(f"Error updating announcement: {e}", file=sys.stderr)
    else:
        course_list = list(canvaslms.cli.courses.filter_courses(canvas, args.course))
        if not course_list:
            canvaslms.cli.err(1, f"No courses found matching pattern: {args.course}")

        title_pattern = args.title if args.title else ".*"
        all_announcements = get_matching_announcements(
            course_list, title_pattern, ignore_case=args.ignore_case
        )

        if not all_announcements:
            canvaslms.cli.err(1, f"No announcements found matching the criteria")
        print(
            f"Found {len(all_announcements)} matching announcement(s):", file=sys.stderr
        )
        for idx, (announcement, course) in enumerate(all_announcements, 1):
            date_str = canvaslms.cli.utils.format_local_time(
                getattr(announcement, "created_at", None)
            )
            print(
                f"  [{idx}] {course.course_code}: {announcement.title} ({date_str})",
                file=sys.stderr,
            )

        print(
            "\nEnter numbers to edit (e.g., '1,3,5' or '1-3' or 'all'), or 'q' to quit:",
            file=sys.stderr,
        )

        try:
            selection = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            return

        if selection in ["q", "quit", "exit", ""]:
            print("Cancelled.", file=sys.stderr)
            return

        selected_indices = parse_selection(selection, len(all_announcements))
        if not selected_indices:
            print("No valid selection. Cancelled.", file=sys.stderr)
            return

        selected_announcements = [all_announcements[i] for i in selected_indices]
        updated_count = 0
        skipped_count = 0

        for announcement, course in selected_announcements:
            print(
                f"\nEditing: {course.course_code}: {announcement.title}",
                file=sys.stderr,
            )

            current_attrs = canvaslms.cli.content.extract_attributes_from_object(
                announcement, canvaslms.cli.content.ANNOUNCEMENT_SCHEMA
            )
            result = canvaslms.cli.content.get_content_from_editor(
                canvaslms.cli.content.ANNOUNCEMENT_SCHEMA,
                current_attrs,
                content_attr="message",
                html_mode=args.html,
            )
            if result is None:
                print("Editor cancelled. Skipping this announcement.", file=sys.stderr)
                skipped_count += 1
                continue

            edited_attrs, body_content = result
            title = edited_attrs.get("title", announcement.title)
            result = canvaslms.cli.content.interactive_confirm_and_edit(
                title,
                body_content,
                edited_attrs,
                canvaslms.cli.content.ANNOUNCEMENT_SCHEMA,
                "Announcement",
                content_attr="message",
            )

            if result is None:
                print("Discarded changes.", file=sys.stderr)
                skipped_count += 1
                continue

            final_attrs, final_content = result

            # Convert to HTML and update
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

            # Prepare update kwargs using final_attrs
            attributes = final_attrs
            announcement_course = course
            update_kwargs = {
                "title": attributes.get("title", announcement.title),
                "message": html_content,
            }

            if "published" in attributes:
                update_kwargs["published"] = attributes["published"]

            # Process date attributes
            for attr in ["delayed_post_at", "lock_at"]:
                parsed = parse_date_attribute(attributes, attr)
                if parsed:
                    update_kwargs[attr] = parsed

            # Process boolean attributes
            for attr in [
                "require_initial_post",
                "allow_rating",
                "only_graders_can_rate",
                "sort_by_rating",
            ]:
                if attr in attributes and attributes[attr] is not None:
                    update_kwargs[attr] = attributes[attr]

            try:
                announcement.update(**update_kwargs)
                print(
                    f"Updated announcement: {attributes.get('title', announcement.title)}",
                    file=sys.stderr,
                )
            except Exception as e:
                logger.error(f"Error updating announcement: {e}")
                print(f"Error updating announcement: {e}", file=sys.stderr)
            updated_count += 1
        print(
            f"\nEditing complete: {updated_count} updated, {skipped_count} skipped.",
            file=sys.stderr,
        )


def get_matching_announcements(course_list, title_regex, ignore_case=False):
    """
    Returns a list of (announcement, course) tuples matching the pattern.

    The pattern is matched against both the title and the Canvas ID.
    Results are sorted by creation date (newest first).
    """
    if not title_regex:
        title_regex = ".*"  # Match all if no pattern specified

    flags = re.IGNORECASE if ignore_case else 0
    try:
        pattern = re.compile(title_regex, flags)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        return []

    matched = []
    for course in course_list:
        try:
            announcements = course.get_discussion_topics(only_announcements=True)
            for announcement in announcements:
                # Match against title or ID
                title = getattr(announcement, "title", "") or ""
                ann_id = str(getattr(announcement, "id", ""))
                if pattern.search(title) or pattern.search(ann_id):
                    matched.append((announcement, course))
        except Exception as e:
            logger.warning(
                f"Error fetching announcements from {course.course_code}: {e}"
            )

    # Sort by creation date (newest first)
    matched.sort(key=lambda x: getattr(x[0], "created_at", ""), reverse=True)
    return matched


def parse_selection(selection, max_count):
    """
    Parse a selection string like '1,3,5' or '1-3' or 'all'.
    Returns a list of zero-based indices.
    """
    if selection == "all":
        return list(range(max_count))

    indices = set()
    parts = selection.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            # Range like '1-3'
            try:
                start, end = part.split("-", 1)
                start = int(start) - 1  # Convert to zero-based
                end = int(end) - 1
                if 0 <= start <= end < max_count:
                    indices.update(range(start, end + 1))
            except ValueError:
                continue
        else:
            # Single number
            try:
                idx = int(part) - 1  # Convert to zero-based
                if 0 <= idx < max_count:
                    indices.add(idx)
            except ValueError:
                continue

    return sorted(indices)


def list_command(config, canvas, args):
    """Lists discussions or announcements from matching courses"""

    # Get list of matching courses
    course_list = list(canvaslms.cli.courses.filter_courses(canvas, args.course))

    if not course_list:
        canvaslms.cli.err(1, f"No courses found matching pattern: {args.course}")

    # List discussions/announcements for each course
    for course in course_list:
        try:
            if args.type == "announcements":
                output = csv.writer(sys.stdout, delimiter=args.delimiter)
                announcements = course.get_discussion_topics(only_announcements=True)
                for announcement in announcements:
                    date_to_show = getattr(
                        announcement, "delayed_post_at", None
                    ) or getattr(announcement, "created_at", None)
                    output.writerow(
                        [
                            course.course_code,
                            announcement.title,
                            canvaslms.cli.utils.format_local_time(date_to_show),
                        ]
                    )
            else:  # discussions
                output = csv.writer(sys.stdout, delimiter=args.delimiter)
                discussions = course.get_discussion_topics()
                for discussion in discussions:
                    if not getattr(discussion, "is_announcement", False):
                        output.writerow(
                            [
                                course.course_code,
                                discussion.title,
                                canvaslms.cli.utils.format_local_time(
                                    discussion.created_at
                                ),
                            ]
                        )
        except Exception as e:
            canvaslms.cli.err(1, f"Error accessing {course.course_code}: {str(e)}")


def discussions_view_command(config, canvas, args):
    """Shows detailed view of discussions or announcements from matching courses"""

    # Get list of matching courses
    course_list = list(canvaslms.cli.courses.filter_courses(canvas, args.course))

    if not course_list:
        canvaslms.cli.err(1, f"No courses found matching pattern: {args.course}")

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

    message_pattern = None
    if args.message:
        try:
            flags = re.IGNORECASE if args.ignore_case else 0
            message_pattern = re.compile(args.message, flags)
        except re.error as e:
            canvaslms.cli.err(1, f"Invalid regex for --message: {e}")

    # Collect all discussions/announcements from matching courses
    all_items = []
    for course in course_list:
        try:
            if args.type == "announcements":
                items = course.get_discussion_topics(only_announcements=True)
            else:  # discussions
                items = course.get_discussion_topics()
                # Filter out announcements when listing discussions
                items = [
                    item
                    for item in items
                    if not getattr(item, "is_announcement", False)
                ]

            # Add course info to each item for display
            for item in items:
                item._course = course
                all_items.append(item)

        except Exception as e:
            canvaslms.cli.err(1, f"Error accessing {course.course_code}: {str(e)}")

    # Filter by regex if provided
    filtered_items = []
    for item in all_items:
        if matches_regex_patterns(item, args):
            filtered_items.append(item)

    # Sort by creation date (newest first)
    filtered_items.sort(key=lambda x: getattr(x, "created_at", ""), reverse=True)

    # Take the requested count
    if args.count == 0:
        count = len(filtered_items)  # Show all matches
    else:
        count = max(1, args.count)

    selected_items = filtered_items[:count]

    if not selected_items:
        canvaslms.cli.err(1, f"No matching {args.type} found")

    # Display items using Rich
    console = rich.console.Console()
    for idx, item in enumerate(selected_items):
        # Print header with course and type info
        item_type = (
            "Announcement" if getattr(item, "is_announcement", False) else "Discussion"
        )
        course = getattr(item, "_course", None)
        course_info = f" [{course.course_code}]" if course else ""

        console.print(f"[bold cyan]{item_type}{course_info}[/bold cyan]")
        console.print(f"[bold]Title:  [/bold] {getattr(item, 'title', 'N/A')}")
        console.print(
            f"[bold]Created:[/bold] {canvaslms.cli.utils.format_local_time(getattr(item, 'created_at', None))}"
        )
        console.print(
            f"[bold]Author: [/bold] {getattr(item, 'author', {}).get('display_name', 'N/A')}"
        )

        # Show URL if available
        url = getattr(item, "html_url", None)
        if url:
            console.print(f"[bold]URL:    [/bold] {url}")

        # Show message content if available
        message = getattr(item, "message", None)
        if message and message.strip():
            console.print(f"[bold]Message:[/bold]")
            # Convert HTML message back to markdown for nice display
            try:
                markdown_content = pypandoc.convert_text(message, "md", format="html")
                console.print(rich.markdown.Markdown(markdown_content))
            except Exception:
                # Fallback: just print the HTML content
                console.print(message)
        else:
            console.print(f"[bold]Message:[/bold] [dim]No content[/dim]")
        if idx != len(selected_items) - 1:
            print()  # Add blank line between items


def parse_yaml_front_matter(content):
    """Parse YAML front matter from content

    Args:
      content: String containing optional YAML front matter followed by content

    Returns:
      Tuple of (attributes dict, content string)
    """
    # Check if content starts with YAML front matter delimiter
    if not content.strip().startswith("---"):
        return {}, content

    # Try to extract YAML front matter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        # parts[0] is empty, parts[1] is YAML, parts[2] is content
        yaml_str = parts[1]
        attributes = yaml.safe_load(yaml_str) or {}
        message_content = parts[2].lstrip("\n")
        return attributes, message_content
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML front matter: {e}")
        return {}, content


def format_yaml_front_matter(attributes, message_content):
    """Format content with YAML front matter

    Args:
      attributes: Dictionary of attributes
      message_content: The message content

    Returns:
      String with YAML front matter and content
    """
    if not attributes:
        return message_content

    yaml_str = yaml.dump(attributes, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n{message_content}"


def get_announcement_from_editor(
    initial_title=None, initial_attributes=None, initial_content=""
):
    """Opens the user's preferred editor to write the announcement with YAML front matter

    Args:
      initial_title: Optional title to pre-populate (overridden by attributes)
      initial_attributes: Optional dictionary of attributes to pre-populate
      initial_content: Optional initial markdown content to pre-populate the editor

    Returns:
      Tuple of (attributes dict, markdown content), or None if cancelled
    """
    editor = os.environ.get("EDITOR", "nano")

    # Prepare initial content with YAML front matter template
    if initial_attributes is None:
        initial_attributes = {}

    # Set default attributes if not provided
    if "title" not in initial_attributes and initial_title:
        initial_attributes["title"] = initial_title

    # Add all possible template fields if not present
    # This shows users all available attributes they can set
    if not initial_attributes.get("title"):
        initial_attributes["title"] = ""
    if "published" not in initial_attributes:
        initial_attributes["published"] = True
    if "delayed_post_at" not in initial_attributes:
        initial_attributes["delayed_post_at"] = None
    if "lock_at" not in initial_attributes:
        initial_attributes["lock_at"] = None
    if "require_initial_post" not in initial_attributes:
        initial_attributes["require_initial_post"] = None
    if "allow_rating" not in initial_attributes:
        initial_attributes["allow_rating"] = None
    if "only_graders_can_rate" not in initial_attributes:
        initial_attributes["only_graders_can_rate"] = None
    if "sort_by_rating" not in initial_attributes:
        initial_attributes["sort_by_rating"] = None

    # Format the initial content
    template_content = format_yaml_front_matter(initial_attributes, initial_content)

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".md", delete=False
    ) as temp_file:
        temp_file.write(template_content)
        temp_file_path = temp_file.name

    try:
        # Open editor
        try:
            subprocess.run([editor, temp_file_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Editor exited with error code {e.returncode}")
            return None
        except FileNotFoundError:
            logger.error(f"Editor '{editor}' not found")
            return None
        except Exception as e:
            logger.error(f"Error opening editor: {e}")
            return None

        # Read the content back
        with open(temp_file_path, "r") as temp_file:
            content = temp_file.read()

        # Parse YAML front matter
        attributes, markdown_content = parse_yaml_front_matter(content)

        return attributes, markdown_content.strip()

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass


def get_message_from_editor(initial_content=""):
    """Opens the user's preferred editor to write the announcement message

    This is the legacy function for backward compatibility.

    Args:
      initial_content: Optional initial markdown content to pre-populate the editor

    Returns:
      The markdown content, or None if cancelled
    """
    result = get_announcement_from_editor(None, {}, initial_content)
    if result is None:
        return None
    attributes, content = result
    return content


def render_message_preview(title, markdown_content, attributes=None):
    """Renders a preview of the announcement message using Rich

    Args:
      title: The announcement title
      markdown_content: The markdown content to preview
      attributes: Optional dictionary of announcement attributes
    """
    console = rich.console.Console(stderr=True)

    print("\n" + "=" * 60, file=sys.stderr)
    console.print(f"[bold cyan]Preview: {title}[/bold cyan]")
    print("=" * 60 + "\n", file=sys.stderr)

    # Show attributes if present
    if attributes:
        console.print("[bold]Attributes:[/bold]")
        for key, value in attributes.items():
            if key != "title":  # Title is already shown in header
                console.print(f"  {key}: {value}")
        print(file=sys.stderr)

    # Render markdown directly
    try:
        console.print(rich.markdown.Markdown(markdown_content))
    except Exception:
        # Fallback: just print the content
        console.print(markdown_content)

    print("\n" + "=" * 60 + "\n", file=sys.stderr)


def interactive_confirm_and_edit(title, message, attributes):
    """Interactive loop for confirming or editing the announcement

    Args:
      title: The announcement title
      message: The markdown message content
      attributes: Dictionary of announcement attributes

    Returns:
      Tuple of (attributes dict, message content), or None if cancelled
    """
    current_message = message
    current_attributes = attributes.copy()
    current_title = title

    while True:
        # Show preview
        render_message_preview(current_title, current_message, current_attributes)

        # Prompt for action
        print("Options:", file=sys.stderr)
        print("  [a] Accept and post announcement", file=sys.stderr)
        print("  [e] Edit message again", file=sys.stderr)
        print("  [d] Discard and cancel", file=sys.stderr)

        try:
            choice = input("Your choice (a/e/d): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            return None

        if choice in ["a", "accept"]:
            return current_attributes, current_message
        elif choice in ["e", "edit"]:
            # Re-open editor with current content
            result = get_announcement_from_editor(
                current_title, current_attributes, current_message
            )
            # Handle cancellation or error
            if result is None:
                print(
                    "Editor cancelled or failed. Keeping previous content.",
                    file=sys.stderr,
                )
            else:
                new_attributes, new_message = result
                if new_message.strip():
                    current_message = new_message
                    current_attributes = new_attributes
                    current_title = new_attributes.get("title", current_title)
                else:
                    print(
                        "Message cannot be empty. Keeping previous content.",
                        file=sys.stderr,
                    )
        elif choice in ["d", "discard", "cancel"]:
            return None
        else:
            print(
                f"Invalid choice '{choice}'. Please enter 'a', 'e', or 'd'.",
                file=sys.stderr,
            )


def parse_date_attribute(attributes, attr_name):
    """Parse a date attribute using utils module's format_canvas_time

    Args:
      attributes: Dictionary of announcement attributes
      attr_name: Name of the date attribute to parse

    Returns:
      Canvas-formatted date string, or None if not present or invalid
    """
    if attr_name not in attributes:
        return None

    date_value = attributes[attr_name]
    if date_value and date_value != "null":
        try:
            return canvaslms.cli.utils.format_canvas_time(date_value)
        except Exception as e:
            logger.warning(f"Failed to parse {attr_name} '{date_value}': {e}")
            return None
    return None


def matches_regex_patterns(item, args):
    """Check if discussion/announcement matches the regex patterns"""
    if not (args.match or args.title or args.message):
        return True

    title = getattr(item, "title", "") or ""
    message = getattr(item, "message", "") or ""
    text = f"{title}\n{message}"

    # Compile patterns dynamically (could be optimized by moving to discussions_view_command)
    flags = re.IGNORECASE if args.ignore_case else 0

    if args.title:
        try:
            title_pattern = re.compile(args.title, flags)
            if title_pattern.search(title):
                return True
        except re.error:
            pass

    if args.message:
        try:
            message_pattern = re.compile(args.message, flags)
            if message_pattern.search(message):
                return True
        except re.error:
            pass

    if args.match:
        try:
            pattern = re.compile(args.match, flags)
            if pattern.search(text):
                return True
        except re.error:
            pass

    return False


def add_command(subp):
    """Adds the discussions command with subcommands to argparse parser"""
    discussions_parser = subp.add_parser(
        "discussions",
        help="Manage course discussions and announcements",
        description="Manage discussions and announcements in Canvas courses.",
    )

    discussions_subp = discussions_parser.add_subparsers(
        title="discussions commands", dest="discussions_command", required=True
    )

    add_announce_command(discussions_subp)
    add_edit_command(discussions_subp)
    add_list_command(discussions_subp)
    add_view_command(discussions_subp)


def add_announce_command(subp):
    """Adds the announce subcommand"""
    announce_parser = subp.add_parser(
        "announce",
        help="Post announcements to courses",
        description="Post announcements to one or more courses matching a regex pattern. "
        "The announcement can be provided via command line or interactively using an editor.",
    )
    announce_parser.set_defaults(func=announce_command)
    announce_parser.add_argument(
        "title",
        nargs="?",
        default=None,
        help="Title of the announcement (can be set in YAML front matter in interactive mode)",
    )
    announce_parser.add_argument(
        "-c",
        "--course",
        required=True,
        help="Regex matching courses on title, course code or Canvas ID",
    )
    announce_parser.add_argument(
        "-m",
        "--message",
        help="Message content (posts directly without preview; requires title argument)",
    )
    canvaslms.cli.content.add_file_option(announce_parser)


def add_list_command(subp):
    """Adds the list subcommand"""
    list_parser = subp.add_parser(
        "list",
        help="List discussions and announcements",
        description="List discussions or announcements from courses.",
    )
    list_parser.set_defaults(func=list_command)
    list_parser.add_argument(
        "type", choices=["announcements", "discussions"], help="Type of content to list"
    )
    list_parser.add_argument(
        "-c",
        "--course",
        required=True,
        help="Regex matching courses on title, course code or Canvas ID",
    )


def add_view_command(subp):
    """Adds the view subcommand"""
    view_parser = subp.add_parser(
        "view",
        help="Show details of discussions and announcements",
        description="Show detailed view of discussions or announcements from courses with rich formatting.",
    )
    view_parser.set_defaults(func=discussions_view_command)
    view_parser.add_argument(
        "type", choices=["announcements", "discussions"], help="Type of content to show"
    )
    view_parser.add_argument(
        "-c",
        "--course",
        required=True,
        help="Regex matching courses on title, course code or Canvas ID",
    )
    view_parser.add_argument(
        "--match",
        help="Regular expression to match against discussion/announcement title and message",
    )
    view_parser.add_argument(
        "--title",
        "-t",
        help="Regular expression to match against discussion/announcement title",
    )
    view_parser.add_argument(
        "--message",
        "-m",
        help="Regular expression to match against discussion/announcement message",
    )
    view_parser.add_argument(
        "--ignore-case",
        "-i",
        action="store_true",
        help="Make the regex case-insensitive",
    )
    view_parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1,
        help="Number of matching items to show (default: 1), set to 0 to show all matches",
    )
