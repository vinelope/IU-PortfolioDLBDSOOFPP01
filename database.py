"""SQLite persistence layer for habits and their completion timestamps."""

import json
import sqlite3
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Union

from habit import Habit, next_period_start, period_start


DEFAULT_DATABASE_PATH = Path("data/habits.db")
DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "four_week_example.json"


class HabitNotFoundError(LookupError):
    """Raised when a requested habit identifier does not exist."""


class DuplicateCompletionError(ValueError):
    """Raised when a habit is checked off twice in the same period."""


HabitIdentifier = Union[int, str]


class HabitRepository:
    """Store and retrieve habit data through a small, explicit repository API.

    The CLI never sends SQL directly. This class forms the boundary between
    application logic and SQLite and keeps database concerns out of the domain
    model and the functional analytics module.
    """

    def __init__(self, database_path: Union[str, Path] = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Create the schema when the database is opened for the first time."""

        schema = """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            description TEXT NOT NULL,
            periodicity TEXT NOT NULL CHECK (periodicity IN ('daily', 'weekly')),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_completions_habit_time
        ON completions(habit_id, completed_at);
        """
        with self._connect() as connection:
            connection.executescript(schema)

    @staticmethod
    def _row_to_habit(row: sqlite3.Row) -> Habit:
        return Habit(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            periodicity=row["periodicity"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def add_habit(
        self,
        name: str,
        description: str,
        periodicity: str,
        created_at: Optional[datetime] = None,
    ) -> Habit:
        """Validate and persist a new habit, then return it with its ID."""

        habit = Habit(
            name=name,
            description=description,
            periodicity=periodicity,
            created_at=created_at or datetime.now(),
        )
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO habits(name, description, periodicity, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        habit.name,
                        habit.description,
                        habit.periodicity,
                        habit.created_at.isoformat(timespec="seconds"),
                    ),
                )
                habit_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("A habit named '{}' already exists.".format(habit.name)) from exc
            raise

        return Habit(
            id=habit_id,
            name=habit.name,
            description=habit.description,
            periodicity=habit.periodicity,
            created_at=habit.created_at,
        )

    def list_habits(self) -> List[Habit]:
        """Return every tracked habit ordered by name."""

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name, description, periodicity, created_at "
                "FROM habits ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [self._row_to_habit(row) for row in rows]

    def get_habit(self, identifier: HabitIdentifier) -> Habit:
        """Find one habit by numeric ID or case-insensitive name."""

        with self._connect() as connection:
            if isinstance(identifier, int):
                row = connection.execute(
                    "SELECT id, name, description, periodicity, created_at "
                    "FROM habits WHERE id = ?",
                    (identifier,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT id, name, description, periodicity, created_at "
                    "FROM habits WHERE name = ? COLLATE NOCASE",
                    (identifier.strip(),),
                ).fetchone()

        if row is None:
            raise HabitNotFoundError("Habit '{}' was not found.".format(identifier))
        return self._row_to_habit(row)

    def delete_habit(self, identifier: HabitIdentifier) -> Habit:
        """Delete a habit and its completion history, returning the deleted habit."""

        habit = self.get_habit(identifier)
        with self._connect() as connection:
            connection.execute("DELETE FROM habits WHERE id = ?", (habit.id,))
        return habit

    def add_completion(
        self,
        identifier: HabitIdentifier,
        completed_at: Optional[datetime] = None,
    ) -> datetime:
        """Check off a habit once in its current daily or weekly period."""

        habit = self.get_habit(identifier)
        completion_time = (completed_at or datetime.now()).replace(microsecond=0)
        if completion_time < habit.created_at:
            raise ValueError("A completion cannot be earlier than the habit creation time.")

        start_date = period_start(completion_time, habit.periodicity)
        end_date = next_period_start(start_date, habit.periodicity)
        start_time = datetime.combine(start_date, time.min)
        end_time = datetime.combine(end_date, time.min)

        with self._connect() as connection:
            duplicate = connection.execute(
                """
                SELECT 1 FROM completions
                WHERE habit_id = ? AND completed_at >= ? AND completed_at < ?
                LIMIT 1
                """,
                (
                    habit.id,
                    start_time.isoformat(timespec="seconds"),
                    end_time.isoformat(timespec="seconds"),
                ),
            ).fetchone()
            if duplicate is not None:
                raise DuplicateCompletionError(
                    "'{}' is already complete for this {} period.".format(
                        habit.name, habit.periodicity
                    )
                )
            connection.execute(
                "INSERT INTO completions(habit_id, completed_at) VALUES (?, ?)",
                (habit.id, completion_time.isoformat(timespec="seconds")),
            )
        return completion_time

    def list_completions(self, identifier: HabitIdentifier) -> List[datetime]:
        """Return all check-off timestamps for one habit in chronological order."""

        habit = self.get_habit(identifier)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT completed_at FROM completions "
                "WHERE habit_id = ? ORDER BY completed_at",
                (habit.id,),
            ).fetchall()
        return [datetime.fromisoformat(row["completed_at"]) for row in rows]

    def completion_map(self) -> Dict[int, List[datetime]]:
        """Return completion timestamps grouped by habit ID."""

        habits = self.list_habits()
        return {habit.id: self.list_completions(habit.id) for habit in habits}

    def count_habits(self) -> int:
        """Return the number of habits currently stored."""

        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM habits").fetchone()[0])

    def load_fixture(self, fixture_path: Union[str, Path] = DEFAULT_FIXTURE_PATH) -> int:
        """Load predefined habits and four weeks of example tracking data.

        The operation is intentionally allowed only on an empty database so
        repeated application starts never duplicate or overwrite user data.
        """

        if self.count_habits() != 0:
            return 0

        path = Path(fixture_path)
        with path.open("r", encoding="utf-8") as fixture_file:
            fixture = json.load(fixture_file)

        with self._connect() as connection:
            for item in fixture["habits"]:
                habit = Habit(
                    name=item["name"],
                    description=item["description"],
                    periodicity=item["periodicity"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                )
                cursor = connection.execute(
                    """
                    INSERT INTO habits(name, description, periodicity, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        habit.name,
                        habit.description,
                        habit.periodicity,
                        habit.created_at.isoformat(timespec="seconds"),
                    ),
                )
                habit_id = cursor.lastrowid
                connection.executemany(
                    "INSERT INTO completions(habit_id, completed_at) VALUES (?, ?)",
                    [
                        (habit_id, datetime.fromisoformat(value).isoformat(timespec="seconds"))
                        for value in item["completions"]
                    ],
                )
        return len(fixture["habits"])

    def ensure_seeded(self) -> int:
        """Load the supplied demonstration fixture if the database is empty."""

        return self.load_fixture(DEFAULT_FIXTURE_PATH)


# Compatibility alias for the class name used in the original concept draft.
HabitDB = HabitRepository
