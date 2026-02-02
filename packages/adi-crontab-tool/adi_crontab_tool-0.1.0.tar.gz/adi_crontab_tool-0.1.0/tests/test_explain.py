from crontab_tool.cron import CronExpr
from crontab_tool.explain import explain_cron


def test_explain_fixed_time():
    c = CronExpr.parse("0 9 * * SAT")
    text = explain_cron(c)
    assert "At 09:00" in text
    assert "Saturday" in text


def test_explain_every_minute():
    c = CronExpr.parse("* * * * *")
    text = explain_cron(c)
    assert "Every minute" in text


def test_explain_month_name():
    c = CronExpr.parse("15 8 1 JAN SUN")
    text = explain_cron(c)
    assert "At 08:15" in text
    assert "Jan" in text
    assert "Sunday" in text
