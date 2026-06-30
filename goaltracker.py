import csv
from datetime import datetime, date, timedelta

from goal_utils import (
    calculate_completion_percentage,
    calculate_estimated_completion,
    on_track_tracker
)

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"


headers = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Est_Completion_Date",
    "Behind_On Track_Ahead", "Streak", "Status", "Completion_%"
]


def add_new_goal():
    while True:
        goal_name = input(f"Enter Your New Goal Name")
        goal_category = int(input(f"Enter Your New Goals Category:\n1. Learning\n2. Project \n3. Health & Fitness \n4. Academic)"))
        if goal_category < 1 or goal_category > 4 or isinstance(goal_category, str) == True:
            print("Error. Enter one of the numbers listed")
            continue
        elif goal_category == 1:
            goal_category = "Learning"
        elif goal_category == 2:
            goal_category = "Project"
        elif goal_category == 3:
            goal_category = "Health & Fitness"
        elif goal_category == 4:
            goal_category = "Academic"


        goal_length = int(input(f"Enter Estimated Hours Till Completion"))
        goal_due_date = input(f"When Do You Want To Finish This? (mm/dd/yyyy format) Or 'Skip' To Skip")
    
        if goal_due_date.lower() == "skip":
            goal_due_date = "N/A"

        start_date = date.today().strftime("%m/%d/%Y")
        new_goal_details = {
        "Name": goal_name,  # from input
        "Category": goal_category,  # from input
        "Start_Date": start_date,
        "Est_Hours_To_Completion": goal_length,  # from input (probably convert to int)
        "Hours_Spent": 0,  # default when goal is created
        "Ideal_Completion_Date": goal_due_date,  # from input
        "Est_Completion_Date": "",  # can calculate later, leave blank for now
        "Behind_On Track_Ahead": "On Track",  # start on track
        "Streak": 0,  # default
        "Status": "Active",
        "Completion_%": 0  # default status
        }
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writerow(new_goal_details)
        
        print("Goal Added.")
        return
  


def update_goal():
    editable_fields = [
    "Name",
    "Category",
    "Est_Hours_To_Completion",
    "Hours_Spent",
    "Ideal_Completion_Date",
    "Status"
    ]

    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        goals = list(reader)
        


    while True:  

        for i, goal in enumerate(goals):
            print(f"{i + 1}. {goal['Name']}")

        choice = int(input("Enter the number of the goal you'd like to update: ")) - 1
        if 0 <= choice < len(goals):
            selected_goal = goals[choice]
        else:
            print("Invalid selection.")
            break
    
        while True:

            for i, field in enumerate(editable_fields):
                print(f"{i + 1}. {field}")

            field_choice = int(input("Enter the number of the field you'd like to update: ")) - 1
            field_name = editable_fields[field_choice]
            new_value = input(f"Enter new value for {field_name}: ")
            selected_goal[field_name] = new_value
            if field_name == "Hours_Spent":
                estimated = calculate_estimated_completion(
                    datetime.strptime(selected_goal["Start_Date"], "%m/%d/%Y"),
                    int(selected_goal["Hours_Spent"]),
                    int(selected_goal["Est_Hours_To_Completion"]),
                    selected_goal["Ideal_Completion_Date"]
            )
                selected_goal["Est_Completion_Date"] = estimated

                selected_goal["Behind_On Track_Ahead"] = on_track_tracker(
                    estimated,
                selected_goal["Ideal_Completion_Date"]
                )
                try:
                    hours_spent = int(selected_goal["Hours_Spent"])
                    est_hours = int(selected_goal["Est_Hours_To_Completion"])
                    if est_hours > 0:
                        completion = (hours_spent / est_hours) * 100
                        selected_goal["Completion_%"] = f"{round(completion, 1)}%"
                    else:
                        selected_goal["Completion_%"] = 0
                except ValueError:
                    selected_goal["Completion_%"] = 0
            last_input = int(input("Goal Updated! \n 1. Update different column \n 2. Update New Goal \n 3. Exit"))
        
            with open(CSV_FILE, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(goals)

            if last_input < 1 or last_input > 3:
                print("Invalid selection")
            elif last_input == 1:
                continue
            elif last_input == 2:
                break
            elif last_input == 3:
                return
    
def delete_goal():
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        goals = list(reader)

    if not goals:
        print("There are no goals to delete.")
        return

    while True:  
        for i, goal in enumerate(goals):
            print(f"{i + 1}. {goal['Name']}")
        
        choice = int(input("Enter the number of the goal you'd like to delete: ")) - 1
        if 0 <= choice < len(goals):
            selected_goal = goals[choice]
        else:
            print("Invalid selection.")
            continue
        
        while True:

            confirmation = int(input(f"Are you sure you want to delete the goal: '{selected_goal['Name']}'?\n1. Yes\n2. No"))
            if confirmation < 1 or confirmation > 2 or isinstance(confirmation, str) == True:
                print("Error. Enter 1 or 2")
                continue
            elif confirmation == 2:
                break
            elif confirmation == 1:
                goals.pop(choice)
                with open(CSV_FILE, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(goals)
                print("Goal deleted.")
                return
        

    

        





def main():
    while True:
        print("\nMENU:")
        print("1. Add a new goal")
        print("2. View goals")
        print("3. Update progress")
        print("4. Delete goal")
        print("5. Exit")

        player_input = input("Enter a number to choose an option: ")

        if player_input == "1":
            add_new_goal()
        elif player_input == "3":
            update_goal()
        elif player_input == "4":
            delete_goal()
        elif player_input == "5":
            break
        else:
            print("Invalid option. Please choose 1-5.")

main()
