import os
import json
from datetime import datetime

RECALL_DIR = "recall_notes"

def prompt_for_recall(goal_name, duration):
    print(f"\nACTIVE RECALL - for {goal_name}")
    note = input(f"What did you learn during the last {duration} minutes?\n> ")

    # Make folder if needed
    goal_folder = os.path.join(RECALL_DIR, goal_name)
    os.makedirs(goal_folder, exist_ok=True)

    # Create timestamped file
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M")
    filename = os.path.join(goal_folder, f"{timestamp}.json")

    # Write note
    with open(filename, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "duration_minutes": duration,
            "note": note
        }, f, indent=2)

    print(f"Note saved: {filename}")


def view_recall_notes(goal_name):
    goal_folder = os.path.join(RECALL_DIR, goal_name)
    if not os.path.exists(goal_folder):
        print("No recall notes found for this project.")
        return

    files = sorted(os.listdir(goal_folder))
    if not files:
        print("No notes yet.")
        return

    print(f"\nRECALL NOTES for {goal_name}:")
    for filename in files:
        filepath = os.path.join(goal_folder, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
            print(f"\n{data['timestamp']} ({data['duration_minutes']} min)")
            print(f"{data['note']}")
