# 175 Days Lifestyle Challenge

A local, command-line habit tracker built for IU course **DLBDSOOFPP01 - Object Oriented and Functional Programming with Python**. It helps users define daily or weekly habits, check them off, persist their history, and inspect their longest streaks.

## Why 175 days?

The number creates a memorable challenge that lasts just under six months (less than half a year). It is long enough for daily and weekly progress to become visible, while remaining a finite milestone. The app supports the journey; it does not promise a scientifically guaranteed time for changing behaviour.

## Features

- Create and delete daily or weekly habits.
- Check off a habit once in each applicable period.
- Store creation times and every completion time in SQLite.
- Start with five predefined habits and four weeks of example tracking data.
- List all habits or filter them by periodicity.
- Calculate the longest streak for every habit, one selected habit, or the overall tracker.
- Keep analytics pure and functional through `map`, `filter`, `reduce`, and immutable inputs.
- Run without third-party runtime dependencies.

## Architecture

The implementation refines the conception-phase design into four clear responsibilities:

1. `main.py` is the command-line interface and translates user commands into application calls.
2. `habit.py` contains the immutable `Habit` domain class and period rules.
3. `database.py` is the repository boundary; it is the only layer that communicates with SQLite.
4. `analyse.py` receives habits and completion data and returns analytics without database access or mutation.

This separation means the interface does **not** communicate directly with the database. The Python domain and repository code validates every operation first.

## Requirements

- Python 3.7 or later
- Git (only needed to clone the repository)

SQLite, `argparse`, JSON support, and the test framework are part of Python's standard library.

## Installation

```bash
git clone https://github.com/vinelope/IU-PortfolioDLBDSOOFPP01.git
cd IU-PortfolioDLBDSOOFPP01

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## First run

```bash
python main.py init
```

This creates `data/habits.db` and imports the demonstration fixture from `fixtures/four_week_example.json`. The fixture contains four daily habits, one weekly habit, and four weeks of example check-offs. Running `init` again is safe: existing data is never overwritten.

## Usage

List all habits or only habits with one periodicity:

```bash
python main.py list
python main.py list --periodicity daily
python main.py list --periodicity weekly
```

Create a personalised habit:

```bash
python main.py add "Drink water" daily --description "Drink two litres of water."
python main.py add "Call family" weekly --description "Have one meaningful family call."
```

Check off a habit by name or numeric ID:

```bash
python main.py check "Drink water"
python main.py check 2
```

For a reproducible demonstration, an ISO date or timestamp can be supplied. A second check-off in the same daily or weekly period is rejected:

```bash
python main.py check "Drink water" --at 2026-07-18T09:30:00
```

Inspect analytics:

```bash
python main.py analytics
python main.py analytics --periodicity weekly
python main.py analytics --habit "Read non-fiction for 15 minutes"
```

Delete a habit and its completion history:

```bash
python main.py delete "Drink water"
```

Use a different database file with either `--database path/to/file.db` before the command or the `HABITS_DB_PATH` environment variable.

## Streak definition

A completion belongs to a calendar period. Daily periods start at midnight; weekly periods follow ISO weeks and start on Monday. Multiple timestamps in the same period count once. A streak is the longest sequence of consecutive completed periods. Missing a completed period breaks the streak.

## Tests

Run the complete unit and integration test suite:

```bash
python -m unittest -v
```

The tests cover validation, daily and weekly period boundaries, persistence, duplicate protection, deletion, fixture integrity, functional streak analytics, and the end-to-end CLI.

## Project structure

```text
.
├── main.py                         # CLI and user-facing output
├── habit.py                        # Object-oriented domain model
├── database.py                     # SQLite repository
├── analyse.py                      # Functional analytics
├── fixtures/
│   └── four_week_example.json      # Five predefined habits and test data
├── test_project.py                 # Unit and integration tests
└── requirements.txt                # Standard-library-only runtime
```

## Development reflection

The conception draft correctly identified a `Habit` class, database persistence, and a user interface, but the first diagram connected the interface directly to the database. Implementation revealed the missing application boundary. The revised design routes commands through validated Python objects and a repository before SQLite. This reduced coupling, made the functional analytics independently testable, and prevented invalid or duplicate check-offs. The next phase can refine presentation, error messaging, and optional progress-rate analytics after tutor feedback.
