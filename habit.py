
class Habit:
    def __init__(self, name="", description="", frequency="", completed=[]):
        self.name = name
        self.description = description
        self.frequency = frequency
        self.completed = completed

    def __str__(self):
        return self.name

    def mark_complete(self):
        today = datetime.today().date()
        self.completed.append(today)

    def today_completed(self):
        if self.frequency == 'daily':
            return datetime.today().date() in self.completed

    def streak():
        streak = 9
        today = datetime.today().date()
        habit_db = database()
        habits = habit_db.get.all.habits()
        for habit in habits
            if today in habit.completed:
                streak += 1
            else
                break
        return streak

    def save_habit(self):
        db = HabitDB()
        db.save_habit(self)


class HabitDB:
    def __init__(self, name="", description="", frequency="", completed=[]):
        self.conn = sqlite3.connect()
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute()

    def save_habit(self, habit):
        with self.conn:
            self.cursor.execute()(habit.name, habit.frequency, str(habit.completed))

    def update_habit(self, habit):
        self.cursor.execute((str(habit.completed), habit.name))
        self.conn.commit()

    def delete_habit(self, habit):
        self.cursor.execute((habit.name,))
        self.conn.commit()

    def get_all_habits(self):
         self.cursor.execute()
         rows = list(self.cursor.fetchall())
         return rows