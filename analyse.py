from datetime import datetime
from habit import HabitDB, Habit

def daily_habits_completed:
    """analyzes habits and returns list of habits completed """
    today = datetime.today().date()
    habit_db = HabitDB()
    habits = habit_db.get_all_habits()
    completed_habits = []
    for habit in habits:
        if habit.frequency == 'daily' and today in habit.completed:
            completed_habits.append(habit)
    return completed_habits

