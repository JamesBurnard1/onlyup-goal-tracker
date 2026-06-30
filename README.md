# Only Up Goal Tracker

Only Up is a personal goal-tracking app built in Python. The main desktop app uses Tkinter, stores goal progress in CSV files, and keeps recall notes as text files.

## Project Layout

- `main_menu_gui.py` - Tkinter entry point for the desktop app.
- `goaltracker.py` - command-line goal tracker flow.
- `*_GUI.py` - desktop windows for adding, viewing, updating, deleting, and working on goals.
- `goal_utils.py` - shared progress and date calculation helpers.
- `GoalsData.csv` - local goal data.
- `RecallNotes/` and `recall_notes/` - saved recall note data.
- `web_demo/` - browser demo version with sample data.
- `*.spec`, `setup.py`, and icon files - packaging resources.

## Run The Desktop App

```bash
python3 main_menu_gui.py
```

## Run The Web Demo

```bash
python3 web_demo/app.py
```

Then open:

```text
http://127.0.0.1:8000
```

The web demo uses sample files in `web_demo/sample_data` and keeps visitor edits in a temporary browser session.

