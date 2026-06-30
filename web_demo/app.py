from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
import csv
import html
import json
import mimetypes
import os
import secrets
import threading
from datetime import date, datetime, timedelta


DEMO_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = DEMO_DIR / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "GoalsData.csv"
RECALL_FOLDER = SAMPLE_DATA_DIR / "RecallNotes"
STATIC_DIR = DEMO_DIR / "static"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))

HEADERS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Est_Completion_Date", "Behind_On Track_Ahead",
    "Streak", "Status", "Completion_%", "Last_Update",
]

CATEGORIES = ["Learning", "Project", "Health & Fitness", "Academic"]
EDITABLE_FIELDS = [
    "Name", "Category", "Start_Date", "Est_Hours_To_Completion", "Hours_Spent",
    "Ideal_Completion_Date", "Streak", "Status", "Completion_%", "Last_Update",
]

SESSIONS = {}
LOCK = threading.Lock()


def esc(value):
    return html.escape(str(value or ""), quote=True)


def read_template_goals():
    if not CSV_FILE.exists():
        return []
    with CSV_FILE.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return [normalize_goal(row) for row in rows]


def read_template_notes():
    notes = {}
    if not RECALL_FOLDER.exists():
        return notes
    for path in sorted(RECALL_FOLDER.glob("*.txt")):
        if "_" not in path.name:
            continue
        project, _date_part = path.name.rsplit("_", 1)
        notes.setdefault(project, []).append({
            "filename": path.name,
            "content": path.read_text(errors="replace"),
        })
    return notes


def normalize_goal(row):
    goal = {header: row.get(header, "") for header in HEADERS}
    if not goal["Last_Update"]:
        goal["Last_Update"] = row.get("Last_Update", "")
    return goal


def new_session_state():
    return {
        "goals": read_template_goals(),
        "notes": read_template_notes(),
        "flash": "",
    }


def parse_date(value):
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except (TypeError, ValueError):
            pass
    raise ValueError("Invalid date")


def calculate_completion_percentage(hours_spent, est_hours):
    try:
        hours_spent = float(hours_spent)
        est_hours = float(est_hours)
    except (TypeError, ValueError):
        return "N/A"
    if est_hours > 0:
        return f"{round((hours_spent / est_hours) * 100, 1)}%"
    return "N/A"


def calculate_estimated_completion(start_date_str, hours_spent, est_hours, goal_due_date_str):
    try:
        start_date = parse_date(start_date_str)
        due_date = parse_date(goal_due_date_str)
        hours_spent = float(hours_spent)
        est_hours = float(est_hours)
    except (TypeError, ValueError):
        return "N/A"

    total_days = (due_date - start_date).days
    if total_days <= 0 or est_hours == 0:
        return "N/A"

    days_since_start = (datetime.today() - start_date).days
    actual_hours_per_day = hours_spent / days_since_start if days_since_start > 0 else 0
    hours_remaining = est_hours - hours_spent
    if actual_hours_per_day > 0:
        days_needed = hours_remaining / actual_hours_per_day
        estimated_completion = datetime.today() + timedelta(days=round(days_needed))
        return estimated_completion.strftime("%m/%d/%Y")
    return "N/A"


def on_track_tracker(estimated_completion_str, ideal_completion_str):
    try:
        estimated = parse_date(estimated_completion_str)
        ideal = parse_date(ideal_completion_str)
    except ValueError:
        return "N/A"
    if estimated < ideal:
        return "Ahead"
    if estimated == ideal:
        return "On Track"
    return "Behind"


def flash(state, message):
    state["flash"] = message


def page(title, body, wide=False, dark=False, script=""):
    classes = ["page"]
    if wide:
        classes.append("wide-page")
    if dark:
        classes.append("dark-page")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body class="{' '.join(classes)}">
  {body}
  {script}
</body>
</html>"""


def flash_html(state):
    message = state.pop("flash", "")
    if not message:
        return ""
    return f'<div class="message">{esc(message)}</div>'


def window(title, content, width="400px", extra_class=""):
    return f"""
<main class="tk-window {extra_class}" style="max-width: {width}">
  {content}
</main>
"""


def button_link(label, href, danger=False):
    cls = "tk-button danger" if danger else "tk-button"
    return f'<a class="{cls}" href="{href}">{esc(label)}</a>'


def option_tags(options, selected=""):
    return "".join(
        f'<option value="{esc(option)}" {"selected" if str(option) == str(selected) else ""}>{esc(option)}</option>'
        for option in options
    )


def progress_row(label, value, maximum, extra_label=None):
    try:
        value_num = float(value)
        max_num = float(maximum)
    except (TypeError, ValueError):
        value_num = 0
        max_num = 1
    percent = 0 if max_num <= 0 else min(max((value_num / max_num) * 100, 0), 100)
    text = extra_label if extra_label is not None else f"{value}/{maximum}"
    return f"""
<div class="progress-row">
  <span>{esc(label)}</span>
  <div class="progress-track"><div class="progress-fill" style="width: {percent}%"></div></div>
  <span class="muted">{esc(text)}</span>
</div>
"""


class DemoHandler(BaseHTTPRequestHandler):
    def get_state(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie"))
        sid = jar.get("only_up_demo")
        sid_value = sid.value if sid else ""
        with LOCK:
            if not sid_value or sid_value not in SESSIONS:
                sid_value = secrets.token_urlsafe(24)
                SESSIONS[sid_value] = new_session_state()
                self.new_sid = sid_value
            return SESSIONS[sid_value]

    def send_html(self, body, status=200):
        data = body.encode("utf-8")
        self.send_response(status)
        if getattr(self, "new_sid", None):
            cookie = cookies.SimpleCookie()
            cookie["only_up_demo"] = self.new_sid
            cookie["only_up_demo"]["path"] = "/"
            self.send_header("Set-Cookie", cookie.output(header="").strip())
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, path):
        self.send_response(303)
        if getattr(self, "new_sid", None):
            cookie = cookies.SimpleCookie()
            cookie["only_up_demo"] = self.new_sid
            cookie["only_up_demo"]["path"] = "/"
            self.send_header("Set-Cookie", cookie.output(header="").strip())
        self.send_header("Location", path)
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return {key: values[-1] for key, values in parse_qs(raw).items()}

    def do_GET(self):
        self.new_sid = None
        state = self.get_state()
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path.startswith("/static/"):
            return self.serve_static(path)
        routes = {
            "/": self.home,
            "/add": self.add_goal,
            "/goals": self.view_goals,
            "/dashboard": lambda s: self.dashboard(s, query.get("name", [""])[0]),
            "/update": self.update_goal,
            "/delete": self.delete_goal,
            "/work": self.work_session,
            "/timer": lambda s: self.timer(s, query.get("name", [""])[0]),
            "/recall": self.view_recall,
        }
        handler = routes.get(path)
        if handler:
            return self.send_html(handler(state))
        self.send_html(page("Not Found", window("Not Found", "<h1>Not Found</h1>")), status=404)

    def do_POST(self):
        self.new_sid = None
        state = self.get_state()
        path = urlparse(self.path).path
        form = self.read_form()
        if path == "/reset":
            with LOCK:
                state.clear()
                state.update(new_session_state())
            flash(state, "Demo data reset.")
            return self.redirect("/")
        if path == "/add":
            return self.create_goal(state, form)
        if path == "/update":
            return self.save_goal(state, form)
        if path == "/delete":
            return self.perform_delete(state, form)
        if path == "/session-complete":
            return self.complete_session(state, form)
        self.redirect("/")

    def serve_static(self, path):
        rel = path.replace("/static/", "", 1)
        file_path = (STATIC_DIR / rel).resolve()
        if not str(file_path).startswith(str(STATIC_DIR.resolve())) or not file_path.exists():
            self.send_error(404)
            return
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def home(self, state):
        content = f"""
  <h1>Only Up</h1>
  {flash_html(state)}
  <nav class="menu-buttons">
    {button_link("Add New Goal", "/add")}
    {button_link("View Goals", "/goals")}
    {button_link("Update Progress", "/update")}
    {button_link("Delete Goal", "/delete")}
    {button_link("Start Work Session", "/work")}
    {button_link("View Recall Notes", "/recall")}
    <form method="post" action="/reset">{'<button class="tk-button" type="submit">Reset Demo Data</button>'}</form>
  </nav>
"""
        return page("Goal Tracker", window("Goal Tracker", content, "400px"))

    def add_goal(self, state):
        content = f"""
  <h2>Add New Goal</h2>
  {flash_html(state)}
  <form class="stack-form" method="post" action="/add">
    <label>Goal Name:<input name="name" required></label>
    <label>Category:<select name="category" required><option value=""></option>{option_tags(CATEGORIES)}</select></label>
    <label>Estimated Hours:<input name="est_hours" type="number" min="0" step="1" required></label>
    <label>Due Date (MM/DD/YYYY):<input name="due" placeholder="11/12/2025"></label>
    <label>Due Time (HH:MM 24hr, optional):<input name="time" placeholder="23:59"></label>
    <button class="tk-button" type="submit">Submit</button>
  </form>
  {button_link("Back", "/")}
"""
        return page("Add New Goal", window("Add New Goal", content, "400px"))

    def create_goal(self, state, form):
        name = form.get("name", "").strip()
        category = form.get("category", "").strip()
        est_hours = form.get("est_hours", "").strip()
        due = form.get("due", "").strip()
        time_input = form.get("time", "").strip()
        if not name or not category or not est_hours:
            flash(state, "Missing Info: Please fill out all required fields.")
            return self.redirect("/add")
        try:
            est_hours_num = int(est_hours)
        except ValueError:
            flash(state, "Invalid Hours: Estimated hours must be a number.")
            return self.redirect("/add")
        if due:
            try:
                if time_input:
                    due_datetime = datetime.strptime(f"{due} {time_input}", "%m/%d/%Y %H:%M")
                else:
                    due_datetime = datetime.strptime(due, "%m/%d/%Y") + timedelta(hours=23, minutes=59)
                due_date_str = due_datetime.strftime("%m/%d/%Y %H:%M")
            except ValueError:
                flash(state, "Invalid Date/Time: Enter date as MM/DD/YYYY and optional time as HH:MM.")
                return self.redirect("/add")
        else:
            due_date_str = "N/A"
        start_date = date.today().strftime("%m/%d/%Y")
        est_completion = calculate_estimated_completion(start_date, 0, est_hours_num, due_date_str)
        tracker_status = on_track_tracker(est_completion, due_date_str)
        state["goals"].append({
            "Name": name,
            "Category": category,
            "Start_Date": start_date,
            "Est_Hours_To_Completion": str(est_hours_num),
            "Hours_Spent": "0",
            "Ideal_Completion_Date": due_date_str,
            "Est_Completion_Date": est_completion,
            "Behind_On Track_Ahead": tracker_status,
            "Streak": "0",
            "Status": "Active",
            "Completion_%": "0",
            "Last_Update": "",
        })
        flash(state, f"Goal '{name}' added successfully!")
        return self.redirect("/")

    def view_goals(self, state):
        active = [g for g in state["goals"] if g["Status"].strip().lower() == "active"]
        completed = [g for g in state["goals"] if g["Status"].strip().lower() in ("completed", "complete")]
        def listbox(goals):
            items = "".join(f'<a class="list-item" href="/dashboard?{urlencode({"name": g["Name"]})}">{esc(g["Name"])}</a>' for g in goals)
            return items or '<div class="empty-row">No goals found.</div>'
        content = f"""
  <h2>View Goals</h2>
  {flash_html(state)}
  <div class="tabs">
    <input checked id="active-tab" name="tabs" type="radio">
    <label for="active-tab">Active</label>
    <input id="completed-tab" name="tabs" type="radio">
    <label for="completed-tab">Completed</label>
    <section class="tab active-panel">
      <p class="section-label">Your Active Goals:</p>
      <div class="listbox">{listbox(active)}</div>
    </section>
    <section class="tab completed-panel">
      <p class="section-label">Your Completed Goals:</p>
      <div class="listbox">{listbox(completed)}</div>
    </section>
  </div>
  {button_link("Back", "/")}
"""
        return page("View Goals", window("View Goals", content, "500px"))

    def find_goal(self, state, name):
        for goal in state["goals"]:
            if goal["Name"] == name:
                return goal
        return None

    def dashboard(self, state, name):
        goal = self.find_goal(state, name)
        if not goal:
            flash(state, "Goal not found.")
            return self.view_goals(state)
        try:
            percent = float(str(goal.get("Completion_%", "0")).replace("%", ""))
        except ValueError:
            percent = 0
        try:
            est_hours = float(goal["Est_Hours_To_Completion"])
            hours_spent = float(goal["Hours_Spent"])
        except ValueError:
            est_hours = hours_spent = 0
        try:
            ideal_date = parse_date(goal["Ideal_Completion_Date"])
            start_date = parse_date(goal["Start_Date"])
            total_days = max((ideal_date - start_date).days, 1)
            remaining = max((ideal_date - datetime.now()).total_seconds(), 0)
            remaining_days = int(remaining // (24 * 3600))
            hours = int((remaining % (24 * 3600)) // 3600)
            minutes = int((remaining % 3600) // 60)
            time_label = f"{remaining_days}d {hours}h {minutes}m"
        except ValueError:
            total_days = remaining_days = 0
            time_label = "N/A"
        try:
            streak = int(goal["Streak"])
        except ValueError:
            streak = 0
        rows = [
            ("Start Date", goal.get("Start_Date", "")),
            ("Ideal Completion Date", goal.get("Ideal_Completion_Date", "")),
            ("Estimated Completion Date", goal.get("Est_Completion_Date", "")),
            ("Status", goal.get("Status", "")),
            ("On Track?", goal.get("Behind_On Track_Ahead", "")),
            ("Last Update", goal.get("Last_Update", "")),
        ]
        info = "".join(f"<dt>{esc(label)}:</dt><dd>{esc(value)}</dd>" for label, value in rows)
        content = f"""
  <h1>{esc(goal["Name"])}</h1>
  <p class="dashboard-summary">{esc(goal["Category"])} | {esc(goal["Status"].capitalize())} | {esc(goal["Behind_On Track_Ahead"])}</p>
  <div class="dial" style="--percent: {max(0, min(percent, 100))}">
    <span>{percent:.1f}%</span>
  </div>
  <div class="progress-grid">
    {progress_row("Hours Spent", hours_spent, est_hours)}
    {progress_row("Time Remaining", remaining_days, total_days or 1, time_label)}
  </div>
  <p class="streak">{streak} Day Streak!</p>
  <dl class="info-grid">{info}</dl>
  {button_link("Back to Goals", "/goals")}
"""
        return page(f"Dashboard - {goal['Name']}", window("Dashboard", content, "900px", "dashboard-window"), wide=True, dark=True)

    def update_goal(self, state):
        active = [g for g in state["goals"] if g["Status"] == "Active"]
        selected = urlparse(self.path).query
        selected_name = parse_qs(selected).get("name", [active[0]["Name"] if active else ""])[0]
        goal = self.find_goal(state, selected_name) if selected_name else None
        if not active:
            content = f"<h2>Edit Goal</h2>{flash_html(state)}<p>There are no active goals to update.</p>{button_link('Back', '/')}"
            return page("Edit Goal", window("Edit Goal", content, "550px"))
        fields = ""
        if goal:
            for field in EDITABLE_FIELDS:
                fields += f'<label>{esc(field.replace("_", " "))}:<input name="{esc(field)}" value="{esc(goal.get(field, ""))}"></label>'
        content = f"""
  <h2>Edit Goal</h2>
  {flash_html(state)}
  <form class="stack-form compact" method="get" action="/update">
    <label>Select Goal:<select name="name" onchange="this.form.submit()">{option_tags([g["Name"] for g in active], selected_name)}</select></label>
  </form>
  <form class="stack-form compact" method="post" action="/update">
    <input type="hidden" name="original_name" value="{esc(selected_name)}">
    {fields}
    <button class="tk-button" type="submit">Save Changes</button>
  </form>
  {button_link("Back", "/")}
"""
        return page("Edit Goal", window("Edit Goal", content, "550px"))

    def save_goal(self, state, form):
        original = form.get("original_name", "")
        goal = self.find_goal(state, original)
        if not goal:
            flash(state, "Goal not found.")
            return self.redirect("/update")
        for field in EDITABLE_FIELDS:
            goal[field] = form.get(field, "").strip()
        goal["Est_Completion_Date"] = calculate_estimated_completion(
            goal["Start_Date"], goal["Hours_Spent"], goal["Est_Hours_To_Completion"], goal["Ideal_Completion_Date"]
        )
        goal["Behind_On Track_Ahead"] = on_track_tracker(goal["Est_Completion_Date"], goal["Ideal_Completion_Date"])
        goal["Completion_%"] = calculate_completion_percentage(goal["Hours_Spent"], goal["Est_Hours_To_Completion"])
        goal["Last_Update"] = datetime.today().strftime("%m/%d/%Y")
        flash(state, f"Goal '{goal['Name']}' updated successfully!")
        return self.redirect("/")

    def delete_goal(self, state):
        names = [g["Name"] for g in state["goals"]]
        content = f"""
  <h2>Delete Goal</h2>
  {flash_html(state)}
  <form class="stack-form" method="post" action="/delete" onsubmit="return confirm('Are you sure you want to delete this goal?')">
    <label>Select Goal to Delete:<select name="name">{option_tags(names)}</select></label>
    <button class="tk-button danger" type="submit">Delete Goal</button>
  </form>
  {button_link("Back", "/")}
"""
        return page("Delete Goal", window("Delete Goal", content, "400px"))

    def perform_delete(self, state, form):
        name = form.get("name", "")
        state["goals"] = [goal for goal in state["goals"] if goal["Name"] != name]
        flash(state, f"Goal '{name}' has been deleted.")
        return self.redirect("/")

    def work_session(self, state):
        active = [g for g in state["goals"] if g["Status"] == "Active"]
        items = "".join(f'<a class="list-item" href="/timer?{urlencode({"name": g["Name"]})}">{esc(g["Name"])}</a>' for g in active)
        if not items:
            items = '<div class="empty-row">You have no active goals to work on.</div>'
        content = f"""
  <h2>Select Goal</h2>
  {flash_html(state)}
  <p class="section-label">Select the goal you're working on:</p>
  <div class="listbox short">{items}</div>
  {button_link("Back", "/")}
"""
        return page("Select Goal", window("Select Goal", content, "400px"))

    def timer(self, state, name):
        if not self.find_goal(state, name):
            flash(state, "Please select a goal.")
            return self.work_session(state)
        content = f"""
  <h2>Work Session - {esc(name)}</h2>
  <div id="timer" class="timer">25:00</div>
  <div class="menu-buttons small">
    <button class="tk-button" id="toggle" type="button">Start / Pause</button>
    <button class="tk-button" id="add" type="button">Add 1 Min</button>
    <button class="tk-button" id="sub" type="button">Subtract 1 Min</button>
    <button class="tk-button" id="reset" type="button">Reset Timer</button>
    {button_link("End Session", "/")}
  </div>
  <dialog id="recallDialog" class="tk-dialog">
    <form method="post" action="/session-complete">
      <input type="hidden" name="goal_name" value="{esc(name)}">
      <input type="hidden" name="minutes_worked" id="minutesWorked" value="25">
      <label>Write what you recall from this session:<textarea name="notes" rows="10"></textarea></label>
      <div class="dialog-actions">
        <button class="tk-button" type="submit">Submit</button>
        <button class="tk-button" name="skip" value="1" type="submit">Skip</button>
      </div>
    </form>
  </dialog>
"""
        script = """
<script>
let remaining = 25 * 60;
let initialDuration = remaining;
let running = false;
let tick = null;
const timer = document.querySelector('#timer');
const dialog = document.querySelector('#recallDialog');
function render() {
  const mins = Math.floor(remaining / 60).toString().padStart(2, '0');
  const secs = (remaining % 60).toString().padStart(2, '0');
  timer.textContent = `${mins}:${secs}`;
}
function stop() {
  running = false;
  if (tick) clearInterval(tick);
  tick = null;
}
document.querySelector('#toggle').addEventListener('click', () => {
  if (running) {
    stop();
    return;
  }
  running = true;
  initialDuration = remaining;
  tick = setInterval(() => {
    remaining -= 1;
    render();
    if (remaining <= 0) {
      stop();
      document.querySelector('#minutesWorked').value = Math.round(initialDuration / 60 * 10000) / 10000;
      dialog.showModal();
    }
  }, 1000);
});
document.querySelector('#add').addEventListener('click', () => { remaining += 60; render(); });
document.querySelector('#sub').addEventListener('click', () => { if (remaining > 60) remaining -= 60; render(); });
document.querySelector('#reset').addEventListener('click', () => { stop(); remaining = 25 * 60; render(); });
render();
</script>
"""
        return page(f"Work Session - {name}", window("Work Session", content, "300px"), script=script)

    def complete_session(self, state, form):
        name = form.get("goal_name", "")
        goal = self.find_goal(state, name)
        if not goal:
            flash(state, "Goal not found.")
            return self.redirect("/")
        try:
            minutes = float(form.get("minutes_worked", "0"))
        except ValueError:
            minutes = 0
        try:
            current_hours = float(goal["Hours_Spent"])
        except ValueError:
            current_hours = 0
        updated_hours = current_hours + (minutes / 60)
        goal["Hours_Spent"] = str(round(updated_hours, 4))
        goal["Completion_%"] = calculate_completion_percentage(goal["Hours_Spent"], goal["Est_Hours_To_Completion"]).replace("%", "")
        notes = form.get("notes", "").strip()
        if notes:
            filename = f"{name}_{datetime.today().strftime('%Y-%m-%d')}.txt"
            state["notes"].setdefault(name, []).append({"filename": filename, "content": notes + "\n\n"})
        flash(state, f"Work session saved for '{name}'.")
        return self.redirect("/")

    def view_recall(self, state):
        projects = sorted(state["notes"].keys())
        selected_project = parse_qs(urlparse(self.path).query).get("project", [projects[0] if projects else ""])[0]
        entries = state["notes"].get(selected_project, [])
        selected_file = parse_qs(urlparse(self.path).query).get("entry", [entries[0]["filename"] if entries else ""])[0]
        selected_note = ""
        for entry in entries:
            if entry["filename"] == selected_file:
                selected_note = entry["content"]
                break
        project_options = option_tags(projects, selected_project)
        entry_options = option_tags([entry["filename"] for entry in entries], selected_file)
        content = f"""
  <h2>View Recall Notes</h2>
  {flash_html(state)}
  <form class="stack-form recall-form" method="get" action="/recall">
    <label>Select Project:<select name="project" onchange="this.form.submit()">{project_options}</select></label>
    <label>Select Recall Entry:<select name="entry">{entry_options}</select></label>
    <button class="tk-button" type="submit">View Notes</button>
  </form>
  <pre class="note-display">{esc(selected_note)}</pre>
  {button_link("Back", "/")}
"""
        return page("View Recall Notes", window("View Recall Notes", content, "700px"))


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), DemoHandler)
    print(f"Only Up web demo running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()
