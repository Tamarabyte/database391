#!/usr/bin/env python

"""
Deletes all tables and recreates them.
"""

import datetime
from app.config import SQLALCHEMY_DATABASE_URI, SERVE_FOLDER, WHOOSH_BASE
from app import db
from app.models import User, Person, Group, Group_List, Image, Popularity

import os

# Drop Tables
db.reflect()
db.drop_all()

# Create Tables
db.metadata.create_all(db.engine, tables=[
    User.__table__,
    Person.__table__,
    Group.__table__,
    Group_List.__table__,
    Image.__table__,
    Popularity.__table__
    ])

# Add Default Groups
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

# Add Admin
admin = User(
    user_name = "admin",
    password = User.hash_password("admin"),
    date_registered = datetime.date.today()
)

db.session.add(group1)
db.session.add(group2)
db.session.add(admin)
db.session.commit()

# Clear text indexes
indexFolder = WHOOSH_BASE + "/Image"
indexFiles = os.listdir(indexFolder)
for fileName in files:
    os.remove(indexFolder+"/"+indexFiles)

# Clear image cache
folderName = SERVE_FOLDER
files = os.listdir(folderName)
for fileName in files:
    os.remove(folderName+"/"+fileName)
