import argparse
import canvasapi
import canvaslms.cli.courses as courses
import csv
import re
import sys


def modules_list_command(config, canvas, args):
    output = csv.writer(sys.stdout, delimiter=args.delimiter)
    course_list = courses.process_course_option(canvas, args)

    for course in course_list:
        modules = filter_modules(course, args.regex)
        for module in modules:
            # Get module items count
            try:
                items = list(module.get_module_items())
                item_count = len(items)
            except:
                item_count = 0

            sequential = (
                module.require_sequential_progress
                if hasattr(module, "require_sequential_progress")
                else False
            )
            progress_mode = "sequential" if sequential else "any-order"

            output.writerow(
                [
                    course.course_code,
                    module.name,
                    module.unlock_at if hasattr(module, "unlock_at") else None,
                    progress_mode,
                    item_count,
                ]
            )


def modules_view_command(config, canvas, args):
    output = csv.writer(sys.stdout, delimiter=args.delimiter)
    course_list = courses.process_course_option(canvas, args)

    for course in course_list:
        modules = filter_modules(course, args.regex)
        for module in modules:
            try:
                items = list(module.get_module_items())
                if not items:
                    # Show module even if it has no items
                    row = [course.course_code, module.name, "No items", ""]
                    if args.show_id:
                        row.append("")
                    row.append("")
                    output.writerow(row)
                else:
                    for item in items:
                        completion_req = ""
                        if (
                            hasattr(item, "completion_requirement")
                            and item.completion_requirement
                        ):
                            req = item.completion_requirement
                            if "type" in req:
                                completion_req = req["type"]
                                if "min_score" in req:
                                    completion_req += (
                                        f" (min score: {req['min_score']})"
                                    )
                        row = [
                            course.course_code,
                            module.name,
                            item.type if hasattr(item, "type") else "Unknown",
                            item.title if hasattr(item, "title") else "No title",
                        ]

                        if args.show_id:
                            if hasattr(item, "content_id"):
                                row.append(item.content_id)
                            elif hasattr(item, "id"):
                                row.append(item.id)
                            else:
                                row.append("")

                        row.append(completion_req)
                        output.writerow(row)
            except:
                # If we can't get items, show the module with error
                row = [course.course_code, module.name, "Error loading items", ""]
                if args.show_id:
                    row.append("")
                row.append("")
                output.writerow(row)


def add_module_option(parser, required=False):
    """Adds module selection option to parser"""
    try:
        courses.add_course_option(parser, required=required)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-M",
        "--module",
        required=required,
        default="" if not required else None,
        help="Regex matching module title or Canvas identifier.",
    )


def process_module_option(canvas, args):
    """Processes module selection from command line args"""
    course_list = courses.process_course_option(canvas, args)
    modules_list = []

    for course in course_list:
        try:
            module_regex = args.module
        except AttributeError:
            module_regex = ".*"

        if module_regex:
            modules = filter_modules(course, module_regex)
            modules_list.extend(modules)

    return modules_list


def filter_modules(course, regex):
    """Returns all modules of course whose name matches regex"""
    name = re.compile(regex)
    return filter(
        lambda module: name.search(module.name) or name.search(str(module.id)),
        course.get_modules(),
    )


def filter_assignments_by_module(module, assignments):
    """Returns elements in assignments that are part of module"""
    # Get all module items that are assignments
    assignment_ids = set()
    try:
        for item in module.get_module_items():
            if hasattr(item, "type") and item.type == "Assignment":
                assignment_ids.add(item.content_id)
    except AttributeError:
        # Handle cases where module items don't have expected attributes
        pass

    for assignment in assignments:
        if assignment.id in assignment_ids:
            yield assignment


def filter_assignments_by_module_list(modules, assignments):
    """Returns elements in assignments that belong to any of the modules"""
    all_assignment_ids = set()
    for module in modules:
        try:
            for item in module.get_module_items():
                if hasattr(item, "type") and item.type == "Assignment":
                    all_assignment_ids.add(item.content_id)
        except AttributeError:
            pass

    for assignment in assignments:
        if assignment.id in all_assignment_ids:
            yield assignment


def filter_pages_by_module_list(modules, pages):
    """Returns elements in pages that belong to any of the modules"""
    all_page_urls = set()
    for module in modules:
        try:
            for item in module.get_module_items():
                if hasattr(item, "type") and item.type == "Page":
                    all_page_urls.add(item.page_url)
        except AttributeError:
            pass

    for page in pages:
        if page.url in all_page_urls:
            yield page


def get_item_modules(course, item_type, item_id):
    """Get list of modules containing an item.

    Args:
        course: Canvas course object
        item_type: 'Assignment' or 'Page'
        item_id: For Assignment: assignment.id (int),
                 For Page: page.url (string slug)

    Returns:
        List of module names containing this item
    """
    target_url = None
    if item_type == "Page":
        try:
            target_url = course.get_page(item_id).url
        except Exception:
            # If we can't resolve the target page, fall back to raw comparisons.
            target_url = item_id

    modules = []
    for module in course.get_modules():
        try:
            for item in module.get_module_items():
                if not hasattr(item, "type") or item.type != item_type:
                    continue
                if item_type == "Assignment":
                    if hasattr(item, "content_id") and item.content_id == item_id:
                        modules.append(module.name)
                        break
                elif item_type == "Page":
                    if hasattr(item, "page_url"):
                        if item.page_url == item_id:
                            modules.append(module.name)
                            break
                        # Compare canonical URLs to avoid duplicates when Canvas redirects old slugs.
                        try:
                            resolved_page = course.get_page(item.page_url)
                            if resolved_page.url == target_url:
                                modules.append(module.name)
                                break
                        except Exception:
                            pass
        except Exception:
            # Skip modules we can't access
            pass
    return modules


def update_item_modules(course, item_type, item_id, module_regexes):
    """Update module membership for an item based on regex patterns.

    Args:
        course: Canvas course object
        item_type: 'Assignment' or 'Page'
        item_id: For Assignment: assignment.id (int),
                 For Page: page.url (string slug)
        module_regexes: List of regex patterns to match module names.
                        Empty list means remove from all modules.

    Returns:
        Tuple of (added_modules, removed_modules) as lists of module names
    """
    all_modules = list(course.get_modules())

    matching_module_ids = set()
    for pattern in module_regexes:
        regex = re.compile(pattern)
        for module in all_modules:
            if regex.search(module.name) or regex.search(str(module.id)):
                matching_module_ids.add(module.id)
    added = []
    removed = []

    for module in all_modules:
        current_item = None
        canonical_page_url = None
        if item_type == "Page":
            try:
                canonical_page_url = course.get_page(item_id).url
            except Exception:
                canonical_page_url = item_id

        try:
            for item in module.get_module_items():
                if not hasattr(item, "type") or item.type != item_type:
                    continue
                if item_type == "Assignment":
                    if hasattr(item, "content_id") and item.content_id == item_id:
                        current_item = item
                        break
                elif item_type == "Page":
                    if hasattr(item, "page_url"):
                        if item.page_url == item_id:
                            current_item = item
                            break
                        # URLs don't match directly; compare canonical URLs to avoid duplicates.
                        try:
                            resolved_page = course.get_page(item.page_url)
                            if resolved_page.url == canonical_page_url:
                                current_item = item
                                break
                        except Exception:
                            pass  # Page doesn't exist or can't be fetched
        except Exception:
            pass
        should_be_in = module.id in matching_module_ids
        if should_be_in and current_item is None:
            # Add to module
            try:
                if item_type == "Assignment":
                    module.create_module_item(
                        {"type": "Assignment", "content_id": item_id}
                    )
                else:  # Page
                    module.create_module_item({"type": "Page", "page_url": item_id})
                added.append(module.name)
            except Exception:
                pass  # Silently skip if we can't add
        elif not should_be_in and current_item is not None:
            # Remove from module
            try:
                current_item.delete()
                removed.append(module.name)
            except Exception:
                pass  # Silently skip if we can't remove
    return added, removed


def add_command(subp):
    """Adds the subcommand and its options to argparse subparser subp"""
    modules_parser = subp.add_parser("modules", help="Work with Canvas modules")
    modules_subp = modules_parser.add_subparsers(
        dest="modules_command", help="Available module commands"
    )

    # Add 'list' subcommand
    list_parser = modules_subp.add_parser(
        "list",
        help="Lists modules of a course",
        description="Lists modules of a course. Output: course, module name, "
        "unlock at, require sequential progress, item count",
    )
    list_parser.set_defaults(func=modules_list_command)
    list_parser.add_argument(
        "regex",
        default=".*",
        nargs="?",
        help="Regex for filtering modules, default: '.*'",
    )
    courses.add_course_option(list_parser, required=True)

    # Add 'view' subcommand
    view_parser = modules_subp.add_parser(
        "view",
        help="Shows modules and their contents",
        description="Shows modules and their contents. Output: course, "
        "module name, item type, item name, [item id], "
        "completion requirement",
    )
    view_parser.set_defaults(func=modules_view_command)
    view_parser.add_argument(
        "regex",
        default=".*",
        nargs="?",
        help="Regex for filtering modules, default: '.*'",
    )
    courses.add_course_option(view_parser, required=True)
    view_parser.add_argument(
        "--show-id", action="store_true", help="Include Canvas IDs in output"
    )
