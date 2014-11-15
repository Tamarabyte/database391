#!/usr/bin/env python

from app.config import SQLALCHEMY_DATABASE_URI
from app import db
from app.models import User, Person, Group, Group_List, Image

db.reflect()
db.drop_all()
db.metadata.create_all(db.engine, tables=[
    User.__table__,
    Person.__table__,
    Group.__table__,
    Group_List.__table__,
    Image.__table__])
