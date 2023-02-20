from loguru import logger as log
from data.__all_classes import *


async def get_db_user(api_user_id: int, db_sess):
    db_user = db_sess.query(User).filter(User.api_id == api_user_id).first()
    if db_user is None:
        log.debug(f"DB user not found by api_id:[{api_user_id}]")
    else:
        log.debug(f"DB found: {db_user}")
    return db_user


async def get_db_group(group_name: str, db_sess):
    group_name_lower = group_name.lower()
    db_group = db_sess.query(Group).filter(Group.name_lower == group_name_lower).first()
    if db_group is None:
        log.debug(f"DB group not found by group_name:[{group_name}]")
    else:
        log.debug(f"DB found: {db_group}")
    return db_group


async def set_db_user_state(db_user, db_sess, state):
    db_user.state = state
    db_sess.commit()
    log.debug(f"DB set state [{state}] to {db_user}")


async def set_db_user_group(db_user, db_sess, db_group):
    db_user.group = db_group
    db_user.group_id = db_group.id
    db_sess.commit()
    log.debug(f"DB set group [{db_group.name}] to {db_user}")
