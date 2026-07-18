"""Domain model and period helpers for the habit tracker.

The :class:`Habit` class deliberately contains no database code.  It models a
habit and validates the information supplied by the user; persistence is the
responsibility of :mod:`database`.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Union


DAILY = "daily"
WEEKLY = "weekly"
VALID_PERIODICITIES = (DAILY, WEEKLY)


@dataclass(frozen=True)
class Habit:
    """A task that must be checked off once in every configured period.

    Attributes:
        name: Short task name shown in the command-line interface.
        description: Clear explanation of what counts as completion.
        periodicity: Either ``"daily"`` or ``"weekly"``.
        created_at: Date and time at which the habit was created.
        id: Database identifier, or ``None`` before the habit is persisted.
    """

    name: str
    description: str
    periodicity: str
    created_at: datetime
    id: Optional[int] = None

    def __post_init__(self) -> None:
        """Normalize text fields and reject incomplete or invalid habits."""

        normalized_name = self.name.strip()
        normalized_description = self.description.strip()
        normalized_periodicity = self.periodicity.strip().lower()

        if not normalized_name:
            raise ValueError("Habit name cannot be empty.")
        if not normalized_description:
            raise ValueError("Habit description cannot be empty.")
        if normalized_periodicity not in VALID_PERIODICITIES:
            raise ValueError("Periodicity must be 'daily' or 'weekly'.")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime value.")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "description", normalized_description)
        object.__setattr__(self, "periodicity", normalized_periodicity)
        object.__setattr__(self, "created_at", self.created_at.replace(microsecond=0))

    @property
    def frequency(self) -> str:
        """Return a backwards-friendly alias for ``periodicity``."""

        return self.periodicity

    def __str__(self) -> str:
        """Return the concise representation used by the CLI."""

        return "{} ({})".format(self.name, self.periodicity)


DateLike = Union[date, datetime]


def period_start(moment: DateLike, periodicity: str) -> date:
    """Return the start date of the period containing ``moment``.

    Daily periods begin on the supplied calendar date. Weekly periods use ISO
    weeks and therefore begin on Monday.
    """

    current_date = moment.date() if isinstance(moment, datetime) else moment
    normalized_periodicity = periodicity.strip().lower()

    if normalized_periodicity == DAILY:
        return current_date
    if normalized_periodicity == WEEKLY:
        return current_date - timedelta(days=current_date.weekday())
    raise ValueError("Periodicity must be 'daily' or 'weekly'.")


def next_period_start(start: date, periodicity: str) -> date:
    """Return the start date immediately after ``start`` for a periodicity."""

    if periodicity == DAILY:
        return start + timedelta(days=1)
    if periodicity == WEEKLY:
        return start + timedelta(days=7)
    raise ValueError("Periodicity must be 'daily' or 'weekly'.")
