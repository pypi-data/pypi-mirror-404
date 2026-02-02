import argparse

from crontab_tool.cron import CronExpr, CronParseError
from crontab_tool.explain import explain_cron


def cmd_validate(expr: str) -> int:
    try:
        CronExpr.parse(expr)
        print("OK")
        return 0
    except CronParseError as e:
        print(f"INVALID: {e}")
        return 2


def cmd_explain(expr: str) -> int:
    try:
        c = CronExpr.parse(expr)
        print(explain_cron(c))
        return 0
    except CronParseError as e:
        print(f"INVALID: {e}")
        return 2


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="crontab-tool",
        description="Validate and explain 5-field cron expressions",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate a cron expression")
    p_validate.add_argument("expr", help='Example: "0 9 * * SAT"')

    p_explain = sub.add_parser("explain", help="Explain a cron expression")
    p_explain.add_argument("expr", help='Example: "*/5 * * * *"')

    args = parser.parse_args()

    if args.command == "validate":
        raise SystemExit(cmd_validate(args.expr))
    raise SystemExit(cmd_explain(args.expr))
