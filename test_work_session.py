# test_work_session.py

from work_session import select_active_goal, WorkSession

goal = select_active_goal()
if goal:
    session = WorkSession(goal)
    session.start()
