from math import ceil
import re
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
from marshmallow import (
    Schema,
    fields,
    post_dump,
    post_load,
    validate,
    validates_schema,
)
from marshmallow.validate import Length
from datetime import date, datetime, timedelta

from sqlalchemy import and_, asc, desc

from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
)
from app.constants import MAX_DIST, MIN_DIST, REGEX_PATTERN_DURATION
from app.models.models import ActivityType, Runs, Users
from app.routes import DEFAULT_ORDERING, flatten_validation_errors
from app.utils.utils import (
    calculate_pace,
    seconds_to_time,
    time_pattern_to_seconds,
    time_to_display,
)

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
            filt = and_(filt, Runs.activity_start_time.isnot(None))

        filt = and_(filt, Runs.deleted_at.is_(None))

        runs: List[Runs] = (
            sess.query(Runs)
            .filter(filt)
            .order_by(Runs.date.asc(), Runs.activity_start_time.asc())
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
    activity_start_time = fields.String(  # TODO - validate time field
        required=False, allow_none=True, validate=lambda _: True
    )
    distance_mi_or_yd = fields.Float(
        required=True,
        validate=lambda x: MIN_DIST[ActivityType.WALK.value]
        <= float(x)
        <= MAX_DIST[ActivityType.SWIM.value],
    )
    activity_duration = fields.String(
        required=True,
        validate=lambda dur: re.match(REGEX_PATTERN_DURATION, dur),
    )
    distance_mi = fields.Decimal(places=2, dump_only=True)
    distance_yard = fields.Int(dump_only=True)
    duration_s = fields.Int(dump_only=True)
    activity_type = fields.Str(
        required=True, validate=validate.OneOf([a.value.lower() for a in ActivityType])
    )
    pace = fields.Decimal(places=2, dump_only=True)
    notes = fields.String(
        required=False,
        validate=Length(max=1000),
    )
    created_at = fields.DateTime(dump_only=True, format="%Y-%m-%d %H:%M:%S")

    @validates_schema
    def validate_distance(self, data, **kwargs):
        print("In validate _distance, provided data", data)
        # TODO - implement distance validation
        pass

    @post_load
    def make_run(self, data, **kwargs) -> Runs:
        activity_start_time = data["activity_start_time"]
        if activity_start_time:
            activity_start_time_hh_mm = ":".join(activity_start_time.split(":")[0:2])

            activity_start_time = datetime.strptime(
                activity_start_time_hh_mm, "%H:%M"
            ).time()

        activity = Runs(
            date=data["date"],
            activity_start_time=activity_start_time or None,
            duration_s=time_pattern_to_seconds(data["activity_duration"]),
            activity_type=data["activity_type"],
            notes=data["notes"],
        )

        if data["activity_type"] == ActivityType.SWIM.value:
            activity.distance_yard = data["distance_mi_or_yd"]
        else:
            activity.distance_mi = data["distance_mi_or_yd"]

        activity.pace = calculate_pace(
            activity.duration_s, activity.distance_mi, activity.distance_yard
        )

        return activity

    @post_dump
    def post_process(self, data, **kwargs):
        """Sanitize data for display. Can add more fields"""
        # transform to hh:mm AM/PM
        data["activity_start_time_formatted"] = time_to_display(
            data.get("activity_start_time")
        )

        data["duration_hmmss"] = seconds_to_time(data.get("duration_s"))
        print(data)
        return data


register_run_schema = RunSchema()


@runs_blueprint.route("/runs/new", methods=["GET"])
@auth_required
def create_run_get():
    current_date = datetime.today().strftime("%Y-%m-%d")

    initial_data = {
        "date": current_date,
        "activity_type": ActivityType,
    }

    return render_template("runs/new_run.html", **initial_data)


@runs_blueprint.route("/runs", methods=["POST"])
@auth_required
def create_run():
    current_date = datetime.today().strftime("%Y-%m-%d")

    initial_data = {
        "activity_type": ActivityType,
    }
    _, user_id = get_token_and_user_id_from_cookies()
    print("Form: ", request.form)
    errs = register_run_schema.validate(request.form)

    initial_data["date"] = request.form["date"] or current_date
    initial_data["activity_start_time"] = request.form["activity_start_time"]
    initial_data["distance_mi_or_yd"] = request.form["distance_mi_or_yd"]
    initial_data["activity_type_selected"] = request.form["activity_type"]
    initial_data["activity_duration"] = request.form["activity_duration"]
    initial_data["notes"] = request.form["notes"]
    initial_data["activity_type"] = ActivityType

    if errs:
        initial_data["errors"] = flatten_validation_errors(errs)
        if "activity_start_time" in initial_data["errors"]:
            del initial_data["activity_start_time"]
        if "distance_mi" in initial_data["errors"]:
            del initial_data["distance_mi"]
        if "duration_m" in initial_data["errors"]:
            del initial_data["duration_m"]
        if "duration_s" in initial_data["errors"]:
            del initial_data["duration_s"]
        if "notes" in initial_data["errors"]:
            del initial_data["notes"]
        print("Errs, ", errs, initial_data)
        return render_template("runs/new_run.html", **initial_data)

    if Users.find(user_id).is_readonly:
        flash(READONLY_MESSAGE, "error")
        return render_template("runs/new_run.html", **initial_data)

    run: Runs = register_run_schema.load(request.form)
    run.user_id = user_id
    existing_runs = get_runs_for_given_date(run.date, user_id)

    if run.activity_start_time:
        run_start_dt: datetime = datetime.combine(run.date, run.activity_start_time)

        for existing_run in existing_runs:
            ex_run_start_dt: datetime = datetime.combine(
                existing_run.date, existing_run.activity_start_time
            )
            ex_run_end_dt = ex_run_start_dt + timedelta(seconds=existing_run.duration_s)
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
    if order_by not in DEFAULT_ORDERING:
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
        return render_template("runs/run_not_found.html")

    if run.user_id != user_id:
        return render_template(
            "runs/invalid_permission.html",
            error_message="You do not have permission to view this run.",
        )

    days_ago = {0: "today", 1: "yesterday"}.get(
        int((datetime.now().date() - run.date).days),
        f"{(datetime.now().date() - run.date).days} days ago",
    )

    run = RunSchema().dump(run)

    return render_template("runs/show_run.html", days_ago=days_ago, run=run)


@runs_blueprint.route("/runs/<int:run_id>/edit", methods=["GET"])
@auth_required
def edit_run_get(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    activity: Runs = Runs.find(run_id)

    if not activity:
        return render_template("runs/run_not_found.html")

    if activity.user_id != user_id:
        return render_template(
            "runs/invalid_permission.html",
            error_message="You do not have permission to view and edit this activity.",
        )

    return render_template(
        "runs/edit_run.html",
        run=RunSchema().dump(activity),
        activity_types=ActivityType,
    )


@runs_blueprint.route("/runs/<int:run_id>/edit", methods=["PUT"])
@auth_required
def edit_run_put(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    run: Runs = Runs.find(run_id)

    if not run:
        return render_template("runs/run_not_found.html")

    if run.user_id != user_id:
        return render_template(
            "runs/invalid_permission.html",
            error_message="You do not have permission to view and edit this activity.",
        )

    if Users.find(user_id).is_readonly == 1:
        flash(READONLY_MESSAGE, "error")
        return render_template("runs/edit_run.html", run=RunSchema().dump(run))

    print(request.form)
    errs = register_run_schema.validate(request.form)

    if errs:
        return render_template(
            "runs/edit_run.html",
            run=RunSchema().dump(run),
            errors=flatten_validation_errors(errs),
        )

    print("Before loading, ", request.form)
    new_run_data: Runs = register_run_schema.load(request.form)
    print(new_run_data)
    if (
        new_run_data.date == run.date
        and new_run_data.activity_start_time == run.activity_start_time
        and new_run_data.distance_mi == run.distance_mi
        and new_run_data.distance_yard == run.distance_yard
        and new_run_data.duration_s == run.duration_s
        and new_run_data.notes == run.notes
        and new_run_data.activity_type == run.activity_type
    ):
        print("No changes were made to the activity")
        flash("No changes were made to the activity", "message")
        return render_template("runs/edit_run.html", run=RunSchema().dump(run))

    print("ABOUT TO UPDATE")
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
        return render_template("runs/run_not_found.html")

    if run.user_id != user_id:
        flash("You do not have permission to delete this activity.", "error")
    elif Users.find(user_id).is_readonly == 1:
        flash(READONLY_MESSAGE, "error")
    else:
        run.delete()
        flash(f"Run with id {run_id} was deleted successfully", "message")

    return redirect(url_for("runs_blueprint.get_runs"), code=303)
