"""Command-line interface for the 175 Days Lifestyle Challenge."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

from analyse import habits_by_periodicity, longest_streak_all, longest_streak_for_habit, streak_table
from database import (
    DEFAULT_DATABASE_PATH,
    DuplicateCompletionError,
    HabitNotFoundError,
    HabitRepository,
)


def parse_identifier(value: str):
    """Use a numeric database ID when possible; otherwise keep the habit name."""

    return int(value) if value.isdigit() else value


def parse_datetime(value: str) -> datetime:
    """Parse an ISO-8601 date or timestamp supplied to ``check --at``."""

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Use ISO format, for example 2026-07-18 or 2026-07-18T07:30:00."
        ) from exc
    if "T" not in value and " " not in value:
        parsed = parsed.replace(hour=12)
    return parsed


def render_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Render a dependency-free text table for terminal output."""

    values = [[str(cell) for cell in row] for row in rows]
    widths = [
        max([len(headers[index])] + [len(row[index]) for row in values])
        for index in range(len(headers))
    ]
    header = "  ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))
    divider = "  ".join("-" * width for width in widths)
    body = [
        "  ".join(row[index].ljust(widths[index]) for index in range(len(headers)))
        for row in values
    ]
    return "\n".join([header, divider] + body)


def build_parser() -> argparse.ArgumentParser:
    """Create the command structure exposed to users."""

    default_database = os.environ.get("HABITS_DB_PATH", str(DEFAULT_DATABASE_PATH))
    parser = argparse.ArgumentParser(
        description="Track daily and weekly habits during a 175-day lifestyle challenge."
    )
    parser.add_argument(
        "--database",
        default=default_database,
        help="SQLite file to use (default: %(default)s or HABITS_DB_PATH).",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Create the database and load the five example habits.")

    list_parser = subparsers.add_parser("list", help="List tracked habits.")
    list_parser.add_argument("--periodicity", choices=("daily", "weekly"))

    add_parser = subparsers.add_parser("add", help="Create a new habit.")
    add_parser.add_argument("name", help="Unique habit name.")
    add_parser.add_argument("periodicity", choices=("daily", "weekly"))
    add_parser.add_argument(
        "--description", required=True, help="What must be done for the habit to count."
    )

    check_parser = subparsers.add_parser("check", help="Check off a habit for its period.")
    check_parser.add_argument("habit", help="Habit name or numeric ID.")
    check_parser.add_argument("--at", type=parse_datetime, help="Optional ISO date or timestamp.")

    delete_parser = subparsers.add_parser("delete", help="Delete a habit and its history.")
    delete_parser.add_argument("habit", help="Habit name or numeric ID.")

    analytics_parser = subparsers.add_parser("analytics", help="Inspect longest streaks.")
    analytics_parser.add_argument("--habit", help="Show the longest streak for one habit.")
    analytics_parser.add_argument("--periodicity", choices=("daily", "weekly"))

    return parser


def handle_init(repository: HabitRepository) -> int:
    added = repository.ensure_seeded()
    if added:
        print("Created the database with 5 habits and four weeks of example data.")
    else:
        print("Database is ready; existing data was left unchanged.")
    return 0


def handle_list(repository: HabitRepository, periodicity: Optional[str]) -> int:
    habits = repository.list_habits()
    selected = habits_by_periodicity(habits, periodicity) if periodicity else habits
    if not selected:
        print("No habits found.")
        return 0
    rows = [
        (habit.id, habit.name, habit.periodicity, habit.created_at.date(), habit.description)
        for habit in selected
    ]
    print(render_table(("ID", "Habit", "Period", "Created", "Definition"), rows))
    return 0


def handle_analytics(
    repository: HabitRepository,
    habit_identifier: Optional[str],
    periodicity: Optional[str],
) -> int:
    habits = repository.list_habits()
    completion_map = repository.completion_map()

    if habit_identifier:
        habit = repository.get_habit(parse_identifier(habit_identifier))
        streak = longest_streak_for_habit(habit, completion_map.get(habit.id, []))
        print("Longest streak for '{}': {} {} period(s).".format(habit.name, streak, habit.periodicity))
        return 0

    selected = habits_by_periodicity(habits, periodicity) if periodicity else habits
    rows = [
        (habit.name, habit.periodicity, streak, len(completion_map.get(habit.id, [])))
        for habit, streak in streak_table(selected, completion_map)
    ]
    print(render_table(("Habit", "Period", "Longest streak", "Check-offs"), rows))
    winner, streak = longest_streak_all(selected, completion_map)
    if winner is not None:
        print("\nOverall longest streak: '{}' with {} {} period(s).".format(
            winner.name, streak, winner.periodicity
        ))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Run one CLI command and return a process exit status."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    repository = HabitRepository(Path(args.database))

    try:
        if args.command == "init":
            return handle_init(repository)

        repository.ensure_seeded()

        if args.command == "list":
            return handle_list(repository, args.periodicity)
        if args.command == "add":
            habit = repository.add_habit(args.name, args.description, args.periodicity)
            print("Created habit #{}: {}".format(habit.id, habit))
            return 0
        if args.command == "check":
            identifier = parse_identifier(args.habit)
            habit = repository.get_habit(identifier)
            completed_at = repository.add_completion(identifier, args.at)
            print("Checked off '{}' at {}.".format(habit.name, completed_at.isoformat(sep=" ")))
            return 0
        if args.command == "delete":
            habit = repository.delete_habit(parse_identifier(args.habit))
            print("Deleted '{}' and its completion history.".format(habit.name))
            return 0
        if args.command == "analytics":
            return handle_analytics(repository, args.habit, args.periodicity)
    except (ValueError, HabitNotFoundError, DuplicateCompletionError) as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        return 2

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
