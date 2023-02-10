import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init(config):
    global __factory

    if __factory:
        return

    connection_string = f"{config['drivername']}://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

    engine = sa.create_engine(connection_string, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
