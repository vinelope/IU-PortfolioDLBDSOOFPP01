"""Pure functional analytics for habit collections.

Database access and user input are intentionally absent from this module. Each
function receives data and returns a new value without mutating its arguments,
which keeps calculations deterministic and straightforward to test.
"""

from datetime import date, datetime
from functools import reduce
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from habit import Habit, next_period_start, period_start


def all_habits(habits: Iterable[Habit]) -> List[Habit]:
    """Return all currently tracked habits as a new list."""

    return list(map(lambda habit: habit, habits))


def habits_by_periodicity(habits: Iterable[Habit], periodicity: str) -> List[Habit]:
    """Return habits matching ``daily`` or ``weekly`` using ``filter``."""

    normalized = periodicity.strip().lower()
    if normalized not in ("daily", "weekly"):
        raise ValueError("Periodicity must be 'daily' or 'weekly'.")
    return list(filter(lambda habit: habit.periodicity == normalized, habits))


def completed_periods(habit: Habit, completions: Iterable[datetime]) -> List[date]:
    """Convert timestamps to sorted, unique period starts for one habit."""

    return sorted(set(map(lambda value: period_start(value, habit.periodicity), completions)))


def longest_streak_for_habit(habit: Habit, completions: Iterable[datetime]) -> int:
    """Return the longest historical run of consecutive completed periods."""

    periods = completed_periods(habit, completions)
    if not periods:
        return 0

    def accumulate(state: Tuple[int, int, date], current: date) -> Tuple[int, int, date]:
        current_run, longest_run, previous = state
        run = current_run + 1 if current == next_period_start(previous, habit.periodicity) else 1
        return run, max(longest_run, run), current

    initial = (1, 1, periods[0])
    return reduce(accumulate, periods[1:], initial)[1]


def streak_table(
    habits: Sequence[Habit], completion_map: Dict[int, Iterable[datetime]]
) -> List[Tuple[Habit, int]]:
    """Return ``(habit, longest_streak)`` rows sorted from strongest to weakest."""

    rows = map(
        lambda habit: (
            habit,
            longest_streak_for_habit(habit, completion_map.get(habit.id, [])),
        ),
        habits,
    )
    return sorted(rows, key=lambda item: (-item[1], item[0].name.lower()))


def longest_streak_all(
    habits: Sequence[Habit], completion_map: Dict[int, Iterable[datetime]]
) -> Tuple[Optional[Habit], int]:
    """Return the habit with the longest run and the run length in periods."""

    rows = streak_table(habits, completion_map)
    return rows[0] if rows else (None, 0)
