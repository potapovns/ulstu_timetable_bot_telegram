import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Image(SqlAlchemyBase):
    __tablename__ = "images"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    theme = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    filename = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    timetable_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("timetables.id"))
    timetable = orm.relationship('Timetable', back_populates="images")
