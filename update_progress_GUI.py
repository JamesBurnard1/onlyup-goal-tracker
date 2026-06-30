import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime, timedelta

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"
EDITABLE_FIELDS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Streak", "Status", "Completion_%", "Last_Update"
]

FULL_HEADERS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Est_Completion_Date",
    "Behind_On Track_Ahead", "Streak", "Status", "Completion_%",
    "Last_Update"
]

def calculate_completion_percentage(hours_spent, est_hours):
    try:
        hours_spent = float(hours_spent)
        est_hours = float(est_hours)
        if est_hours > 0:
            return f"{round((hours_spent / est_hours) * 100, 1)}%"
    except Exception:
        pass
    return "N/A"

def calculate_estimated_completion(start_date_str, hours_spent, est_hours, goal_due_date_str):
    try:
        start_date = datetime.strptime(start_date_str, "%m/%d/%Y")
        due_date = datetime.strptime(goal_due_date_str, "%m/%d/%Y")
        total_days = (due_date - start_date).days
        if total_days <= 0 or est_hours == 0:
            return "N/A"

        ideal_hours_per_day = est_hours / total_days
        days_since_start = (datetime.today() - start_date).days
        actual_hours_per_day = hours_spent / days_since_start if days_since_start > 0 else 0

        hours_remaining = est_hours - hours_spent
        if actual_hours_per_day > 0:
            days_needed = hours_remaining / actual_hours_per_day
            estimated_completion = datetime.today() + timedelta(days=round(days_needed))
            return estimated_completion.strftime("%m/%d/%Y")
    except Exception:
        pass
    return "N/A"

def on_track_tracker(estimated_completion_str, ideal_completion_str):
    try:
        estimated = datetime.strptime(estimated_completion_str, "%m/%d/%Y")
        ideal = datetime.strptime(ideal_completion_str, "%m/%d/%Y")

        if estimated < ideal:
            return "Ahead"
        elif estimated == ideal:
            return "On Track"
        else:
            return "Behind"
    except Exception:
        return "N/A"

def update_progress_gui():
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        goals = [row for row in reader if row['Status'] == 'Active']

    if not goals:
        messagebox.showinfo("No Active Goals", "There are no active goals to update.")
        return

    original_name = tk.StringVar()

    def load_selected_goal(event=None):
        selected_name = goal_combo.get()
        original_name.set(selected_name)
        for goal in goals:
            if goal["Name"] == selected_name:
                for field in EDITABLE_FIELDS:
                    if field in entries:
                        entries[field].delete(0, tk.END)
                        entries[field].insert(0, goal.get(field, ""))
                break

    def save_updates():
        updated_goal = {field: entries[field].get().strip() for field in EDITABLE_FIELDS}

        # Load all goals from CSV
        with open(CSV_FILE, "r", newline="") as f:
            all_goals = list(csv.DictReader(f))

        # Update matching row by name
        for i, row in enumerate(all_goals):
            if row["Name"] == original_name.get():
                for field in EDITABLE_FIELDS:
                    row[field] = updated_goal[field]
                all_goals[i] = row
                break

        # Write changes
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FULL_HEADERS)
            writer.writeheader()
            writer.writerows(all_goals)

        # Now recalculate tracking values using updated data
        for row in all_goals:
            if row["Name"] == updated_goal["Name"]:
                try:
                    est_completion = calculate_estimated_completion(
                        row["Start_Date"],
                        float(row["Hours_Spent"]),
                        float(row["Est_Hours_To_Completion"]),
                        row["Ideal_Completion_Date"]
                    )
                    tracker_status = on_track_tracker(est_completion, row["Ideal_Completion_Date"])
                    completion_pct = calculate_completion_percentage(
                        float(row["Hours_Spent"]),
                        float(row["Est_Hours_To_Completion"])
                    )
                except Exception:
                    est_completion, tracker_status, completion_pct = "N/A", "N/A", "N/A"

                row["Est_Completion_Date"] = est_completion
                row["Behind_On Track_Ahead"] = tracker_status
                row["Completion_%"] = completion_pct
                row["Last_Update"] = datetime.today().strftime("%m/%d/%Y")
                break

        # Write again with tracking updates
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FULL_HEADERS)
            writer.writeheader()
            writer.writerows(all_goals)

        messagebox.showinfo("Success", f"Goal '{updated_goal['Name']}' updated successfully!")
        win.destroy()

    # GUI
    win = tk.Toplevel()
    win.title("Edit Goal")
    win.geometry("550x900")
    win.configure(padx=20, pady=20)

    tk.Label(win, text="Select Goal:").pack(anchor="w")
    goal_names = [g['Name'] for g in goals]
    goal_combo = ttk.Combobox(win, values=goal_names, state="readonly", width=50)
    goal_combo.pack(pady=5)
    goal_combo.bind("<<ComboboxSelected>>", load_selected_goal)

    entries = {}
    for field in EDITABLE_FIELDS:
        tk.Label(win, text=field.replace("_", " ") + ":").pack(anchor="w")
        entry = tk.Entry(win, width=60)
        entry.pack(pady=3)
        entries[field] = entry

    tk.Button(win, text="Save Changes", command=save_updates).pack(pady=20)

if __name__ == "__main__":
    update_progress_gui()
