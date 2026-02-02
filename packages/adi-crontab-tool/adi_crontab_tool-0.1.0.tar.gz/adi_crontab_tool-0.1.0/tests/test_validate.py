import pytest
from crontab_tool.cron import CronExpr, CronParseError


@pytest.mark.parametrize("expr", [
    "*/5 * * * *",
    "0 9 * * SAT",
    "15 8 1 JAN SUN",
    "0 0 1-5 1-12 0-6",
    "0,15,30,45 9 * * MON-FRI",
])
def test_valid_expressions(expr: str):
    CronExpr.parse(expr)  # should not raise


@pytest.mark.parametrize("expr", [
    "* * * *",                # not 5 fields
    "60 * * * *",             # minute out of range
    "* 24 * * *",             # hour out of range
    "* * 0 * *",              # day-of-month out of range
    "* * * 13 *",             # month out of range
    "* * * * 7",              # day-of-week out of range (we use 0-6)
    "*/0 * * * *",            # step invalid
    "5-1 * * * *",            # bad range
    "* * * FOO *",            # bad month name
])
def test_invalid_expressions(expr: str):
    with pytest.raises(CronParseError):
        CronExpr.parse(expr)
