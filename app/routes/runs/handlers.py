from flask import render_template
from app.auth import auth_required, get_user_id
from app.routes.run_routes import RunSchema
from app.routes.runs.utils import (
    INVALID_PERMISSION_ERR,
    RUN_NOT_FOUND_ERR,
    common_initial_data,
    get_run_and_validate_permission,
)
from app.utils.utils import calc_days_ago


@auth_required
def new_run():
    user_id = get_user_id()
    initial_data = common_initial_data(user_id)
    return render_template("runs/new_run.html", **initial_data)


@auth_required
def show_run(run_id):
    user_id = get_user_id()
    run, error = get_run_and_validate_permission(run_id, user_id)

    if error == RUN_NOT_FOUND_ERR:
        return render_template("runs/run_not_found.html")

    if error == INVALID_PERMISSION_ERR:
        return render_template(
            "runs/invalid_permission.html",
            error_message=INVALID_PERMISSION_ERR,
        )

    days_ago = calc_days_ago(run.date)
    run = RunSchema().dump(run)

    return render_template("runs/show_run.html", days_ago=days_ago, run=run)
