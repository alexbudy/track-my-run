from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


from sqlalchemy import Column, DateTime, String, Integer, func


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(60), unique=True)
    age = Column(Integer)
    note = Column(String(200))
    create_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"
    
class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(), nullable=True)

    def __repr__(self):
        return f"<Users {self.id}, {self.name}>"