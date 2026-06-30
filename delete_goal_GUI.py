import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os

CSV_FILE = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/GoalsData.csv"
HEADERS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Est_Completion_Date",
    "Behind_On Track_Ahead", "Streak", "Status", "Completion_%", "Last_Update"
]

def delete_goal_gui():
    if not os.path.exists(CSV_FILE):
        messagebox.showerror("Error", "GoalsData.csv not found.")
        return

    # Load goals from CSV
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        goals = [row for row in reader]

    if not goals:
        messagebox.showinfo("No Goals", "There are no goals to delete.")
        return

    def perform_deletion():
        selected_name = goal_combo.get()
        if not selected_name:
            messagebox.showwarning("Select Goal", "Please select a goal to delete.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{selected_name}'?")
        if not confirm:
            return

        updated_goals = [row for row in goals if row["Name"] != selected_name]

        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(updated_goals)

        messagebox.showinfo("Deleted", f"Goal '{selected_name}' has been deleted.")
        win.destroy()

    win = tk.Toplevel()
    win.title("Delete Goal")
    win.geometry("400x200")
    win.configure(padx=20, pady=20)

    tk.Label(win, text="Select Goal to Delete:").pack(anchor="w")
    goal_names = [row["Name"] for row in goals]
    goal_combo = ttk.Combobox(win, values=goal_names, state="readonly", width=40)
    goal_combo.pack(pady=5)

    tk.Button(win, text="Delete Goal", command=perform_deletion).pack(pady=20)

if __name__ == "__main__":
    delete_goal_gui()
