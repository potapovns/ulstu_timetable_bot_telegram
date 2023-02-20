import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Timetable(SqlAlchemyBase):
    __tablename__ = "timetables"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    week_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    week_json = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    updated_datetime = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    group_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("groups.id", ondelete="CASCADE"))
    group = orm.relationship('Group', back_populates="timetables")
    images = orm.relationship("Image", back_populates='timetable')
