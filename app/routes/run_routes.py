from typing import List
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from marshmallow import Schema, fields, post_load, validates
from marshmallow.validate import Length, Range
from datetime import date, datetime, timedelta

from sqlalchemy import and_

from app.auth import auth_required, get_token_and_user_id_from_cookies
from app.models.models import Runs
from app.routes import abort, flatten_validation_errors, stringify_validation_errors

PAGE_SIZE: int = 20  # default page size for # of runs to return
MAX_PAGE_SIZE: int = 50

runs_blueprint = Blueprint("runs_blueprint", __name__)


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

        runs: List[Runs] = (
            sess.query(Runs)
            .filter(filt)
            .order_by(Runs.date.asc(), Runs.run_start_time.asc())
            .all()
        )

        return runs


def get_runs_for_given_user(
    user_id: int, page_num: int, page_size: int = PAGE_SIZE
) -> tuple[List[Runs], int]:
    """
    page_num: starts at 0
    page_size: runs / page

    Returns paginated runs, and total count of runs
    """
    offset: int = (page_num) * page_size

    with current_app.Session() as sess:
        runs: List[Runs] = (
            sess.query(Runs)
            .filter(Runs.user_id == user_id)
            .order_by(Runs.date.desc(), Runs.run_start_time.desc())
            .limit(page_size)
            .offset(offset)
            .all()
        )
        total_count: int = sess.query(Runs).filter(Runs.user_id == user_id).count()

    return runs, total_count


class RunSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(
        required=True,
        validate=lambda x: x >= date(2024, 1, 1) and x <= datetime.now().date(),
    )
    run_start_time = fields.String(
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
        print("Before run", data)
        r = Runs(
            date=data["date"],
            run_start_time=data["run_start_time"] or None,
            distance_mi=data["distance_mi"],
            runtime_s=data["runtime_m"] * 60 + data["runtime_s"],
            notes=data["notes"],
        )
        # print(r)
        return r


register_run_schema = RunSchema()


@runs_blueprint.route("/create_run", methods=["GET", "POST"])
@auth_required
def create_run():
    current_date = datetime.today().strftime("%Y-%m-%d")

    initial_data = {
        "logged_in": True,
        "firstname": session.get("firstname"),
        "current_date": current_date,
    }
    if request.method == "GET":
        return render_template("new_run.html", **initial_data)

    _, user_id = get_token_and_user_id_from_cookies()
    errs = register_run_schema.validate(request.form)

    if errs:
        initial_data["errors"] = flatten_validation_errors(errs)
        return render_template("new_run.html", **initial_data)

    run: Runs = register_run_schema.load(request.form)
    run.user_id = user_id
    print(run)
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
                return render_template("new_run.html", **initial_data)

    with current_app.Session() as sess:
        try:
            sess.add(run)
            sess.commit()
        except Exception as e:
            sess.rollback()
            err = str(e)
            current_app.logger.error(err)

            return abort("Unknown error")

        return render_template("run_created.html", **initial_data)


@runs_blueprint.route("/my_runs", methods=["GET"])
@auth_required
def get_runs():
    _, user_id = get_token_and_user_id_from_cookies()

    page_num = request.args.get("page", 0, type=int)
    page_size = request.args.get("size", PAGE_SIZE, type=int)

    if page_num < 0:
        flash("Page query param should not be negative", "error")
        return render_template("index.html")
    if page_size <= 0 or page_size > MAX_PAGE_SIZE:
        flash(f"Please specify a page_size in the range 1 to {MAX_PAGE_SIZE}")
        return render_template("index.html")

    runs: List[Runs]
    total_count: int
    runs, total_count = get_runs_for_given_user(user_id, page_num, page_size)

    run_schema = RunSchema()
    runs = [run_schema.dump(run) for run in runs]

    return render_template(
        "index.html",
        runs=runs,
        total_runs=total_count,
        page=page_num,
        page_size=page_size,
        runs_in_page=len(runs),
        logged_in=True,
        firstname=session.get("firstname"),
    )


@runs_blueprint.route("/delete_run/<int:run_id>", methods=["DELETE"])
@auth_required
def delete_run(run_id):
    _, user_id = get_token_and_user_id_from_cookies()

    with current_app.Session() as sess:
        run_to_delete = sess.query(Runs).get(run_id)
        if not run_to_delete:
            return abort("Run not found for given id", 404)
        if run_to_delete.user_id != user_id:
            return abort("Can't delete this run - owned by another user", 404)
        sess.delete(run_to_delete)
        sess.commit()

        # TODO - handle deletions from other elements
        return ""