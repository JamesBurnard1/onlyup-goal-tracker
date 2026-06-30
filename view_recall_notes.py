import tkinter as tk
from tkinter import ttk, messagebox
import os

RECALL_FOLDER = "/Users/jamesburnard/Desktop/Projects/Personal Tracker/RecallNotes"

def view_recall_notes_gui():
    if not os.path.exists(RECALL_FOLDER):
        messagebox.showerror("Error", "RecallNotes folder not found.")
        return

    # Step 1: Extract project names from files
    filenames = os.listdir(RECALL_FOLDER)
    if not filenames:
        messagebox.showinfo("No Notes", "No recall notes found.")
        return

    project_to_files = {}
    for fname in filenames:
        if fname.endswith(".txt") and "_" in fname:
            project, datepart = fname.rsplit("_", 1)
            if project not in project_to_files:
                project_to_files[project] = []
            project_to_files[project].append(fname)

    def update_entries_dropdown(event=None):
        selected_project = project_combo.get()
        entries = sorted(project_to_files.get(selected_project, []))
        entry_combo["values"] = entries
        entry_combo.set("")  # Reset selection
        text_display.delete("1.0", tk.END)

    def display_selected_note():
        selected_file = entry_combo.get()
        if not selected_file:
            return
        filepath = os.path.join(RECALL_FOLDER, selected_file)
        with open(filepath, "r") as f:
            content = f.read()
        text_display.delete("1.0", tk.END)
        text_display.insert(tk.END, content)
        text_display.tag_configure("note", font=("Times New Roman", 12), spacing3=6)
        text_display.tag_add("note", "1.0", tk.END)

    # GUI
    win = tk.Toplevel()
    win.title("View Recall Notes")
    win.geometry("700x600")
    win.configure(padx=20, pady=20)

    tk.Label(win, text="Select Project:", font=("Arial", 12)).pack(anchor="w")
    project_combo = ttk.Combobox(win, values=sorted(project_to_files.keys()), state="readonly", width=50)
    project_combo.pack(pady=5)
    project_combo.bind("<<ComboboxSelected>>", update_entries_dropdown)

    tk.Label(win, text="Select Recall Entry:", font=("Arial", 12)).pack(anchor="w")
    entry_combo = ttk.Combobox(win, state="readonly", width=50)
    entry_combo.pack(pady=5)

    tk.Button(win, text="View Notes", command=display_selected_note).pack(pady=10)

    text_display = tk.Text(win, wrap="word", font=("Times New Roman", 12), spacing3=6)
    text_display.pack(fill="both", expand=True, pady=10)

if __name__ == "__main__":
    view_recall_notes_gui()
