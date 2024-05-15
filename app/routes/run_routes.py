from typing import List
from flask import Blueprint, current_app, jsonify, request
from marshmallow import Schema, fields, post_load
from marshmallow.validate import Length, Range
from datetime import date, datetime, timedelta

from sqlalchemy import and_

from app.auth import auth_required, get_token_and_user_id_from_cookies
from app.models.models import Runs
from app.routes import abort

PAGE_SIZE: int = 20  # default page size for # of runs to return
MAX_PAGE_SIZE: int = 50

runs_blueprint = Blueprint("runs_blueprint", __name__)


class RunSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(
        required=True,
        validate=lambda x: x >= date(2024, 1, 1),
    )
    run_start_time = fields.Time(required=False)
    distance_mi = fields.Float(
        required=True,
        validate=lambda x: 0.1 <= x <= 10,
    )
    runtime_s = fields.Integer(
        required=True,
        validate=Range(min=60 * 2, max=60 * 60 * 2),
    )
    notes = fields.String(
        required=False,
        validate=Length(max=1000),
    )
    created_at = fields.DateTime(dump_only=True, format="%Y-%m-%d %H:%M:%S")

    @post_load
    def make_run(self, data, **kwargs):
        return Runs(**data)


register_run_schema = RunSchema()


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


@runs_blueprint.route("/api/runs", methods=["GET"])
@auth_required
def get_runs():
    _, user_id = get_token_and_user_id_from_cookies()
    print(request.args)

    page_num = request.args.get("page", 0, type=int)
    page_size = request.args.get("size", PAGE_SIZE, type=int)

    if page_num < 0:
        return abort("Page query param should not be negative")
    if page_size <= 0 or page_size > MAX_PAGE_SIZE:
        return abort(f"Please specify a page_size in the range 1 to {MAX_PAGE_SIZE}")

    runs: List[Runs]
    total_count: int
    runs, total_count = get_runs_for_given_user(user_id, page_num, page_size)

    run_schema = RunSchema()

    return (
        jsonify(
            {
                "runs": [run_schema.dump(run) for run in runs],
                "total_runs": total_count,
                "page": page_num,
                "page_size": page_size,
                "runs_in_page": len(runs),
            }
        ),
        200,
    )


@runs_blueprint.route("/api/runs", methods=["POST"])
@auth_required
def create_run():
    _, user_id = get_token_and_user_id_from_cookies()
    errs = register_run_schema.validate(request.json)

    if errs:
        return abort(errs)

    run: Runs = register_run_schema.load(request.json)
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
                return abort("Start time of given run overlaps with existing run")

    with current_app.Session() as sess:
        try:
            sess.add(run)
            sess.commit()
        except Exception as e:
            sess.rollback()
            err = str(e)
            current_app.logger.error(err)

            return abort("Unknown error")

        return jsonify({"message": f"Run created with id {run.id}"}), 200


@runs_blueprint.route("/api/runs/<int:run_id>", methods=["DELETE"])
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

        return jsonify({"message": "Run succesfully deleted"}), 200
