import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import date, datetime, timedelta

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"

HEADERS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Est_Completion_Date",
    "Behind_On Track_Ahead", "Streak", "Status", "Completion_%"
]

def calculate_completion_percentage(hours_spent, est_hours):
    if est_hours > 0:
        return round((hours_spent / est_hours) * 100, 1)
    return 0

def calculate_estimated_completion(start_date_str, hours_spent, est_hours, goal_due_date_str):
    try:
        start_date = parse_date(start_date_str)
        due_date = parse_date(goal_due_date_str)
    except Exception:
        return "N/A"

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
    else:
        return "N/A"

def on_track_tracker(estimated_completion_str, ideal_completion_str):
    try:
        estimated = parse_date(estimated_completion_str)
        ideal = parse_date(ideal_completion_str)

        if estimated < ideal:
            return "Ahead"
        elif estimated == ideal:
            return "On Track"
        else:
            return "Behind"
    except Exception:
        return "N/A"

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y %H:%M")
    except ValueError:
        return datetime.strptime(date_str, "%m/%d/%Y")

def open_add_goal_window():
    win = tk.Toplevel()
    win.title("Add New Goal")
    win.geometry("400x400")
    win.configure(padx=20, pady=20)

    # --- Goal Name ---
    tk.Label(win, text="Goal Name:").pack(anchor="w")
    name_entry = tk.Entry(win, width=30)
    name_entry.pack(pady=5)

    # --- Category ---
    tk.Label(win, text="Category:").pack(anchor="w")
    category_combo = ttk.Combobox(win, values=["Learning", "Project", "Health & Fitness", "Academic"], state="readonly")
    category_combo.pack(pady=5)

    # --- Estimated Hours ---
    tk.Label(win, text="Estimated Hours:").pack(anchor="w")
    hours_entry = tk.Entry(win, width=10)
    hours_entry.pack(pady=5)

    # --- Due Date ---
    tk.Label(win, text="Due Date (MM/DD/YYYY):").pack(anchor="w")
    due_entry = tk.Entry(win, width=15)
    due_entry.pack(pady=5)

    # --- Due Time (Optional) ---
    tk.Label(win, text="Due Time (HH:MM 24hr, optional):").pack(anchor="w")
    time_entry = tk.Entry(win, width=10)
    time_entry.pack(pady=5)

    def submit_goal():
        name = name_entry.get().strip()
        category = category_combo.get().strip()
        est_hours = hours_entry.get().strip()
        due = due_entry.get().strip()
        time_input = time_entry.get().strip()

        if not name or not category or not est_hours:
            messagebox.showerror("Missing Info", "Please fill out all required fields.")
            return

        try:
            est_hours = int(est_hours)
        except ValueError:
            messagebox.showerror("Invalid Hours", "Estimated hours must be a number.")
            return

        # Parse due date + optional time
        if due:
            try:
                if time_input:
                    due_datetime = datetime.strptime(f"{due} {time_input}", "%m/%d/%Y %H:%M")
                else:
                    due_datetime = datetime.strptime(due, "%m/%d/%Y") + timedelta(hours=23, minutes=59)
                due_date_str = due_datetime.strftime("%m/%d/%Y %H:%M")
            except ValueError:
                messagebox.showerror("Invalid Date/Time", "Enter date as MM/DD/YYYY and optional time as HH:MM (24hr).")
                return
        else:
            due_date_str = "N/A"

        start_date = date.today().strftime("%m/%d/%Y")
        hours_spent = 0

        est_completion = calculate_estimated_completion(start_date, hours_spent, est_hours, due_date_str)
        status = on_track_tracker(est_completion, due_date_str)
        completion_pct = calculate_completion_percentage(hours_spent, est_hours)

        new_goal = {
            "Name": name,
            "Category": category,
            "Start_Date": start_date,
            "Est_Hours_To_Completion": est_hours,
            "Hours_Spent": hours_spent,
            "Ideal_Completion_Date": due_date_str,
            "Est_Completion_Date": est_completion,
            "Behind_On Track_Ahead": status,
            "Streak": 0,
            "Status": "Active",
            "Completion_%": completion_pct
        }

        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writerow(new_goal)

        messagebox.showinfo("Goal Added", f"Goal '{name}' added successfully!")
        win.destroy()

    tk.Button(win, text="Submit", command=submit_goal).pack(pady=20)

if __name__ == "__main__":
    open_add_goal_window()
