import base64
from passlib.hash import md5_crypt

from app import db
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint, ForeignKey
from sqlalchemy.orm import relationship


class User(db.Model):
    __tablename__ = 'users'
    
    user_name= db.Column(db.VARCHAR(24), primary_key=True)
    password = db.Column(db.VARCHAR(34), nullable=False)
    date_registered = db.Column(db.Date)
    
    group_lists = relationship("Group_List")

    def __repr__(self):
        return '<User %r>' % (self.user_name)
    
    # required by Flask-Login
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_name)
    
    def verify_password(self, password):
        return md5_crypt.verify(password, str(self.password))
    
    def validateActivationKey(self, hash):
        try:
            decoded = base64.urlsafe_b64decode(hash).decode('utf-8')
            result = md5_crypt.verify(str(self.user_name), decoded)
            return result
        except ValueError:
            return False
    
    def validatePasswordResetKey(self, hash):
        try:
            decoded = base64.urlsafe_b64decode(hash).decode('utf-8')
            result = md5_crypt.verify(str(self.password), decoded)
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
    __tablename__ = 'persons'
    
    user_name= db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), primary_key=True)
    first_name = db.Column(db.VARCHAR(24), nullable=False)
    last_name = db.Column(db.VARCHAR(24), nullable=False)
    address = db.Column(db.VARCHAR(128), nullable=False)
    email = db.Column(db.VARCHAR(128), nullable=False, unique=True)
    phone = db.Column(db.CHAR(10), nullable=False)

    def __repr__(self):
        return '<Person %r %r>' % (self.first_name, self.last_name)
    
class Group(db.Model):
    __tablename__ = 'groups'
    
    group_id= db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), nullable=False)
    group_name = db.Column(db.VARCHAR(24), nullable=False)
    date_created = db.Column(db.Date, nullable=False)
    
    __table_args__ = (UniqueConstraint('user_name', 'group_name'),)

    def __repr__(self):
        return '<Group %r %r>' % (self.user_name, self.group_name)

class Group_List(db.Model):
    __tablename__ = 'group_lists'
    
    group_id = db.Column(db.Integer, ForeignKey('groups.group_id'), primary_key=True)
    friend_id = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), primary_key=True)
    date_added = db.Column(db.Date, nullable=False)
    notice = db.Column(db.VARCHAR(1024), nullable=True)
    
    def __repr__(self):
        return '<Group List %r %r>' % (self.group_id, self.friend_id)

class Image(db.Model):
    __tablename__ = 'images'
    
    photo_id = db.Column(db.Integer, primary_key=True)
    owner_name = db.Column(db.VARCHAR(24), ForeignKey('users.user_name'), nullable=False)
    permitted = db.Column(db.Integer, ForeignKey('groups.group_id'), nullable=False)
    subject = db.Column(db.VARCHAR(128), nullable=False)
    place = db.Column(db.VARCHAR(128), nullable=False)
    timing = db.Column(db.Date, nullable=False)
    description = db.Column(db.VARCHAR(2048), nullable=False)
    thumbnail = db.Column(db.BLOB, nullable=False)
    photo = db.Column(db.BLOB, nullable=False)
        

    def __repr__(self):
        return '<Image %r %r>' % (self.phot_id, self.owner_name)
