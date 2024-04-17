from sqlalchemy.ext.declarative import declarative_base


Base = (
    declarative_base()
)  # TODO - add schema? Base = declarative_base(metadata=MetaData(schema="myschema"))
metadata = Base.metadata


from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, func


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
