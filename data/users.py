import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    api_id = sqlalchemy.Column(sqlalchemy.Integer, index=True, unique=True)
    state = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    theme = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    group_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("groups.id"))
    group = orm.relationship('Group', back_populates="users")

    def __repr__(self):
        return f"User(id:{self.id}, api_id:{self.api_id}, state:{self.state}," \
               f" theme:{self.theme}, group_id:{self.group_id}, group:{self.group})"
