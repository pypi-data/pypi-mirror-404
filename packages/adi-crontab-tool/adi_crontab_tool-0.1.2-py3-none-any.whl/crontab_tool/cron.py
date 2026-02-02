from __future__ import annotations

from dataclasses import dataclass


class CronParseError(ValueError):
    pass


_MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

_DOW = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}


def _split(expr: str) -> list[str]:
    parts = expr.strip().split()
    if len(parts) != 5:
        raise CronParseError(f"expected 5 fields, got {len(parts)}")
    return parts


def _to_int(token: str, field: str, name_map: dict[str, int] | None) -> int:
    t = token.strip().upper()
    if name_map and t in name_map:
        return name_map[t]
    try:
        return int(t)
    except ValueError as e:
        raise CronParseError(f"{field}: invalid value {token!r}") from e


def _validate_range(start: int, end: int, min_v: int, max_v: int, field: str) -> None:
    if start < min_v or end > max_v or start > end:
        raise CronParseError(f"{field}: range {start}-{end} out of [{min_v},{max_v}]")


def _parse_all(min_v: int, max_v: int) -> set[int]:
    return set(range(min_v, max_v + 1))


def _parse_step(part: str, min_v: int, max_v: int, field: str, name_map: dict[str, int] | None) -> set[int]:
    left, step_s = part.split("/", 1)
    step = _to_int(step_s, field, None)
    if step <= 0:
        raise CronParseError(f"{field}: step must be > 0")

    if left == "*":
        start, end = min_v, max_v
    elif "-" in left:
        a_s, b_s = left.split("-", 1)
        start = _to_int(a_s, field, name_map)
        end = _to_int(b_s, field, name_map)
    else:
        raise CronParseError(f"{field}: bad step syntax {part!r}")

    _validate_range(start, end, min_v, max_v, field)
    return set(range(start, end + 1, step))


def _parse_range(part: str, min_v: int, max_v: int, field: str, name_map: dict[str, int] | None) -> set[int]:
    a_s, b_s = part.split("-", 1)
    start = _to_int(a_s, field, name_map)
    end = _to_int(b_s, field, name_map)

    _validate_range(start, end, min_v, max_v, field)
    return set(range(start, end + 1))


def _parse_single(part: str, min_v: int, max_v: int, field: str, name_map: dict[str, int] | None) -> set[int]:
    v = _to_int(part, field, name_map)
    if v < min_v or v > max_v:
        raise CronParseError(f"{field}: {v} out of range [{min_v},{max_v}]")
    return {v}


def _parse_part(part: str, min_v: int, max_v: int, field: str, name_map: dict[str, int] | None) -> set[int]:
    part = part.strip()
    if not part:
        raise CronParseError(f"{field}: empty")

    if "/" in part:
        return _parse_step(part, min_v, max_v, field, name_map)

    if part == "*":
        return _parse_all(min_v, max_v)

    if "-" in part:
        return _parse_range(part, min_v, max_v, field, name_map)

    return _parse_single(part, min_v, max_v, field, name_map)


def _parse_field(token: str, min_v: int, max_v: int, field: str, name_map: dict[str, int] | None) -> set[int]:
    token = token.strip()
    if not token:
        raise CronParseError(f"{field}: empty")

    if "," in token:
        out: set[int] = set()
        for part in token.split(","):
            out |= _parse_part(part, min_v, max_v, field, name_map)
        return out

    return _parse_part(token, min_v, max_v, field, name_map)


@dataclass(frozen=True)
class CronExpr:
    minute: set[int]
    hour: set[int]
    dom: set[int]
    month: set[int]
    dow: set[int]

    @staticmethod
    def parse(expr: str) -> "CronExpr":
        m, h, dom, mon, dow = _split(expr)

        minute = _parse_field(m, 0, 59, "minute", None)
        hour = _parse_field(h, 0, 23, "hour", None)
        day_of_month = _parse_field(dom, 1, 31, "day-of-month", None)
        month = _parse_field(mon, 1, 12, "month", _MONTHS)
        day_of_week = _parse_field(dow, 0, 6, "day-of-week", _DOW)

        return CronExpr(
            minute=minute,
            hour=hour,
            dom=day_of_month,
            month=month,
            dow=day_of_week,
        )
