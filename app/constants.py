from app.models.models import ActivityType

REGEX_PATTERN_DURATION = r"^([0-9]|10):[0-5][0-9]:[0-5][0-9]$"

# unit adjusted based on activity type
MIN_DIST = {
    ActivityType.WALK.value: 0.1,
    ActivityType.RUN.value: 0.1,
    ActivityType.BIKE.value: 1,
    ActivityType.SWIM.value: 25,  # yards
}

MAX_DIST = {
    ActivityType.WALK.value: 30,
    ActivityType.RUN.value: 30,
    ActivityType.BIKE.value: 100,
    ActivityType.SWIM.value: 5000,  # yards
}
