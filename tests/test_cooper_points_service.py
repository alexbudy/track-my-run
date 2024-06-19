from app.constants import DIST_INTERVALS
from app.models.models import ActivityType
from app.services.cooper_points_service import CooperPointsService
from tests import app, db_session


def test_get_points_below_min_dist():
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


def test_get_points_above_max_dist(db_session):
    assert CooperPointsService.get_points("swim", 3500, "2:00:00") == 0.0
    assert CooperPointsService.get_points("swim", 3500, "1:00:00") == 37.0

    assert CooperPointsService.get_points("walk", 30, "09:00:00") == 25.22
    assert (
        CooperPointsService.get_points("walk", 30, "12:00:00") == 25.22
    )  # above time cap of 10:00:01

    assert CooperPointsService.get_points("bike", 110, "09:00:00") == 98.5
    assert (
        CooperPointsService.get_points("bike", 110, "12:00:00") == 68.5
    )  # above time cap of 10:00:01
