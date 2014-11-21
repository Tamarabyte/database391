"""
Database Models used by SQL Alchemy.
Tables are generated based on data in this file.
"""

import base64
from passlib.hash import md5_crypt

from app import db, app
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
import flask_whooshalchemy as whooshalchemy


class User(db.Model):
    """ ORM for the `users` table """

    __tablename__ = 'users'
    
    # Columns
    user_name= db.Column(db.VARCHAR(24), primary_key=True)
    password = db.Column(db.VARCHAR(34), nullable=False)
    date_registered = db.Column(db.Date)
    
    # Object relationship to follow with SQL Alchemy
    images = relationship("Image", backref="owner")
    groups = relationship("Group", backref="owner")
    group_lists = relationship("Group_List", backref="member")

    def __repr__(self):
        return '<User %r>' % (self.user_name)
    
    # Required by Flask-Login
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_name)
    
    # Validate that the password passed in matches the users hashed password
    def verify_password(self, password):
        return md5_crypt.verify(password, str(self.password))
    
    # Validate that the password reset key recieved in the url
    # matches the users hashed password
    def validatePasswordResetKey(self, hash):
        try:
            decoded = base64.urlsafe_b64decode(hash).decode('utf-8')
            result = md5_crypt.verify(str(self.password), decoded)
            return result
        except ValueError:
            return False
    
    # User activation uses a hashed username as the url string
    # We know which user to activate based on whether the hash
    # matches a hash of the user name
    def validateActivationKey(self, hash):
        try:
            decoded = base64.urlsafe_b64decode(hash).decode('utf-8')
            result = md5_crypt.verify(str(self.user_name), decoded)
            return result
        except ValueError:
            return False
 
    def hash_password(password):
        return md5_crypt.encrypt(password)

    def createActivationKey(username):
        crypt = md5_crypt.encrypt(username)
        return base64.urlsafe_b64encode(crypt.encode('utf-8'))

    def createPasswordResetKey(password):
        crypt = md5_crypt.encrypt(password)
        return base64.urlsafe_b64encode(crypt.encode('utf-8'))
    


class Person(db.Model):
    """ ORM for the `persons` table """

    __tablename__ = 'persons'
    
    # Columns
    user_name= db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), primary_key=True)
    first_name = db.Column(db.VARCHAR(24), nullable=False)
    last_name = db.Column(db.VARCHAR(24), nullable=False)
    address = db.Column(db.VARCHAR(128), nullable=False)
    email = db.Column(db.VARCHAR(128), nullable=False, unique=True)
    phone = db.Column(db.CHAR(10), nullable=False)

    def __repr__(self):
        return '<Person %r %r>' % (self.first_name, self.last_name)
    
class Group(db.Model):
    """ ORM for the `group` table """

    __tablename__ = 'groups'
    
    # Columns
    group_id= db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), nullable=True)
    group_name = db.Column(db.VARCHAR(24), nullable=False)
    date_created = db.Column(db.Date, nullable=False)
    
    # Object relationships to follow with sqlalchemy
    images = relationship("Image", backref="group")
    group_lists = relationship("Group_List", backref="group")
    
    __table_args__ = (UniqueConstraint('user_name', 'group_name'),)

    def __repr__(self):
        return '<Group %r %r>' % (self.user_name, self.group_name)

class Group_List(db.Model):
    """ ORM for the `group_lists` table """

    __tablename__ = 'group_lists'
    
    # Columns
    group_id = db.Column(db.Integer, ForeignKey('groups.group_id'), primary_key=True)
    friend_id = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), primary_key=True)
    date_added = db.Column(db.Date, nullable=False)
    notice = db.Column(db.VARCHAR(1024), nullable=True)
    
    def __repr__(self):
        return '<Group List %r %r>' % (self.group_id, self.friend_id)

class Image(db.Model):
    """ ORM for the `images` table """

    __tablename__ = 'images'
    # Add a text index to these fields
    __searchable__ = ['subject', 'place', 'description']
    
    # Columns
    photo_id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), nullable=False)
    permitted = db.Column(db.Integer, ForeignKey('groups.group_id'), nullable=False)
    subject = db.Column(db.VARCHAR(128), nullable=True)
    place = db.Column(db.VARCHAR(128), nullable=True)
    timing = db.Column(db.Date, nullable=False)
    description = db.Column(db.VARCHAR(2048), nullable=True)
    thumbnail = db.Column(db.BLOB, nullable=False)
    photo = db.Column(db.BLOB, nullable=False)

    # Relationship to follow with sqlalchemy
    viewed_by = relationship("Popularity", backref="image")
    
    def __repr__(self):
        return '<Image %r %r>' % (self.photo_id, self.owner_name)

# Register indexes on images
whooshalchemy.whoosh_index(app, Image)

class Popularity(db.Model):
    """
    ORM for the `popularity` table. This table stores a combination of photo_id/viewed_by for each
    user that has viewed an image.
    """

    __tablename__ = 'popularities'
    
    # Columns
    photo_id = db.Column(db.Integer, ForeignKey('images.photo_id'), primary_key=True, nullable=False)
    viewed_by = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), primary_key=True, nullable=False)
       

    def __repr__(self):
        return '<Popularity %r %r>' % (self.photo_id, self.viewed_by)
