from datetime import date, timedelta
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Date,
    Numeric,
    Time,
    ForeignKey,
    MetaData,
    String,
    Integer,
    Float,
    func,
)
from enum import Enum
from app.extensions import db
from app.utils.utils import calculate_pace, hash_password


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base = declarative_base(
    metadata=MetaData(naming_convention=convention)  # TODO add schema here if needed
)


class BaseMixin(object):
    """Common methods for given models"""

    @classmethod
    def find(cls, id_):
        id_ = int(id_)

        obj = db.session.query(cls).filter(cls.id == id_).first()
        return obj

    def save(self):
        print("Saving", self)
        db.session.add(self)
        db.session.commit()


class Credentials(BaseMixin, Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(), unique=True, nullable=False)
    hashed_pass = Column(String(), nullable=False)
    salt = Column(String(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    user = relationship("Users", backref="users", uselist=False)

    @classmethod
    def find_cred_on_login(cls, login):
        cred = db.session.query(Credentials).filter(Credentials.login == login).first()
        return cred

    @classmethod
    def update_password(cls, login, password):
        cred = Credentials.find_cred_on_login(login)
        hashed_pass: str = hash_password(password, cred.salt)

        if hashed_pass == cred.hashed_pass:
            raise ValueError("Old password cannot be the same as new password")

        cred.hashed_pass = hashed_pass
        cred.updated_at = func.now()
        cred.save()

    def __repr__(self):
        return f"<Credentials {self.id}, {self.login}>"


class Users(BaseMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nick = Column(String(), unique=False, nullable=True)
    email = Column(String(), unique=False, nullable=True)
    email_verified_at = Column(DateTime, nullable=True, default=None)
    is_admin = Column(Integer, nullable=False, default=0)
    is_readonly = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    credentials = relationship("Credentials", backref="credentials", uselist=False)

    @classmethod
    def find_user_on_email(cls, email):
        user = db.session.query(Users).filter(Users.email == email).first()
        return user

    def __repr__(self):
        return f"<Users {self.id}, optional nick={self.nick}, email={self.email}, is_admin={self.is_admin}, is_readonly={self.is_readonly}>"


class ActivityType(Enum):
    BIKE = "bike"
    RUN = "run"
    SWIM = "swim"
    WALK = "walk"


# TODO - will need to rename to Activity
class Runs(BaseMixin, Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, default=func.current_date())
    activity_start_time = Column(Time, nullable=True)
    distance_mi = Column(Float, nullable=True)
    distance_yard = Column(Integer, nullable=True)  # TODO - rename to distance_yards
    duration_s = Column(Integer, nullable=False)
    activity_type = Column(
        String(),
        nullable=False,
        default=ActivityType.RUN.value,
        server_default=ActivityType.RUN.value,
    )
    pace = Column(
        Numeric(precision=6, scale=4), nullable=False
    )  # store as min/mi for now for easy sort
    notes = Column(String(), nullable=True)
    cooper_points = Column(Numeric(precision=5, scale=2), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    __table_args__ = (
        CheckConstraint(
            "(activity_type = 'swim' AND distance_yard IS NOT NULL AND distance_mi IS NULL) OR (activity_type != 'swim' AND distance_yard IS NULL AND distance_mi IS NOT NULL)",
            name="correct_metric_for_activity_type",
        ),
    )

    def __repr__(self):
        return (
            f"<Runs(id={self.id}, user_id={self.user_id}, date={self.date}, "
            f"activity_start_time={self.activity_start_time}, distance_mi={self.distance_mi}, distance_yard={self.distance_yard}, "
            f"duration_s={self.duration_s} activity_type={self.activity_type}, notes={self.notes})>"
        )

    def delete(self):
        # for now do soft-deletions
        self.deleted_at = func.now()
        db.session.commit()

    def update(self, new_run: "Runs"):
        self.date = new_run.date
        self.activity_start_time = (
            new_run.activity_start_time if new_run.activity_start_time else None
        )
        self.distance_mi = new_run.distance_mi
        self.distance_yard = new_run.distance_yard
        self.duration_s = new_run.duration_s
        self.activity_type = new_run.activity_type
        self.pace = calculate_pace(
            new_run.duration_s, new_run.distance_mi, new_run.distance_yard
        )
        self.notes = new_run.notes
        self.cooper_points = new_run.cooper_points
        self.updated_at = func.now()
        db.session.commit()

    @classmethod
    def total_points(cls, user_id: int, days_back: int = 7) -> float:
        result = (
            db.session.query(func.sum(Runs.cooper_points))
            .filter(
                Runs.user_id == user_id,
                Runs.date >= date.today() - timedelta(days=days_back),
                Runs.deleted_at.is_(None),
            )
            .scalar()
        )

        if not result:
            return 0

        return round(result, 1)


class CooperPoints(BaseMixin, Base):
    __tablename__ = "cooper_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity = Column(String(), nullable=False)
    distance_floor = Column(
        Numeric(precision=6, scale=2), nullable=False
    )  # distance based on activity. Traveled distance floored to nearest in table
    lowest_time = Column(Time, nullable=False)
    highest_time = Column(Time, nullable=False)
    points = Column(Numeric(precision=5, scale=2), nullable=False)

    def __repr__(self):
        return (
            f"<CooperPoints(id={self.id}, activity={self.activity}, distance_floor={self.distance_floor}, "
            f"lowest_time={self.lowest_time}, highest_time={self.highest_time}, points={self.points})>"
        )

    @classmethod
    def find_row(
        cls, activity: str, distance_floor: float | int, duration: str
    ) -> "CooperPoints":
        row = (
            db.session.query(CooperPoints)
            .filter(
                CooperPoints.activity == activity,
                CooperPoints.distance_floor == distance_floor,
                CooperPoints.lowest_time <= duration,
                duration <= CooperPoints.highest_time,
            )
            .order_by(CooperPoints.points.desc())
            .first()
        )
        return row
