import tkinter as tk
from tkinter import messagebox
from add_goal_GUI import open_add_goal_window
from update_progress_GUI import update_progress_gui
from work_session_gui import launch_work_session_gui
from delete_goal_GUI import delete_goal_gui
from view_recall_notes import view_recall_notes_gui
from view_goals_gui import view_goals_gui



# ---- Main Window ----
def main_menu():
    root = tk.Tk()
    root.title("Goal Tracker")
    root.geometry("400x500")
    root.configure(padx=20, pady=20)

    tk.Label(root, text="Only Up", font=("Helvetica", 18, "bold")).pack(pady=10)

    # ---- Button Layout ----
    tk.Button(root, text="Add New Goal", width=25, command = open_add_goal_window).pack(pady=5)
    tk.Button(root, text="View Goals", width=25, command=view_goals_gui).pack(pady=5)
    tk.Button(root, text="Update Progress", width=25, command=update_progress_gui).pack(pady=5)
    tk.Button(root, text="Delete Goal", width=25, command=delete_goal_gui).pack(pady=5)
    tk.Button(root, text="Start Work Session", width=25, command=launch_work_session_gui).pack(pady=5)
    tk.Button(root, text="View Recall Notes", width=25, command=view_recall_notes_gui).pack(pady=5)
    tk.Button(root, text="Exit", width=25, command=root.quit).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main_menu()