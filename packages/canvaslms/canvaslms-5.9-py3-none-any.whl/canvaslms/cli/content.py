"""Content editing and rendering utilities for Canvas LMS.

This module provides reusable infrastructure for editing Canvas content
(announcements, assignments, pages) with YAML front matter, enabling
bidirectional workflows between Canvas and local files.
"""

import logging
import os
import subprocess
import sys
import tempfile

import pypandoc
import rich.console
import rich.markdown
import yaml

ANNOUNCEMENT_SCHEMA = {
    "id": {
        "default": None,
        "required": False,
        "canvas_attr": "id",
        "description": "Announcement ID (for identification during edit)",
    },
    "title": {
        "default": "",
        "required": True,
        "canvas_attr": "title",
        "description": "Announcement title",
    },
    "message": {
        "default": "",
        "required": True,
        "canvas_attr": "message",
        "description": "Announcement body (HTML)",
    },
    "published": {
        "default": True,
        "required": False,
        "canvas_attr": "published",
        "description": "Whether to publish immediately",
    },
    "delayed_post_at": {
        "default": None,
        "required": False,
        "canvas_attr": "delayed_post_at",
        "description": "Schedule for future posting (ISO datetime)",
    },
    "lock_at": {
        "default": None,
        "required": False,
        "canvas_attr": "lock_at",
        "description": "Date to lock discussion (ISO datetime)",
    },
    "require_initial_post": {
        "default": None,
        "required": False,
        "canvas_attr": "require_initial_post",
        "description": "Require initial post before viewing",
    },
    "allow_rating": {
        "default": None,
        "required": False,
        "canvas_attr": "allow_rating",
        "description": "Allow rating posts",
    },
    "only_graders_can_rate": {
        "default": None,
        "required": False,
        "canvas_attr": "only_graders_can_rate",
        "description": "Restrict rating to graders",
    },
    "sort_by_rating": {
        "default": None,
        "required": False,
        "canvas_attr": "sort_by_rating",
        "description": "Sort posts by rating",
    },
}

ASSIGNMENT_SCHEMA = {
    "name": {
        "default": "",
        "required": True,
        "canvas_attr": "name",
        "description": "Assignment name/title",
    },
    "id": {
        "default": None,
        "required": False,
        "canvas_attr": "id",
        "description": "Assignment ID (for identification during edit)",
    },
    "due_at": {
        "default": None,
        "required": False,
        "canvas_attr": "due_at",
        "description": "Due date (ISO 8601 datetime)",
    },
    "unlock_at": {
        "default": None,
        "required": False,
        "canvas_attr": "unlock_at",
        "description": "Available from date (ISO 8601 datetime)",
    },
    "lock_at": {
        "default": None,
        "required": False,
        "canvas_attr": "lock_at",
        "description": "Available until date (ISO 8601 datetime)",
    },
    "points_possible": {
        "default": None,
        "required": False,
        "canvas_attr": "points_possible",
        "description": "Maximum points for the assignment",
    },
    "published": {
        "default": True,
        "required": False,
        "canvas_attr": "published",
        "description": "Whether the assignment is visible to students",
    },
    "rubric": {
        "default": None,
        "required": False,
        "canvas_attr": "rubric",
        "description": "Rubric criteria and ratings",
    },
}

PAGE_SCHEMA = {
    "title": {
        "default": "",
        "required": True,
        "canvas_attr": "title",
        "description": "Page title",
    },
    "url": {
        "default": None,
        "required": False,
        "canvas_attr": "url",
        "description": "Page URL slug (for identification during edit)",
    },
    "published": {
        "default": True,
        "required": False,
        "canvas_attr": "published",
        "description": "Whether the page is visible to students",
    },
    "front_page": {
        "default": False,
        "required": False,
        "canvas_attr": "front_page",
        "description": "Set as the course front page",
    },
    "editing_roles": {
        "default": "teachers",
        "required": False,
        "canvas_attr": "editing_roles",
        "description": "Who can edit: teachers, students, members, or public",
    },
}


logger = logging.getLogger(__name__)


def parse_yaml_front_matter(content):
    """Parse YAML front matter from content.

    Args:
        content: String containing optional YAML front matter followed by content

    Returns:
        Tuple of (attributes dict, content string without front matter)
    """
    if not content.strip().startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        yaml_str = parts[1]
        attributes = yaml.safe_load(yaml_str) or {}
        message_content = parts[2].lstrip("\n")
        return attributes, message_content
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML front matter: {e}")
        return {}, content


def format_yaml_front_matter(attributes, message_content):
    """Format content with YAML front matter.

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


def create_schema_template(schema):
    """Create an attributes template from a schema definition.

    Args:
        schema: Dict mapping attribute names to their definitions.
                Each definition has 'default', 'required', 'canvas_attr' keys.

    Returns:
        Dict with attribute names mapped to their default values.
    """
    return {name: defn["default"] for name, defn in schema.items()}


def extract_attributes_from_object(obj, schema):
    """Extract attributes from a Canvas object using schema.

    This enables the 'infer from object' capability. Given an announcement,
    assignment, or page object, extract attributes according to the schema.

    Args:
        obj: Canvas API object (Announcement, Assignment, Page, etc.)
        schema: Schema defining which attributes to extract

    Returns:
        Dict with attribute values extracted from the object
    """
    attributes = {}
    for name, defn in schema.items():
        canvas_attr = defn.get("canvas_attr", name)
        value = getattr(obj, canvas_attr, defn["default"])
        attributes[name] = value
    return attributes


def validate_attributes(attributes, schema):
    """Validate attributes against schema.

    Args:
        attributes: Dict of attribute values
        schema: Schema with required/optional definitions

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    for name, defn in schema.items():
        if defn.get("required", False):
            value = attributes.get(name)
            if value is None or value == "":
                errors.append(f"Required attribute '{name}' is missing or empty")
    return errors


def render_to_markdown(obj, schema, content_attr="message", extra_attributes=None):
    """Render a Canvas object to Markdown with YAML front matter.

    This is the Canvas-to-file direction: take a Canvas object and produce
    a Markdown file suitable for Git storage.

    Args:
        obj: Canvas API object
        schema: Schema for attribute extraction
        content_attr: Name of the attribute containing HTML content
                     (e.g., 'message' for announcements, 'description' for assignments)
        extra_attributes: Optional dict of additional attributes to include
                         in the YAML front matter (e.g., {'modules': ['Module 1']})

    Returns:
        Markdown string with YAML front matter
    """
    attributes = extract_attributes_from_object(obj, schema)
    if extra_attributes:
        attributes.update(extra_attributes)

    html_content = getattr(obj, content_attr, "") or ""
    if html_content:
        try:
            markdown_content = pypandoc.convert_text(html_content, "md", format="html")
        except Exception as e:
            logger.warning(f"Failed to convert HTML to Markdown: {e}")
            markdown_content = html_content
    else:
        markdown_content = ""

    return format_yaml_front_matter(attributes, markdown_content)


def render_to_html(obj, schema, content_attr="message", extra_attributes=None):
    """Render a Canvas object to HTML with YAML front matter.

    Unlike render_to_markdown, this outputs the HTML content as-is,
    without converting to Markdown. Use this when HTML elements must
    be preserved exactly (embedded videos, iframes, custom formatting).

    Args:
        obj: Canvas API object
        schema: Schema for attribute extraction
        content_attr: Name of the attribute containing HTML content
        extra_attributes: Optional dict of additional attributes

    Returns:
        String with YAML front matter and HTML body
    """
    attributes = extract_attributes_from_object(obj, schema)
    if extra_attributes:
        attributes.update(extra_attributes)

    html_content = getattr(obj, content_attr, "") or ""
    return format_yaml_front_matter(attributes, html_content)


def read_content_from_file(file_path):
    """Read content from a Markdown file with YAML front matter.

    This is the file-to-Canvas direction: read a Markdown file (possibly
    from a Git repo) and parse its attributes and content.

    Args:
        file_path: Path to the Markdown file

    Returns:
        Tuple of (attributes dict, markdown content)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file has invalid YAML front matter
    """
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    attributes, markdown_content = parse_yaml_front_matter(file_content)
    return attributes, markdown_content


def add_file_option(parser):
    """Add the -f/--file option to a parser.

    Args:
        parser: argparse parser to add the option to
    """
    parser.add_argument(
        "-f",
        "--file",
        help="Read content from a Markdown file with YAML front matter. "
        "When specified, ignores -i/--interactive and -m/--message.",
    )


def get_content_from_editor(
    schema,
    initial_attributes=None,
    content_attr=None,
    extra_attributes=None,
    html_mode=False,
):
    """Open editor to edit content with YAML front matter.

    Args:
        schema: Schema defining available attributes
        initial_attributes: Optional pre-populated attributes (including content)
        content_attr: Name of attribute that represents body content.
                     If provided: extracts from initial_attributes, converts
                     HTML to Markdown (unless html_mode), excludes from YAML.
        extra_attributes: Optional dict of additional attributes to include
                         in YAML front matter (e.g., modules, rubric)
        html_mode: If True, skip HTML-to-Markdown conversion and use .html suffix

    Returns:
        Tuple of (attributes dict, content), or None if cancelled.
        Content is Markdown unless html_mode=True (then raw HTML).
    """
    editor = os.environ.get("EDITOR", "nano")

    if initial_attributes is None:
        initial_attributes = {}

    # Extract content from attributes if content_attr specified
    body_content = ""
    if content_attr and content_attr in initial_attributes:
        html_content = initial_attributes.get(content_attr, "") or ""
        if html_content:
            if html_mode:
                body_content = html_content  # Keep raw HTML
            else:
                try:
                    body_content = pypandoc.convert_text(
                        html_content, "md", format="html"
                    )
                except Exception:
                    body_content = html_content

    # Build template: schema defaults + initial_attributes, minus content_attr
    template_attrs = create_schema_template(schema)
    if content_attr:
        template_attrs.pop(content_attr, None)
    template_attrs.update(initial_attributes)
    if content_attr:
        template_attrs.pop(content_attr, None)  # Also remove from merged attrs
    if extra_attributes:
        template_attrs.update(extra_attributes)

    template_content = format_yaml_front_matter(template_attrs, body_content)

    file_suffix = ".html" if html_mode else ".md"
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=file_suffix, delete=False
    ) as temp_file:
        temp_file.write(template_content)
        temp_file_path = temp_file.name

    try:
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

        with open(temp_file_path, "r") as temp_file:
            file_content = temp_file.read()

        attributes, content = parse_yaml_front_matter(file_content)
        return attributes, content.strip()

    finally:
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass


def render_content_preview(
    title, markdown_content, attributes=None, content_type="Content"
):
    """Render a preview of content in the terminal using Rich.

    Args:
        title: Title to display in preview header
        markdown_content: Markdown content to render
        attributes: Optional dict of attributes to display
        content_type: Type label (e.g., 'Announcement', 'Assignment')
    """
    console = rich.console.Console(stderr=True)

    print("\n" + "=" * 60, file=sys.stderr)
    console.print(f"[bold cyan]Preview {content_type}: {title}[/bold cyan]")
    print("=" * 60 + "\n", file=sys.stderr)

    if attributes:
        console.print("[bold]Attributes:[/bold]")
        for key, value in attributes.items():
            if key != "title":
                console.print(f"  {key}: {value}")
        print(file=sys.stderr)

    try:
        console.print(rich.markdown.Markdown(markdown_content))
    except Exception:
        console.print(markdown_content)

    print("\n" + "=" * 60 + "\n", file=sys.stderr)


def interactive_confirm_and_edit(
    title, message, attributes, schema, content_type="Content", content_attr="message"
):
    """Interactive loop for confirming or editing content.

    Args:
        title: Content title
        message: Markdown content
        attributes: Current attributes
        schema: Schema for re-editing
        content_type: Type label for display
        content_attr: Name of attribute that holds body content (for re-editing)

    Returns:
        Tuple of (attributes, message), or None if cancelled
    """
    current_message = message
    current_attributes = attributes.copy()
    current_title = title

    while True:
        render_content_preview(
            current_title, current_message, current_attributes, content_type
        )

        print("Options:", file=sys.stderr)
        print(f"  [a] Accept and post {content_type.lower()}", file=sys.stderr)
        print("  [e] Edit again", file=sys.stderr)
        print("  [d] Discard and cancel", file=sys.stderr)

        try:
            choice = input("Your choice (a/e/d): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            return None

        if choice in ["a", "accept"]:
            return current_attributes, current_message
        elif choice in ["e", "edit"]:
            edit_attrs = current_attributes.copy()
            edit_attrs[content_attr] = current_message
            result = get_content_from_editor(
                schema, edit_attrs, content_attr=content_attr
            )
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
