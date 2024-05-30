from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    DateTime,
    Date,
    Time,
    ForeignKey,
    MetaData,
    String,
    Integer,
    Float,
    func,
)
from enum import Enum
from app.database import db


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
        db.session.add(self)
        db.session.commit()


class Credentials(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(), unique=True, nullable=False)
    hashed_pass = Column(String(), nullable=False)
    salt = Column(String(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    @classmethod
    def find_cred_on_login(cls, login):
        cred = db.session.query(Credentials).filter(Credentials.login == login).first()
        return cred

    def __repr__(self):
        return f"<Credentials {self.id}, {self.login}>"


class Users(BaseMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nick = Column(String(), unique=False, nullable=True)
    email = Column(String(), unique=True, nullable=True)
    is_admin = Column(Integer, nullable=False, default=0)
    is_readonly = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    def __repr__(self):
        return f"<Users {self.id}, optional nick={self.nick}, is_admin={self.is_admin}, is_readonly={self.is_readonly}>"


class ActivityType(Enum):
    RUN = "run"
    BIKE = "bike"
    SWIM = "swim"


class Runs(BaseMixin, Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, default=func.current_date())
    run_start_time = Column(Time, nullable=True)
    distance_mi = Column(Float, nullable=False)
    runtime_s = Column(Integer, nullable=False)
    activity_type = Column(
        String(),
        nullable=False,
        default=ActivityType.RUN.value,
        server_default=ActivityType.RUN.value,
    )
    notes = Column(String(), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    def __repr__(self):
        return (
            f"<Runs(id={self.id}, user_id={self.user_id}, date={self.date}, "
            f"run_start_time={self.run_start_time}, distance_mi={self.distance_mi}, "
            f"runtime_s={self.runtime_s})>"
        )

    def delete(self):
        # for now do soft-deletions
        self.deleted_at = func.now()
        db.session.commit()

    def update(self, new_run: "Runs"):
        self.date = new_run.date
        self.run_start_time = new_run.run_start_time if new_run.run_start_time else None
        self.distance_mi = new_run.distance_mi
        self.runtime_s = new_run.runtime_s
        self.notes = new_run.notes
        self.updated_at = func.now()
        db.session.commit()
