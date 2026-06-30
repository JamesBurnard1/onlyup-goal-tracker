from datetime import datetime, timedelta


def calculate_completion_percentage(hours_spent, est_hours):
    if est_hours > 0:
        return f"{round((hours_spent / est_hours) * 100, 1)}%"
    return "N/A"


def calculate_estimated_completion(start_date, hours_spent, est_hours, goal_due_date):
    due_date = datetime.strptime(goal_due_date, "%m/%d/%Y")
    
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