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

    def __repr__(self):
        return f"<Credentials {self.id}, {self.login}>"


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    firstname = Column(String(), nullable=False)
    lastname = Column(String(), nullable=True)
    email = Column(String(), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now())
    deleted_at = Column(DateTime, nullable=True, default=None)

    def __repr__(self):
        return f"<Users {self.id}, {self.firstname} {self.lastname} {self.email}>"


class Runs(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, default=func.current_date())
    run_start_time = Column(Time, nullable=True)
    distance_mi = Column(Float, nullable=False)
    runtime_s = Column(Integer, nullable=False)
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
