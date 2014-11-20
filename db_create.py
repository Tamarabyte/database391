#!/usr/bin/env python

import datetime
from app.config import SQLALCHEMY_DATABASE_URI
from app import db
from app.models import User, Person, Group, Group_List, Image, Popularity

db.reflect()
db.drop_all()
db.metadata.create_all(db.engine, tables=[
    User.__table__,
    Person.__table__,
    Group.__table__,
    Group_List.__table__,
    Image.__table__,
    Popularity.__table__])

group1 = Group(
    group_id = 1,
    group_name = 'public',
    date_created = datetime.date.today(),
)

group2 = Group(
    group_id = 2,
    group_name = 'private',
    date_created = datetime.date.today()
)


db.session.add(group1)
db.session.add(group2)
db.session.commit()
