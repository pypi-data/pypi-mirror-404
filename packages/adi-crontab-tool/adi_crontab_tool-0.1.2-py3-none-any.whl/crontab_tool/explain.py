from __future__ import annotations

from crontab_tool.cron import CronExpr

DOW_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTH_NAMES = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _is_all(values: set[int], min_v: int, max_v: int) -> bool:
    return values == set(range(min_v, max_v + 1))


def _fmt_set(values: set[int], names: list[str] | None = None) -> str:
    xs = sorted(values)
    if names:
        txt = [names[i] for i in xs]
    else:
        txt = [str(i) for i in xs]
    return txt[0] if len(txt) == 1 else ", ".join(txt)


def _detect_step(values: set[int], min_v: int, max_v: int) -> int | None:
    """Detect if values follow a step pattern (e.g., every N). Returns step or None."""
    if not values:
        return None
    sorted_vals = sorted(values)
    if len(sorted_vals) < 2:
        return None
    
    # Check if it starts at min_v and follows a regular step
    if sorted_vals[0] != min_v:
        return None
    
    step = sorted_vals[1] - sorted_vals[0]
    if step <= 0:
        return None
    
    # Verify all values follow this step pattern starting from min_v
    expected = set(range(min_v, max_v + 1, step))
    return step if values == expected else None


def explain_cron(c: CronExpr) -> str:
    # Detect patterns
    minute_step = _detect_step(c.minute, 0, 59)
    hour_step = _detect_step(c.hour, 0, 23)
    all_hours = _is_all(c.hour, 0, 23)
    all_minutes = _is_all(c.minute, 0, 59)
    all_dom = _is_all(c.dom, 1, 31)
    all_months = _is_all(c.month, 1, 12)
    all_dow = _is_all(c.dow, 0, 6)

    # Build time part with smart detection
    if all_hours and all_minutes:
        time_part = "Every minute"
    elif all_hours and minute_step and minute_step > 1:
        time_part = f"Every {minute_step} minutes"
    elif all_hours and len(c.minute) == 1:
        mm = next(iter(c.minute))
        time_part = f"At minute {mm:02d} of every hour"
    elif hour_step and hour_step > 1 and len(c.minute) == 1:
        mm = next(iter(c.minute))
        time_part = f"At minute {mm:02d} past every {hour_step} hours"
    elif len(c.hour) == 1 and len(c.minute) == 1:
        hh = next(iter(c.hour))
        mm = next(iter(c.minute))
        time_part = f"At {hh:02d}:{mm:02d}"
    elif all_hours and len(c.minute) <= 5:
        time_part = f"At minute(s) {_fmt_set(c.minute)}"
    elif len(c.minute) == 1:
        mm = next(iter(c.minute))
        if len(c.hour) <= 5:
            time_part = f"At minute {mm:02d} past hour(s) {_fmt_set(c.hour)}"
        else:
            time_part = f"At minute {mm:02d}"
    else:
        # Fallback
        time_part = f"At specific times"

    # Build date constraints (only show if NOT all)
    parts = [time_part]
    
    if not all_dom:
        parts.append(f"on day(s) {_fmt_set(c.dom)} of the month")
    
    if not all_months:
        parts.append(f"in {_fmt_set(c.month, MONTH_NAMES)}")
    
    if not all_dow:
        parts.append(f"on {_fmt_set(c.dow, DOW_NAMES)}")

    return ", ".join(parts) + "."
