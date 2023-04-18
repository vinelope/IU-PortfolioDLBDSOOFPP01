def habit_creation():
    """ creates a personalised habit """
    # Get an input from the user to create the personalised habit
    name = input("Give a name to your new habit: ")
    description = input("Description of your new habit: ")
    frequency = input("Define the frequency: ")
    completed = False

    # Creation of the object for the personalized habit
    habit_personalised = habit_perso(name, description, frequency, completed)

    # Save the info into database
    habit_perso.save_habit()
    print("Habit '{name}' correctly created")

def habit_complete():
    """ mark the habit as completed"""
    db = database()
    habits = db.get_all
    if habits:
        input = select("Which habit have you completed?", choices=[f"{habits[0]}" for habit in habits]).ask()
        for habit in habits:
            print(habit)
        habit_id =int(input())
        for habit in habits:
            if habit.id == habit.id:
                habit.completed = True
                habit.save_habit()
                print(f"Completed {habit.name}. Congrats")
                break
            else:
                print("Think again, something is wrong")
        else:
            print("There are nothing completed")

def habit_deletion():
    """ delete the selected habit"""
    db = database()
    habits = db.get_all_habits()
    if not habits:
        print("There is nothing to delete for now")
        return
    print("Which habit do you wanna to delete?")
    for i, habit in enumerate(habits):
        print(f"{i + 1}.{habits[1]}")
        habit_index = int(input("> ")) - 1
        habit_id = habits[habit_index][0]
        db.delete_habit(habit_id)
        print(f"Habit '{habits[habit_index][1]}' deleted.")

def list_habits():
    """ Shows the list of all habits personalised or standard ones"""
def help():
    """ shows help text for the user understand the commands """
    print("Commands:")
    print("habit_creation - create a habit")
    print("habit_complete - mark the habit as complete")
    print("habit_deletion - delete the selected habit")
    print("list_habits - list all habits")
    print("streak - get the streak for a habit")
    print("exit - exit the program")
    if __name__ == "__main__":
        help()
        while True:
            command = select("What would you like to do?", choices=["habit_creation", "habit_complete","delete_habit","list_habits","strike","exit"]).ask()
            if command == "habit_creation":
                 habit_creation()
            elif command == "habit_complete":
                 habit_complete()
            elif command == "delete_habit":
                 habit_deletion()
            elif command == "list_habits":
                 list_habits()
            elif command == "streak":
                 streak()
            elif command == "exit":
                 break
            else:
                 print("Invalid command")
def streak():
    """create the streak for the habit completed in a row"""
    db = database()
    habits = db.get_all_habits()
    habit_objects = [habit(*habit) for habit in habits]
    habit_names =[habit.name for habit in habit_objects]
    habit_names = select("Which habit do you want to get the streak for", choices=habits_names).ask()
    habit = next(filter(lambda h: h.name == habit_name, habit_objects))
    streak = habit.streak()
    print(f"Your streak for '{habit_name}' is {streak}' days")