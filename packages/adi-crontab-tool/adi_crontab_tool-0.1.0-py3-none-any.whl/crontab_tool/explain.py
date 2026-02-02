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


def explain_cron(c: CronExpr) -> str:
    # time
    if len(c.hour) == 1 and len(c.minute) == 1:
        hh = next(iter(c.hour))
        mm = next(iter(c.minute))
        time_part = f"At {hh:02d}:{mm:02d}"
    elif _is_all(c.hour, 0, 23) and _is_all(c.minute, 0, 59):
        time_part = "Every minute"
    elif len(c.minute) == 1:
        mm = next(iter(c.minute))
        time_part = f"At minute {mm:02d} past hour(s): {_fmt_set(c.hour)}"
    else:
        time_part = f"At minutes {_fmt_set(c.minute)} and hours {_fmt_set(c.hour)}"

    # date
    dom_part = "every day" if _is_all(c.dom, 1, 31) else f"on day(s) {_fmt_set(c.dom)}"
    mon_part = "every month" if _is_all(c.month, 1, 12) else f"in month(s) {_fmt_set(c.month, MONTH_NAMES)}"
    dow_part = "every day of week" if _is_all(c.dow, 0, 6) else f"on {_fmt_set(c.dow, DOW_NAMES)}"

    return f"{time_part}, {dom_part}, {mon_part}, {dow_part}."
