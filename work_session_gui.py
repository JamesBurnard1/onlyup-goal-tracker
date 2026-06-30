import tkinter as tk
from tkinter import messagebox
import csv
import time
import threading
from datetime import datetime
import os
import platform
import subprocess

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"
RECALL_FOLDER = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/RecallNotes"

if not os.path.exists(RECALL_FOLDER):
    os.makedirs(RECALL_FOLDER)

def play_sound():
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])
    elif system == "Windows":
        import winsound
        winsound.MessageBeep()
    else:
        print("\a")

def get_active_goals():
    active_goals = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Status"] == "Active":
                active_goals.append(row)
    return active_goals

def save_recall_notes(goal_name, notes):
    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"{goal_name}_{today}.txt"
    filepath = os.path.join(RECALL_FOLDER, filename)
    with open(filepath, "a") as f:
        f.write(notes.strip() + "\n\n")

def add_time_to_goal(goal_name, minutes_worked):
    updated_rows = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] == goal_name:
                current_hours = float(row["Hours_Spent"])
                updated_hours = current_hours + (minutes_worked / 60)
                row["Hours_Spent"] = round(updated_hours, 4)

                try:
                    est_hours = float(row["Est_Hours_To_Completion"])
                    if est_hours > 0:
                        completion = round((updated_hours / est_hours) * 100, 1)
                    else:
                        completion = 0.0
                except:
                    completion = 0.0

                row["Completion_%"] = completion
            updated_rows.append(row)

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=updated_rows[0].keys())
        writer.writeheader()
        writer.writerows(updated_rows)

def launch_work_session_gui():
    goals = get_active_goals()
    if not goals:
        messagebox.showinfo("No Active Goals", "You have no active goals to work on.")
        return

    selector = tk.Tk()
    selector.title("Select Goal")
    selector.geometry("400x300")

    tk.Label(selector, text="Select the goal you're working on:", font=("Arial", 12)).pack(pady=10)

    listbox = tk.Listbox(selector, width=50)
    for goal in goals:
        listbox.insert(tk.END, goal["Name"])
    listbox.pack(pady=10)

    def start_session():
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a goal.")
            return
        goal_name = listbox.get(selected[0])
        selector.destroy()
        open_timer_window(goal_name)

    tk.Button(selector, text="Start Work Session", command=start_session).pack(pady=10)
    selector.mainloop()

def open_timer_window(goal_name):
    root = tk.Tk()
    root.title(f"Work Session - {goal_name}")
    root.geometry("300x250")

    minutes = tk.IntVar(value=25)
    remaining = tk.IntVar(value=minutes.get() * 60)
    running = tk.BooleanVar(value=False)

    timer_label = tk.Label(root, text="", font=("Helvetica", 32))
    timer_label.pack(pady=20)

    def update_display():
        mins, secs = divmod(remaining.get(), 60)
        timer_label.config(text=f"{mins:02d}:{secs:02d}")
        root.update_idletasks()

    def countdown():
        nonlocal initial_duration
        initial_duration = remaining.get()  # capture actual timer start time
        while remaining.get() > 0 and running.get():
            time.sleep(1)
            remaining.set(remaining.get() - 1)
            update_display()

        if remaining.get() == 0:
            play_sound()
            running.set(False)
            minutes_worked = round((initial_duration - remaining.get()) / 60, 4)
            show_recall_popup(goal_name, minutes_worked)

    def toggle():
        if not running.get():
            running.set(True)
            threading.Thread(target=countdown, daemon=True).start()
        else:
            running.set(False)

    def add_min():
        remaining.set(remaining.get() + 60)
        update_display()

    def subtract_min():
        if remaining.get() > 60:
            remaining.set(remaining.get() - 60)
            update_display()

    def reset():
        running.set(False)
        remaining.set(minutes.get() * 60)
        update_display()

    def show_recall_popup(goal_name, minutes_worked):
        popup = tk.Toplevel()
        popup.title("Active Recall")
        popup.geometry("400x300")

        tk.Label(popup, text="Write what you recall from this session:").pack(pady=10)
        text_area = tk.Text(popup, wrap="word", height=10, width=40)
        text_area.pack(padx=10)

        def submit_notes():
            notes = text_area.get("1.0", tk.END).strip()
            if notes:
                save_recall_notes(goal_name, notes)
            add_time_to_goal(goal_name, minutes_worked)
            popup.destroy()

        def skip_notes():
            add_time_to_goal(goal_name, minutes_worked)
            popup.destroy()

        tk.Button(popup, text="Submit", command=submit_notes).pack(side="left", padx=30, pady=10)
        tk.Button(popup, text="Skip", command=skip_notes).pack(side="right", padx=30, pady=10)

    initial_duration = 0  # initialized outside countdown
    update_display()

    tk.Button(root, text="Start / Pause", command=toggle).pack(pady=5)
    tk.Button(root, text="Add 1 Min", command=add_min).pack(pady=5)
    tk.Button(root, text="Subtract 1 Min", command=subtract_min).pack(pady=5)
    tk.Button(root, text="Reset Timer", command=reset).pack(pady=5)
    tk.Button(root, text="End Session", command=root.destroy).pack(pady=10)

    root.mainloop()
