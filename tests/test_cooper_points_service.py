from flask.testing import FlaskClient
from app.constants import DIST_INTERVALS
from app.models.models import ActivityType
from app.services.cooper_points_service import CooperPointsService
from tests import app, db_session


def test_get_points_below_min():
    # for now just a bit below will get you zero points
    for activity in ActivityType:
        assert (
            CooperPointsService.get_points(
                activity.value, DIST_INTERVALS[activity.value][0] - 0.1, "0:10:00"
            )
            == 0
        )


def test_get_points_in_range(db_session):
    assert CooperPointsService.get_points("bike", 10, "00:50:00") == 8.5

    assert CooperPointsService.get_points("swim", 600, "00:09:00") == 7.5
    assert CooperPointsService.get_points("swim", 630, "00:09:00") == 7.5
