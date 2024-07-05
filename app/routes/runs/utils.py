from app.auth import get_token_and_user_id_from_cookies
from app.models.models import ActivityType, Runs
from app.utils.utils import calc_days_ago, current_date_to_display

RUN_NOT_FOUND_ERR = "Run not found"
INVALID_PERMISSION_ERR = "You do not have permission to view this run."


def get_user_id() -> int:
    _, user_id = get_token_and_user_id_from_cookies()
    return user_id


def common_initial_data(user_id) -> dict:
    return {
        "date": current_date_to_display(),
        "activity_type": ActivityType,
        "cooper_points": 0,
        "weekly_cooper_points": Runs.total_points(user_id),
    }


def get_run_and_validate_permission(run_id, user_id) -> tuple[Runs, str]:
    run = Runs.find(run_id)
    if not run:
        return None, "Run not found"
    if run.user_id != user_id:
        return None, "You do not have permission to view this run."
    return run, None


def days_ago(date):
    days_ago = {0: "today", 1: "yesterday"}.get(
        calc_days_ago(date),
        f"{calc_days_ago(date)} days ago",
    )
    return days_ago
