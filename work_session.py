import tkinter as tk
from tkinter import messagebox
import csv
import os
from datetime import datetime

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"

def open_work_session_gui():
    # Load active goals
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        goals = [row["Name"] for row in reader if row["Status"] != "Completed"]

    if not goals:
        messagebox.showinfo("No Active Goals", "You don't have any active goals.")
        return

    # Selection window
    selector = tk.Toplevel()
    selector.title("Select Goal")
    selector.geometry("300x200")
    tk.Label(selector, text="Which goal are you working on?", pady=10).pack()

    listbox = tk.Listbox(selector)
    for goal in goals:
        listbox.insert(tk.END, goal)
    listbox.pack(pady=5)

    def confirm_selection():
        selected_index = listbox.curselection()
        if not selected_index:
            messagebox.showwarning("No Selection", "Please select a goal.")
            return
        goal_name = goals[selected_index[0]]
        selector.destroy()
        start_timer_window(goal_name)

    tk.Button(selector, text="Start Session", command=confirm_selection).pack(pady=10)

def start_timer_window(goal_name):
    win = tk.Toplevel()
    win.title(f"Work Session - {goal_name}")
    win.geometry("300x250")

    minutes = tk.IntVar(value=25)
    running = tk.BooleanVar(value=False)

    timer_label = tk.Label(win, text="25:00", font=("Helvetica", 32))
    timer_label.pack(pady=20)

    def update_timer():
        if running.get():
            mins = minutes.get()
            if mins > 0:
                minutes.set(mins - 1)
                timer_label.config(text=f"{mins-1:02d}:00")
                win.after(60000, update_timer)  # 1-minute countdown
            else:
                timer_label.config(text="00:00")
                ring_bell()
                win.after(500, lambda: end_session(goal_name, original_minutes.get()))
                return

    original_minutes = tk.IntVar(value=25)

    def start():
        if not running.get():
            running.set(True)
            original_minutes.set(minutes.get())
            update_timer()

    def pause():
        running.set(False)

    def add_min():
        minutes.set(minutes.get() + 1)
        timer_label.config(text=f"{minutes.get():02d}:00")

    def sub_min():
        if minutes.get() > 1:
            minutes.set(minutes.get() - 1)
            timer_label.config(text=f"{minutes.get():02d}:00")

    # Controls
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Start", command=start).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Pause", command=pause).grid(row=0, column=1, padx=5)

    tk.Button(btn_frame, text="+1 min", command=add_min).grid(row=1, column=0, padx=5, pady=5)
    tk.Button(btn_frame, text="-1 min", command=sub_min).grid(row=1, column=1, padx=5, pady=5)

def ring_bell():
    try:
        import winsound
        winsound.Beep(1000, 500)
    except ImportError:
        print("\a")  # macOS/Linux bell

def end_session(goal_name, minutes):
    root = tk.Toplevel()
    root.title("Active Recall")
    root.geometry("400x250")

    def skip():
        root.destroy()
        log_session_time(goal_name, minutes)

    def submit_notes():
        notes = notes_box.get("1.0", tk.END).strip()
        if notes:
            save_recall_notes(goal_name, notes)
        root.destroy()
        log_session_time(goal_name, minutes)

    tk.Label(root, text="Would you like to add Active Recall notes?").pack(pady=10)
    notes_box = tk.Text(root, height=6, width=45)
    notes_box.pack(pady=5)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    tk.Button(button_frame, text="Skip", command=skip).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="Submit", command=submit_notes).grid(row=0, column=1, padx=10)

def log_session_time(goal_name, minutes):
    updated = False
    new_rows = []

    with open(CSV_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] == goal_name:
                try:
                    old_hours = float(row["Hours_Spent"])
                except ValueError:
                    old_hours = 0.0
                row["Hours_Spent"] = str(round(old_hours + minutes / 60, 2))
                updated = True
            new_rows.append(row)

    if updated:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=new_rows[0].keys())
            writer.writeheader()
            writer.writerows(new_rows)

def save_recall_notes(goal_name, notes):
    today = datetime.today().strftime("%m-%d-%Y")
    folder = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/RecallNotes"
    os.makedirs(folder, exist_ok=True)
    filename = f"{folder}/{goal_name}__{today}.txt"

    with open(filename, "w") as f:
        f.write(notes)
