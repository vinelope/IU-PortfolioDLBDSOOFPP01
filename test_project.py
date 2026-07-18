"""Unit and integration tests for the 175 Days habit tracker."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from analyse import habits_by_periodicity, longest_streak_all, longest_streak_for_habit
from database import DuplicateCompletionError, HabitNotFoundError, HabitRepository
from habit import Habit, period_start
from main import main as cli_main


class HabitModelTests(unittest.TestCase):
    def test_habit_normalizes_and_validates_input(self):
        habit = Habit("  Read  ", "  Read 15 minutes  ", "DAILY", datetime(2026, 6, 20))
        self.assertEqual(habit.name, "Read")
        self.assertEqual(habit.periodicity, "daily")

        with self.assertRaises(ValueError):
            Habit("", "Description", "daily", datetime(2026, 6, 20))
        with self.assertRaises(ValueError):
            Habit("Read", "Description", "monthly", datetime(2026, 6, 20))

    def test_weekly_periods_start_on_monday(self):
        self.assertEqual(
            str(period_start(datetime(2026, 7, 18, 9, 30), "weekly")),
            "2026-07-13",
        )


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        self.repository = HabitRepository(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_create_retrieve_check_and_delete_habit(self):
        habit = self.repository.add_habit(
            "Hydrate",
            "Drink two litres of water.",
            "daily",
            datetime(2026, 7, 1, 8, 0),
        )
        self.assertEqual(self.repository.get_habit(habit.id).name, "Hydrate")

        self.repository.add_completion(habit.id, datetime(2026, 7, 2, 10, 0))
        self.assertEqual(len(self.repository.list_completions(habit.id)), 1)
        with self.assertRaises(DuplicateCompletionError):
            self.repository.add_completion(habit.id, datetime(2026, 7, 2, 20, 0))

        self.repository.delete_habit(habit.id)
        with self.assertRaises(HabitNotFoundError):
            self.repository.get_habit(habit.id)

    def test_weekly_habit_allows_one_check_off_per_iso_week(self):
        habit = self.repository.add_habit(
            "Reflect",
            "Write a weekly progress note.",
            "weekly",
            datetime(2026, 6, 1),
        )
        self.repository.add_completion(habit.id, datetime(2026, 7, 13, 9, 0))
        with self.assertRaises(DuplicateCompletionError):
            self.repository.add_completion(habit.id, datetime(2026, 7, 19, 18, 0))
        self.repository.add_completion(habit.id, datetime(2026, 7, 20, 9, 0))
        self.assertEqual(len(self.repository.list_completions(habit.id)), 2)

    def test_fixture_supplies_five_habits_and_four_weeks_of_data(self):
        loaded = self.repository.ensure_seeded()
        habits = self.repository.list_habits()
        self.assertEqual(loaded, 5)
        self.assertEqual(len(habits), 5)
        self.assertEqual(len(habits_by_periodicity(habits, "daily")), 4)
        self.assertEqual(len(habits_by_periodicity(habits, "weekly")), 1)
        self.assertTrue(all(self.repository.list_completions(habit.id) for habit in habits))
        self.assertEqual(self.repository.ensure_seeded(), 0)


class AnalyticsTests(unittest.TestCase):
    def test_daily_and_weekly_longest_streaks(self):
        daily = Habit("Daily", "Daily test habit.", "daily", datetime(2026, 7, 1), id=1)
        daily_completions = [
            datetime(2026, 7, 1, 8),
            datetime(2026, 7, 2, 8),
            datetime(2026, 7, 3, 8),
            datetime(2026, 7, 5, 8),
        ]
        self.assertEqual(longest_streak_for_habit(daily, daily_completions), 3)

        weekly = Habit("Weekly", "Weekly test habit.", "weekly", datetime(2026, 6, 1), id=2)
        weekly_completions = [
            datetime(2026, 6, 1),
            datetime(2026, 6, 8),
            datetime(2026, 6, 15),
            datetime(2026, 6, 29),
        ]
        self.assertEqual(longest_streak_for_habit(weekly, weekly_completions), 3)

    def test_fixture_global_longest_streak_is_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = HabitRepository(Path(directory) / "fixture.db")
            repository.ensure_seeded()
            winner, streak = longest_streak_all(
                repository.list_habits(), repository.completion_map()
            )
            self.assertEqual(winner.name, "Read non-fiction for 15 minutes")
            self.assertEqual(streak, 28)


class CommandLineTests(unittest.TestCase):
    def test_cli_initialization_listing_and_analytics(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "cli.db")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(cli_main(["--database", database, "init"]), 0)
                self.assertEqual(cli_main(["--database", database, "list", "--periodicity", "weekly"]), 0)
                self.assertEqual(cli_main(["--database", database, "analytics"]), 0)
            rendered = output.getvalue()
            self.assertIn("four weeks of example data", rendered)
            self.assertIn("Write a weekly reflection", rendered)
            self.assertIn("Overall longest streak", rendered)


if __name__ == "__main__":
    unittest.main()
