import logging
import re
import sys

import pypandoc
import rich.console
import rich.markdown
import rich.syntax

from datetime import datetime

import canvaslms.cli
import canvaslms.cli.content
import canvaslms.cli.courses
import canvaslms.cli.modules

logger = logging.getLogger(__name__)


def add_page_options(parser, required=False):
    """Add course and page selection options to a parser."""
    canvaslms.cli.courses.add_course_option(parser, required=required)
    parser.add_argument(
        "-p",
        "--page",
        default=".*",
        help="Regex matching page title or URL slug, default: '.*'",
    )
    parser.add_argument(
        "-M",
        "--module",
        default="",
        help="Regex matching module title or Canvas identifier. "
        "Can be combined with -p for AND filtering.",
    )


def process_page_option(canvas, args):
    """Process page options and return matching pages."""
    course_list = canvaslms.cli.courses.process_course_option(canvas, args)
    pages = []
    for course in course_list:
        filtered_pages = filter_pages(course, args.page)

        if args.module:
            course_modules = canvaslms.cli.modules.filter_modules(course, args.module)
            filtered_pages = list(
                canvaslms.cli.modules.filter_pages_by_module_list(
                    course_modules, filtered_pages
                )
            )

        pages.extend(filtered_pages)
    if not pages:
        raise canvaslms.cli.EmptyListError("No pages found matching the criteria")
    return pages


def filter_pages(course, regex):
    """Return pages from course whose title or URL matches regex."""
    pattern = re.compile(regex)
    result = []
    for page in course.get_pages():
        if pattern.search(page.title) or pattern.search(page.url):
            page.course = course
            result.append(page)
    return result


def pages_list_command(config, canvas, args):
    """List wiki pages from courses."""
    import csv

    output = csv.writer(sys.stdout, delimiter=args.delimiter)
    pages = process_page_option(canvas, args)

    for page in pages:
        output.writerow(
            [
                page.course.course_code,
                page.title,
                "published" if page.published else "unpublished",
                page.html_url,
            ]
        )


def pages_view_command(config, canvas, args):
    """View wiki page content."""
    console = rich.console.Console()
    pages = process_page_option(canvas, args)

    for page in pages:
        full_page = page.course.get_page(page.url)
        full_page.course = page.course

        if sys.stdout.isatty():
            if args.html:
                header = f"# {full_page.title}\n\n"
                header += f"## Metadata\n\n"
                header += f"- Course: {full_page.course.course_code}\n"
                header += f"- Published: {'Yes' if full_page.published else 'No'}\n"
                header += f"- URL: {full_page.html_url}\n"
                if hasattr(full_page, "front_page") and full_page.front_page:
                    header += f"- Front page: Yes\n"
                if hasattr(full_page, "editing_roles"):
                    header += f"- Editing roles: {full_page.editing_roles}\n"
                header += "\n## Content (HTML)\n\n"

                with console.pager(styles=True):
                    console.print(rich.markdown.Markdown(header))
                    if hasattr(full_page, "body") and full_page.body:
                        syntax = rich.syntax.Syntax(
                            full_page.body, "html", theme="monokai", word_wrap=True
                        )
                        console.print(syntax)
                    else:
                        console.print("(No content)")
            else:
                output = format_page(full_page)
                with console.pager(styles=False, links=True):
                    console.print(rich.markdown.Markdown(output, code_theme="manni"))
        else:
            if args.html:
                page_modules = canvaslms.cli.modules.get_item_modules(
                    full_page.course, "Page", full_page.url
                )
                output = canvaslms.cli.content.render_to_html(
                    full_page,
                    canvaslms.cli.content.PAGE_SCHEMA,
                    content_attr="body",
                    extra_attributes={"modules": page_modules},
                )
                print(output)
            else:
                page_modules = canvaslms.cli.modules.get_item_modules(
                    full_page.course, "Page", full_page.url
                )
                output = canvaslms.cli.content.render_to_markdown(
                    full_page,
                    canvaslms.cli.content.PAGE_SCHEMA,
                    content_attr="body",
                    extra_attributes={"modules": page_modules},
                )
                print(output)


def format_page(page):
    """Format a wiki page for terminal display."""
    text = f"# {page.title}\n\n"
    text += f"## Metadata\n\n"
    text += f"- Course: {page.course.course_code}\n"
    text += f"- Published: {'Yes' if page.published else 'No'}\n"
    text += f"- URL: {page.html_url}\n"

    if hasattr(page, "front_page") and page.front_page:
        text += f"- Front page: Yes\n"

    if hasattr(page, "editing_roles"):
        text += f"- Editing roles: {page.editing_roles}\n"

    text += "\n## Content\n\n"

    if hasattr(page, "body") and page.body:
        try:
            markdown_content = pypandoc.convert_text(page.body, "md", format="html")
            text += markdown_content
        except Exception:
            text += page.body
    else:
        text += "(No content)"

    return text


def pages_edit_command(config, canvas, args):
    """Edit wiki page content interactively or from file."""
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
            attributes, canvaslms.cli.content.PAGE_SCHEMA
        )
        if errors:
            for error in errors:
                print(f"Validation error: {error}", file=sys.stderr)
            return
        if args.html:
            html_content = body_content  # Already HTML, no conversion needed
        else:
            html_content = pypandoc.convert_text(body_content, "html", format="md")

        if "url" in attributes and attributes["url"]:
            page_url = attributes["url"]
            course_list = canvaslms.cli.courses.process_course_option(canvas, args)
            if not course_list:
                print("Error: No courses found matching criteria", file=sys.stderr)
                return

            course = course_list[0]
            try:
                full_page = course.get_page(page_url)
                full_page.course = course
                update_data = {
                    "wiki_page": {
                        "title": attributes.get("title", full_page.title),
                        "body": html_content,
                    }
                }

                if "published" in attributes:
                    update_data["wiki_page"]["published"] = attributes["published"]
                if "front_page" in attributes:
                    update_data["wiki_page"]["front_page"] = attributes["front_page"]
                if "editing_roles" in attributes and attributes["editing_roles"]:
                    update_data["wiki_page"]["editing_roles"] = attributes[
                        "editing_roles"
                    ]

                try:
                    full_page.edit(**update_data)
                    full_page._fetched_at = datetime.now()
                    if hasattr(full_page.course, "page_cache"):
                        full_page.course.page_cache[full_page.url] = (full_page, {})
                    logger.info(f"Updated page: {full_page.title}")
                    if "modules" in attributes:
                        module_regexes = attributes["modules"]
                        added, removed = canvaslms.cli.modules.update_item_modules(
                            full_page.course, "Page", full_page.url, module_regexes
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
                    logger.error(f"Error updating page '{full_page.title}': {e}")
                    print(
                        f"Error updating page '{full_page.title}': {e}", file=sys.stderr
                    )
            except Exception as e:
                if args.create:
                    create_params = {
                        "title": attributes.get("title", "Untitled Page"),
                        "body": html_content,
                    }
                    if "published" in attributes:
                        create_params["published"] = attributes["published"]
                    if "front_page" in attributes:
                        create_params["front_page"] = attributes["front_page"]
                    if "editing_roles" in attributes and attributes["editing_roles"]:
                        create_params["editing_roles"] = attributes["editing_roles"]

                    try:
                        new_page = course.create_page(wiki_page=create_params)
                        new_page.course = course
                        print(
                            f"Created page: {new_page.title} (url: {new_page.url})",
                            file=sys.stderr,
                        )
                        if "modules" in attributes:
                            module_regexes = attributes["modules"]
                            added, removed = canvaslms.cli.modules.update_item_modules(
                                new_page.course, "Page", new_page.url, module_regexes
                            )
                            if added:
                                print(
                                    f"  Added to modules: {', '.join(added)}",
                                    file=sys.stderr,
                                )
                    except Exception as e:
                        logger.error(f"Error creating page: {e}")
                        print(f"Error creating page: {e}", file=sys.stderr)
                else:
                    print(
                        f"Error: Page '{page_url}' not found. "
                        f"Use --create to create a new page.",
                        file=sys.stderr,
                    )
                    return
        else:
            if "title" in attributes and attributes["title"]:
                title = attributes["title"]
                course_list = canvaslms.cli.courses.process_course_option(canvas, args)
                if not course_list:
                    print("Error: No courses found matching criteria", file=sys.stderr)
                    return

                course = course_list[0]

                matching_pages = [p for p in course.get_pages() if p.title == title]

                if len(matching_pages) == 1:
                    full_page = course.get_page(matching_pages[0].url)
                    full_page.course = course
                    update_data = {
                        "wiki_page": {
                            "title": attributes.get("title", full_page.title),
                            "body": html_content,
                        }
                    }

                    if "published" in attributes:
                        update_data["wiki_page"]["published"] = attributes["published"]
                    if "front_page" in attributes:
                        update_data["wiki_page"]["front_page"] = attributes[
                            "front_page"
                        ]
                    if "editing_roles" in attributes and attributes["editing_roles"]:
                        update_data["wiki_page"]["editing_roles"] = attributes[
                            "editing_roles"
                        ]

                    try:
                        full_page.edit(**update_data)
                        full_page._fetched_at = datetime.now()
                        if hasattr(full_page.course, "page_cache"):
                            full_page.course.page_cache[full_page.url] = (full_page, {})
                        logger.info(f"Updated page: {full_page.title}")
                        if "modules" in attributes:
                            module_regexes = attributes["modules"]
                            added, removed = canvaslms.cli.modules.update_item_modules(
                                full_page.course, "Page", full_page.url, module_regexes
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
                        logger.error(f"Error updating page '{full_page.title}': {e}")
                        print(
                            f"Error updating page '{full_page.title}': {e}",
                            file=sys.stderr,
                        )
                elif len(matching_pages) == 0:
                    if args.create:
                        create_params = {
                            "title": attributes.get("title", "Untitled Page"),
                            "body": html_content,
                        }
                        if "published" in attributes:
                            create_params["published"] = attributes["published"]
                        if "front_page" in attributes:
                            create_params["front_page"] = attributes["front_page"]
                        if (
                            "editing_roles" in attributes
                            and attributes["editing_roles"]
                        ):
                            create_params["editing_roles"] = attributes["editing_roles"]

                        try:
                            new_page = course.create_page(wiki_page=create_params)
                            new_page.course = course
                            print(
                                f"Created page: {new_page.title} (url: {new_page.url})",
                                file=sys.stderr,
                            )
                            if "modules" in attributes:
                                module_regexes = attributes["modules"]
                                added, removed = (
                                    canvaslms.cli.modules.update_item_modules(
                                        new_page.course,
                                        "Page",
                                        new_page.url,
                                        module_regexes,
                                    )
                                )
                                if added:
                                    print(
                                        f"  Added to modules: {', '.join(added)}",
                                        file=sys.stderr,
                                    )
                        except Exception as e:
                            logger.error(f"Error creating page: {e}")
                            print(f"Error creating page: {e}", file=sys.stderr)
                    else:
                        print(
                            f"Error: Page '{title}' not found. "
                            f"Use --create to create a new page.",
                            file=sys.stderr,
                        )
                        return
                else:
                    print(
                        f"Error: Multiple pages with title '{title}' found. "
                        f"Add 'url' field to YAML to identify specific page.",
                        file=sys.stderr,
                    )
                    return
            else:
                pages = process_page_option(canvas, args)
                if len(pages) > 1:
                    print(
                        f"Error: {len(pages)} pages match filter. "
                        f"Add 'title' or 'url' to YAML, or use -p to narrow selection.",
                        file=sys.stderr,
                    )
                    return
                for page in pages:
                    full_page = page.course.get_page(page.url)
                    full_page.course = page.course
                    update_data = {
                        "wiki_page": {
                            "title": attributes.get("title", full_page.title),
                            "body": html_content,
                        }
                    }

                    if "published" in attributes:
                        update_data["wiki_page"]["published"] = attributes["published"]
                    if "front_page" in attributes:
                        update_data["wiki_page"]["front_page"] = attributes[
                            "front_page"
                        ]
                    if "editing_roles" in attributes and attributes["editing_roles"]:
                        update_data["wiki_page"]["editing_roles"] = attributes[
                            "editing_roles"
                        ]

                    try:
                        full_page.edit(**update_data)
                        full_page._fetched_at = datetime.now()
                        if hasattr(full_page.course, "page_cache"):
                            full_page.course.page_cache[full_page.url] = (full_page, {})
                        logger.info(f"Updated page: {full_page.title}")
                        if "modules" in attributes:
                            module_regexes = attributes["modules"]
                            added, removed = canvaslms.cli.modules.update_item_modules(
                                full_page.course, "Page", full_page.url, module_regexes
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
                        logger.error(f"Error updating page '{full_page.title}': {e}")
                        print(
                            f"Error updating page '{full_page.title}': {e}",
                            file=sys.stderr,
                        )
    else:
        try:
            page_list = process_page_option(canvas, args)
        except canvaslms.cli.EmptyListError as e:
            print(f"Error: {e}", file=sys.stderr)
            return
        print(f"Will edit {len(page_list)} page(s):", file=sys.stderr)
        for page in page_list:
            course_code = page.course.course_code if hasattr(page, "course") else "?"
            print(f"  - {course_code}: {page.title}", file=sys.stderr)

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

        for page in page_list:
            # Fetch full page content (list only has basic info)
            full_page = page.course.get_page(page.url)
            full_page.course = page.course

            course_code = page.course.course_code if hasattr(page, "course") else "?"
            print(f"\nEditing: {course_code}: {full_page.title}", file=sys.stderr)

            current_attrs = canvaslms.cli.content.extract_attributes_from_object(
                full_page, canvaslms.cli.content.PAGE_SCHEMA
            )
            page_modules = canvaslms.cli.modules.get_item_modules(
                full_page.course, "Page", full_page.url
            )
            result = canvaslms.cli.content.get_content_from_editor(
                canvaslms.cli.content.PAGE_SCHEMA,
                current_attrs,
                content_attr="body",
                extra_attributes={"modules": page_modules},
                html_mode=args.html,
            )
            if result is None:
                print("Editor cancelled. Skipping this page.", file=sys.stderr)
                skipped_count += 1
                continue

            # body_content is Markdown or HTML depending on args.html
            attributes, body_content = result
            title = attributes.get("title", full_page.title)
            result = canvaslms.cli.content.interactive_confirm_and_edit(
                title,
                body_content,
                attributes,
                canvaslms.cli.content.PAGE_SCHEMA,
                "Page",
                content_attr="body",
            )

            if result is None:
                print("Discarded changes for this page.", file=sys.stderr)
                skipped_count += 1
                continue

            final_attrs, final_content = result
            if args.html:
                html_content = final_content  # Already HTML, no conversion needed
            else:
                try:
                    html_content = pypandoc.convert_text(
                        final_content, "html", format="md"
                    )
                except Exception as e:
                    logger.warning(f"Failed to convert markdown to HTML: {e}")
                    html_content = final_content

            update_data = {
                "wiki_page": {
                    "title": final_attrs.get("title", full_page.title),
                    "body": html_content,
                }
            }

            # Add optional attributes
            if "published" in final_attrs:
                update_data["wiki_page"]["published"] = final_attrs["published"]
            if "front_page" in final_attrs:
                update_data["wiki_page"]["front_page"] = final_attrs["front_page"]
            if "editing_roles" in final_attrs and final_attrs["editing_roles"]:
                update_data["wiki_page"]["editing_roles"] = final_attrs["editing_roles"]

            try:
                full_page.edit(**update_data)
                full_page._fetched_at = datetime.now()
                if hasattr(full_page.course, "page_cache"):
                    full_page.course.page_cache[full_page.url] = (full_page, {})
                logger.info(f"Updated page: {full_page.title}")
                if "modules" in final_attrs:
                    module_regexes = final_attrs["modules"]
                    added, removed = canvaslms.cli.modules.update_item_modules(
                        full_page.course, "Page", full_page.url, module_regexes
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
                logger.error(f"Error updating page '{full_page.title}': {e}")
                print(f"Error updating page '{full_page.title}': {e}", file=sys.stderr)
                skipped_count += 1
        print(
            f"\nDone. Updated {updated_count}/{len(page_list)} page(s).",
            file=sys.stderr,
        )
        if skipped_count > 0:
            print(f"Skipped {skipped_count} page(s).", file=sys.stderr)


def add_command(subp):
    """Adds the pages command with subcommands to argparse parser"""
    pages_parser = subp.add_parser(
        "pages",
        help="Manage course wiki pages",
        description="Manage wiki pages in Canvas courses: list, view, and edit.",
    )

    pages_subp = pages_parser.add_subparsers(
        title="pages commands", dest="pages_command", required=True
    )

    list_parser = pages_subp.add_parser(
        "list",
        help="List wiki pages in a course",
        description="Lists wiki pages from courses. "
        "Output: <course> <title> <published> <url>",
    )
    list_parser.set_defaults(func=pages_list_command)
    add_page_options(list_parser)
    view_parser = pages_subp.add_parser(
        "view",
        help="View page content",
        description="View wiki page content. When piped, outputs editable format "
        "with YAML front matter. Use --html to preserve HTML instead of "
        "converting to Markdown.",
    )
    view_parser.set_defaults(func=pages_view_command)
    add_page_options(view_parser)
    view_parser.add_argument(
        "--html",
        action="store_true",
        help="Output raw HTML instead of converting to Markdown",
    )
    edit_parser = pages_subp.add_parser(
        "edit",
        help="Edit page content interactively or from a file",
        description="Edit wiki page content. Without -f, opens each matching "
        "page in your editor for interactive editing with preview. "
        "With -f, reads from a Markdown file with YAML front matter and updates "
        "directly (script-friendly). If the YAML contains a 'url' field, the "
        "command uses it to identify the page; use --create to create a new page "
        "if the URL is not found. Use --html to read/edit HTML directly without "
        "Markdown conversion.",
    )
    edit_parser.set_defaults(func=pages_edit_command)
    add_page_options(edit_parser, required=True)
    canvaslms.cli.content.add_file_option(edit_parser)
    edit_parser.add_argument(
        "--create",
        action="store_true",
        help="Create a new page if the URL in the YAML is not found",
    )
    edit_parser.add_argument(
        "--html",
        action="store_true",
        help="Read file as HTML instead of converting from Markdown. "
        "In interactive mode, edit HTML directly.",
    )
