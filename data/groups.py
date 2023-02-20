import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Group(SqlAlchemyBase):
    __tablename__ = "groups"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name_lower = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    users = orm.relationship("User", back_populates="group")
    timetables = orm.relationship("Timetable", back_populates='group')

    def __repr__(self):
        return f"Group(id:{self.id}, name:{self.name}, users:{len(self.users)}, timetables:{len(self.timetables)})"
