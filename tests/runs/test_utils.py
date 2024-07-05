from datetime import date, timedelta
from app.routes.runs.utils import days_ago_in_words


def test_days_ago():
    assert "today" == days_ago_in_words(date.today())
    assert "yesterday" == days_ago_in_words(date.today() - timedelta(days=1))
    assert "2 days ago" == days_ago_in_words(date.today() - timedelta(days=2))
    assert "5 days ago" == days_ago_in_words(date.today() - timedelta(days=5))
