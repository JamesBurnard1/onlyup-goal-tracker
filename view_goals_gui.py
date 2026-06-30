import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"
HEADERS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Est_Completion_Date",
    "Behind_On Track_Ahead", "Streak", "Status", "Completion_%", "Last_Update"
]

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y %H:%M")
    except ValueError:
        return datetime.strptime(date_str, "%m/%d/%Y")

def view_goals_gui():
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        all_goals = []
        for row in reader:
            # Normalize Status
            row["Status"] = row["Status"].strip().lower()
            all_goals.append(row)

    active_goals = [g for g in all_goals if g["Status"] == "active"]
    completed_goals = [g for g in all_goals if g["Status"] in ("completed", "complete")]

    print("Statuses:", [g["Status"] for g in all_goals])
    print("Completed goals:", [g["Name"] for g in completed_goals])

    def open_dashboard(goal):
        dash = tk.Toplevel()
        dash.title(f"\U0001F4CA Dashboard - {goal['Name']}")
        dash.geometry("900x750")
        dash.configure(padx=30, pady=30, bg="#1e1e2f")

        tk.Label(dash, text=goal["Name"], font=("Helvetica", 28, "bold"), bg="#1e1e2f", fg="white").pack(pady=(10, 20))
        summary = f"{goal['Category']} | {goal['Status'].capitalize()} | {goal['Behind_On Track_Ahead']}"
        tk.Label(dash, text=summary, font=("Helvetica", 12), bg="#1e1e2f", fg="lightgrey").pack(pady=(0, 15))

        main_frame = tk.Frame(dash, bg="#1e1e2f")
        main_frame.pack(fill="both", expand=True)

        dial_frame = tk.Frame(main_frame, bg="#1e1e2f")
        dial_frame.pack(pady=10)
        canvas = tk.Canvas(dial_frame, width=250, height=250, bg="#1e1e2f", highlightthickness=0)
        canvas.pack()
        try:
            percent = float(goal.get("Completion_%", "0").replace("%", ""))
        except:
            percent = 0.0
        canvas.create_oval(30, 30, 220, 220, outline="#444", width=20)
        extent = (percent / 100) * 360
        canvas.create_arc(30, 30, 220, 220, start=90, extent=-extent, outline="#00e676", style="arc", width=20)
        canvas.create_text(125, 125, text=f"{percent:.1f}%", font=("Helvetica", 18, "bold"), fill="white")

        progress_frame = tk.Frame(main_frame, bg="#1e1e2f")
        progress_frame.pack(pady=25)

        def add_progress(label, value, max_val, row, extra_label=None):
            tk.Label(progress_frame, text=label, font=("Helvetica", 10), bg="#1e1e2f", fg="white").grid(row=row, column=0, sticky="w", padx=5, pady=3)
            bar = ttk.Progressbar(progress_frame, length=300, maximum=max_val)
            bar.grid(row=row, column=1, padx=10, pady=3)
            bar['value'] = value
            extra_text = f"{value}/{max_val}" if extra_label is None else extra_label
            tk.Label(progress_frame, text=extra_text, font=("Helvetica", 10), bg="#1e1e2f", fg="lightgrey").grid(row=row, column=2, sticky="w")

        try:
            est_hours = float(goal["Est_Hours_To_Completion"])
            hours_spent = float(goal["Hours_Spent"])
        except:
            est_hours = hours_spent = 0

        try:
            ideal_date = parse_date(goal["Ideal_Completion_Date"])
            start_date = parse_date(goal["Start_Date"])
            total_days = max((ideal_date - start_date).days, 1)
            remaining_time = ideal_date - datetime.now()
            remaining_seconds = max(remaining_time.total_seconds(), 0)
            remaining_days = int(remaining_seconds // (24 * 3600))
            hours = int((remaining_seconds % (24 * 3600)) // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            time_label = f"{remaining_days}d {hours}h {minutes}m"
        except:
            total_days = remaining_days = hours = minutes = 0
            time_label = "N/A"

        add_progress("Hours Spent", hours_spent, est_hours, 0)

        if time_label != "N/A":
            add_progress("Time Remaining", remaining_days, total_days, 1, extra_label=time_label)
        else:
            add_progress("Time Remaining", 0, 1, 1, extra_label="N/A")

        try:
            streak = int(goal["Streak"])
        except:
            streak = 0

        streak_frame = tk.Frame(main_frame, bg="#1e1e2f")
        streak_frame.pack(pady=20)
        tk.Label(streak_frame, text=f" {streak} Day Streak! ", font=("Helvetica", 20, "bold"), bg="#1e1e2f", fg="#ff9800").pack()

        info_frame = tk.Frame(main_frame, bg="#1e1e2f")
        info_frame.pack(pady=20)

        def add_info(label, value, row):
            tk.Label(info_frame, text=label + ":", font=("Helvetica", 10, "bold"), bg="#1e1e2f", fg="white", anchor="w", width=25).grid(row=row, column=0, sticky="w", pady=3)
            tk.Label(info_frame, text=value, font=("Helvetica", 10), bg="#1e1e2f", fg="lightgrey", anchor="w").grid(row=row, column=1, sticky="w", pady=3)

        rows = [
            ("Start Date", goal.get("Start_Date", "")),
            ("Ideal Completion Date", goal.get("Ideal_Completion_Date", "")),
            ("Estimated Completion Date", goal.get("Est_Completion_Date", "")),
            ("Status", goal.get("Status", "")),
            ("On Track?", goal.get("Behind_On Track_Ahead", "")),
            ("Last Update", goal.get("Last_Update", "")),
        ]

        for idx, (label, val) in enumerate(rows):
            add_info(label, val, idx)

    def populate_listbox(listbox, goals_list):
        listbox.delete(0, tk.END)
        for goal in goals_list:
            listbox.insert(tk.END, goal["Name"])

    def on_project_select(listbox, goal_list):
        selection = listbox.curselection()
        if not selection:
            return
        goal_name = listbox.get(selection[0])
        for goal in goal_list:
            if goal["Name"] == goal_name:
                open_dashboard(goal)
                break

    win = tk.Toplevel()
    win.title("\U0001F4D6 View Goals")
    win.geometry("500x500")
    win.configure(padx=20, pady=20)

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True)

    active_frame = ttk.Frame(notebook)
    notebook.add(active_frame, text="Active")
    tk.Label(active_frame, text="Your Active Goals:", font=("Helvetica", 12)).pack(pady=5)
    active_listbox = tk.Listbox(active_frame, width=50)
    active_listbox.pack(pady=5, fill="both", expand=True)
    populate_listbox(active_listbox, active_goals)
    active_listbox.bind("<<ListboxSelect>>", lambda e: on_project_select(active_listbox, active_goals))

    completed_frame = ttk.Frame(notebook)
    notebook.add(completed_frame, text="Completed")
    tk.Label(completed_frame, text="Your Completed Goals:", font=("Helvetica", 12)).pack(pady=5)
    completed_listbox = tk.Listbox(completed_frame, width=50)
    completed_listbox.pack(pady=5, fill="both", expand=True)
    populate_listbox(completed_listbox, completed_goals)
    completed_listbox.bind("<<ListboxSelect>>", lambda e: on_project_select(completed_listbox, completed_goals))

if __name__ == "__main__":
    view_goals_gui()
