from flask import Blueprint
from . import handlers

runs_blueprint_refactored = Blueprint("runs_blueprint_refactored", __name__)

# TODO start breaking up the routes

runs_blueprint_refactored.route("/new", methods=["GET"])(handlers.new_run)
runs_blueprint_refactored.route("/runs/<int:run_id>", methods=["GET"])(
    handlers.show_run
)

# runs_blueprint.route("/my_runs", methods=["GET"])(handlers.my_runs)
# runs_blueprint.route("/runs/<int:run_id>/edit", methods=["GET"])(handlers.edit_run_get)

# runs_blueprint.route("/runs", methods=["POST"])(handlers.create_run)
# runs_blueprint.route("/runs/<int:run_id>/edit", methods=["PUT"])(handlers.edit_run_put)
# runs_blueprint.route("/runs/<int:run_id>/delete", methods=["DELETE"])(
#     handlers.delete_run
# )

# runs_blueprint.route("/runs/cooper-points", methods=["GET"])(handlers.cooper_points)
