import arrow
import datetime


def format_local_time(iso_ts):
    """
    Formats an ISO timestamp string in local time (YYYY-MM-DD HH:mm).
    """
    if not iso_ts:
        return "N/A"
    try:
        return arrow.get(iso_ts).to("local").format("YYYY-MM-DD HH:mm")
    except Exception:
        return iso_ts


def format_canvas_time(iso_ts):
    """
    Parses an ISO timestamp string as local time and converts to UTC ISO format.
    Returns Canvas-compatible UTC timestamp ending with 'Z'.
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


def _has_explicit_timezone(date_str):
    """
    Detect if a string contains explicit timezone information.

    Markers indicating explicit timezone:
    - 'Z' suffix (UTC)
    - '+' or '-' with time offset (e.g., +02:00, -05:00)

    Returns True if timezone is explicit, False for naive strings.
    """
    if not isinstance(date_str, str):
        return False
    # Check for Z suffix indicating UTC
    if "Z" in date_str:
        return True
    # Check for timezone offset (+/- with time)
    # Date strings like YYYY-MM-DD have 2 hyphens
    # Timezone offsets add more: YYYY-MM-DDTHH:MM:SS-05:00 has 3+ hyphens
    if "+" in date_str or date_str.count("-") > 2:
        return True
    return False


def parse_date(date_str):
    """Parse a date string using arrow with multiple format attempts

    Returns a Canvas-compatible UTC timestamp ending with 'Z'
    """
    if not date_str or date_str.lower() in ["none", "clear", ""]:
        return None

    # Try common formats in order of preference
    formats = [
        None,  # ISO format (arrow's default)
        "YYYY-MM-DD HH:mm:ss",
        "YYYY-MM-DD HH:mm",
        "YYYY-MM-DD",
        "MMM DD YYYY",
        "MMMM DD, YYYY",
        "MM/DD/YYYY",
        "DD/MM/YYYY",
        "YYYY/MM/DD",
    ]

    for fmt in formats:
        try:
            if fmt is None:
                # Check if string has explicit timezone info
                if _has_explicit_timezone(date_str):
                    # Preserve explicit timezone
                    return format_canvas_time(arrow.get(date_str))
                else:
                    # Interpret naive string as local time
                    return format_canvas_time(arrow.get(date_str, tzinfo="local"))
            else:
                # Format-specific strings never include timezone, always use local
                return format_canvas_time(arrow.get(date_str, fmt, tzinfo="local"))
        except (arrow.parser.ParserError, ValueError):
            continue

    # If nothing worked, try natural language parsing
    try:
        import dateutil.parser

        parsed_date = dateutil.parser.parse(date_str)
        # Use format_canvas_time for Canvas compatibility
        return format_canvas_time(arrow.get(parsed_date))
    except (ImportError, ValueError):
        pass

    raise ValueError(
        f"Could not parse date: '{date_str}'. "
        "Try formats like: YYYY-MM-DD, YYYY-MM-DD HH:MM, or MM/DD/YYYY"
    )
