from math import ceil
from typing import List
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from marshmallow import Schema, fields, post_dump, post_load
from marshmallow.validate import Length, Range
from datetime import date, datetime, timedelta

from sqlalchemy import and_, asc, desc

from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
)
from app.models.models import Runs, Users
from app.routes import DEFAULT_ORDERING, flatten_validation_errors

PAGE_SIZE: int = 20  # default page size for # of runs to return
MAX_PAGE_SIZE: int = 50

runs_blueprint = Blueprint("runs_blueprint", __name__)

READONLY_MESSAGE = "Readonly user, cannot create or modify runs. Please use a different account to create or modify runs."


def get_runs_for_given_date(
    d: date, user_id: int, skip_runs_with_no_start_time: bool = True, overlap=True
):
    """overlap: Add previous and next day's runs as well"""
    with current_app.Session() as sess:
        if overlap:
            filt = and_(
                Runs.date >= d - timedelta(days=1), Runs.date <= d + timedelta(days=1)
            )
        else:
            filt = Runs.date == d

        filt = and_(filt, Runs.user_id == user_id)

        if skip_runs_with_no_start_time:
            filt = and_(filt, Runs.run_start_time.isnot(None))

        filt = and_(filt, Runs.deleted_at.is_(None))

        runs: List[Runs] = (
            sess.query(Runs)
            .filter(filt)
            .order_by(Runs.date.asc(), Runs.run_start_time.asc())
            .all()
        )

        return runs


def get_runs_for_given_user(
    user_id: int,
    page_num: int,
    page_size: int = PAGE_SIZE,
    order_by: str = "date",
    order: str = "desc",
) -> tuple[List[Runs], int]:
    """
    page_num: starts at 0
    page_size: runs / page

    Returns paginated runs, and total count of runs
    """
    offset: int = (page_num - 1) * page_size
    order_col = getattr(Runs, order_by)
    ordering = desc if order.lower() == "desc" else asc

    with current_app.Session() as sess:
        runs: List[Runs] = (
            sess.query(Runs)
            .filter(and_(Runs.deleted_at.is_(None), Runs.user_id == user_id))
            .order_by(ordering(order_col))
            .limit(page_size)
            .offset(offset)
            .all()
        )
        total_count: int = (
            sess.query(Runs)
            .filter(and_(Runs.deleted_at.is_(None), Runs.user_id == user_id))
            .count()
        )

    return runs, total_count


class RunSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(
        required=True,
        validate=lambda x: x >= date(2024, 1, 1) and x <= datetime.now().date(),
    )
    run_start_time = fields.String(  # TODO - validate time field
        required=False, allow_none=True, validate=lambda _: True
    )
    distance_mi = fields.Float(
        required=True,
        validate=lambda x: 0.1 <= x <= 10,
    )
    runtime_m = fields.Integer(
        required=True,
        validate=Range(min=1, max=60),
    )
    runtime_s = fields.Integer(
        required=True,
        validate=Range(min=0, max=59),
    )
    notes = fields.String(
        required=False,
        validate=Length(max=1000),
    )
    created_at = fields.DateTime(dump_only=True, format="%Y-%m-%d %H:%M:%S")

    @post_load
    def make_run(self, data, **kwargs):
        run_start_time = data["run_start_time"]
        if run_start_time:
            if run_start_time.count(":") >= 2:
                run_start_time = ":".join(run_start_time.split(":")[0:2])

            run_start_time = datetime.strptime(run_start_time, "%H:%M").time()

        r = Runs(
            date=data["date"],
            run_start_time=run_start_time or None,
            distance_mi=data["distance_mi"],
            runtime_s=data["runtime_m"] * 60 + data["runtime_s"],
            notes=data["notes"],
        )

        return r

    @post_dump
    def post_process_run_start_time(self, data, **kwargs):
        """Sanitize data for display"""
        run_start_time = data["run_start_time"]
        if run_start_time:
            hr = run_start_time.split(":")[0]
            mn = run_start_time.split(":")[1]
            data["run_start_time"] = run_start_time[0:6] + "00"
            if hr[0] == "0":
                hr = hr[1]

            am_pm = "AM"
            if int(hr) >= 12:
                am_pm = "PM"
            if int(hr) > 12:
                hr = int(hr) - 12

            data["run_start_time_formatted"] = f"{hr}:{mn} {am_pm}"

        data["distance_mi"] = float("{:.2f}".format(data["distance_mi"]))

        return data


register_run_schema = RunSchema()


@runs_blueprint.route("/runs/new", methods=["GET"])
@auth_required
def create_run_get():
    current_date = datetime.today().strftime("%Y-%m-%d")

    initial_data = {
        "logged_in": True,
        "current_date": current_date,
    }

    return render_template("runs/new_run.html", **initial_data)


@runs_blueprint.route("/runs", methods=["POST"])
@auth_required
def create_run():
    current_date = datetime.today().strftime("%Y-%m-%d")

    initial_data = {
        "logged_in": True,
        "current_date": request.form["date"] or current_date,
    }

    _, user_id = get_token_and_user_id_from_cookies()
    errs = register_run_schema.validate(request.form)

    initial_data["run_start_time"] = request.form["run_start_time"]
    initial_data["distance_mi"] = request.form["distance_mi"]
    initial_data["runtime_m"] = request.form["runtime_m"]
    initial_data["runtime_s"] = request.form["runtime_s"]
    initial_data["notes"] = request.form["notes"]
    print(initial_data)
    if errs:
        initial_data["errors"] = flatten_validation_errors(errs)
        if "run_start_time" in initial_data["errors"]:
            del initial_data["run_start_time"]
        if "distance_mi" in initial_data["errors"]:
            del initial_data["distance_mi"]
        if "runtime_m" in initial_data["errors"]:
            del initial_data["runtime_m"]
        if "runtime_s" in initial_data["errors"]:
            del initial_data["runtime_s"]
        if "notes" in initial_data["errors"]:
            del initial_data["notes"]

        return render_template("runs/new_run.html", **initial_data)

    if Users.find(user_id).is_readonly:
        flash(READONLY_MESSAGE, "error")
        return render_template("runs/new_run.html", **initial_data)

    run: Runs = register_run_schema.load(request.form)
    run.user_id = user_id
    existing_runs = get_runs_for_given_date(run.date, user_id)

    if run.run_start_time:
        run_start_dt: datetime = datetime.combine(run.date, run.run_start_time)

        for existing_run in existing_runs:
            ex_run_start_dt: datetime = datetime.combine(
                existing_run.date, existing_run.run_start_time
            )
            ex_run_end_dt = ex_run_start_dt + timedelta(seconds=existing_run.runtime_s)
            if ex_run_start_dt <= run_start_dt <= ex_run_end_dt:
                flash("Start time of given run overlaps with existing run")
                return render_template("runs/new_run.html", **initial_data)

    run.save()
    flash(f"Created run {run.id} for {run.date}", "message")
    session["highlight_run_id"] = run.id
    return redirect(url_for("runs_blueprint.get_runs"), code=303)


@runs_blueprint.route("/my_runs", methods=["GET"])
@auth_required
def get_runs():
    _, user_id = get_token_and_user_id_from_cookies()

    page_num = request.args.get("page", 1, type=int)
    page_size = request.args.get("size", PAGE_SIZE, type=int)
    order_by = request.args.get("order_by", "date", type=str)
    order = request.args.get("order", "desc", type=str)

    highlight_run_id = None
    if "highlight_run_id" in session:
        highlight_run_id = (
            session["highlight_run_id"] if "highlight_run_id" in session else None
        )
        del session["highlight_run_id"]

    if page_num < 1:
        page_num = 1
    if page_size <= 0 or page_size > MAX_PAGE_SIZE:
        page_size = PAGE_SIZE
    if order_by not in ["date", "run_start_time", "distance_mi", "runtime_s"]:
        order_by = "date"
    if order not in ["asc", "desc"]:
        order = "desc"

    runs: List[Runs]
    total_count: int
    runs, total_count = get_runs_for_given_user(
        user_id, page_num, page_size, order_by, order
    )

    run_schema = RunSchema()
    runs = [run_schema.dump(run) for run in runs]

    ordering = DEFAULT_ORDERING.copy()
    ordering[order_by] = "desc" if order == "asc" else "asc"  # flip the order
    ordering["last_ordered"] = order_by
    ordering["last_ordered_dir"] = order

    return render_template(
        "index.html",
        runs=runs,
        page=page_num,
        total_count=total_count,
        runs_in_page=len(runs),
        logged_in=True,
        order_vals=ordering,
        total_pages=ceil(total_count / page_size) or 1,
        highlight_run_id=highlight_run_id,
    )


@runs_blueprint.route("/runs/<int:run_id>", methods=["GET"])
@auth_required
def show_run(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    run: Runs = Runs.find(run_id)

    if not run:
        return render_template("runs/run_not_found.html", logged_in=True)

    if run.user_id != user_id:
        return render_template(
            "runs/invalid_permission.html",
            error_message="You do not have permission to view this run.",
            logged_in=True,
        )

    days_ago = {0: "today", 1: "yesterday"}.get(
        int((datetime.now().date() - run.date).days),
        f"{(datetime.now().date() - run.date).days} days ago",
    )

    run = RunSchema().dump(run)

    return render_template(
        "runs/show_run.html", days_ago=days_ago, run=run, logged_in=True
    )


@runs_blueprint.route("/runs/<int:run_id>/edit", methods=["GET"])
@auth_required
def edit_run_get(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    run: Runs = Runs.find(run_id)

    if not run:
        return render_template("runs/run_not_found.html", logged_in=True)

    if run.user_id != user_id:
        return render_template(
            "runs/invalid_permission.html",
            error_message="You do not have permission to view and edit this run.",
            logged_in=True,
        )

    run = RunSchema().dump(run)

    return render_template("runs/edit_run.html", run=run, logged_in=True)


@runs_blueprint.route("/runs/<int:run_id>/edit", methods=["PUT"])
@auth_required
def edit_run_put(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    run: Runs = Runs.find(run_id)

    if not run:
        return render_template("runs/run_not_found.html", logged_in=True)

    if run.user_id != user_id:
        return render_template(
            "runs/invalid_permission.html",
            error_message="You do not have permission to view and edit this run.",
            logged_in=True,
        )

    if Users.find(user_id).is_readonly == 1:
        flash(READONLY_MESSAGE, "error")
        return render_template(
            "runs/edit_run.html", run=RunSchema().dump(run), logged_in=True
        )

    errs = register_run_schema.validate(request.form)
    if errs:
        return render_template(
            "runs/edit_run.html",
            run=RunSchema().dump(run),
            errors=flatten_validation_errors(errs),
            logged_in=True,
        )

    new_run_data: Runs = register_run_schema.load(request.form)

    if (
        new_run_data.date == run.date
        and new_run_data.run_start_time == run.run_start_time
        and new_run_data.distance_mi == run.distance_mi
        and new_run_data.runtime_s == run.runtime_s
        and new_run_data.notes == run.notes
    ):
        flash("No changes were made to the run", "message")
        return render_template(
            "runs/edit_run.html",
            run=RunSchema().dump(run),
            logged_in=True,
        )

    run.update(new_run_data)

    flash(f"Run {run_id} edited successfully", "message")
    session["highlight_run_id"] = run_id
    return redirect(url_for("runs_blueprint.get_runs"), code=303)


@runs_blueprint.route("/runs/<int:run_id>/delete", methods=["DELETE"])
@auth_required
def delete_run(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    run: Runs = Runs.find(run_id)

    if not run:
        return render_template("runs/run_not_found.html", logged_in=True)

    if run.user_id != user_id:
        flash("You do not have permission to delete this run.", "error")
    elif Users.find(user_id).is_readonly == 1:
        flash(READONLY_MESSAGE, "error")
    else:
        run.delete()
        flash(f"Run with id {run_id} was deleted successfully", "message")

    return redirect(url_for("runs_blueprint.get_runs"), code=303)
