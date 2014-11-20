import datetime
import re

from flask.ext.wtf import Form
from flask import flash
from flask.ext.login import current_user
from wtforms import StringField, SelectMultipleField, BooleanField, ValidationError, validators, SelectField
from wtforms.widgets import TextArea
from werkzeug.datastructures import MultiDict
from app import db
from ..models import User, Group, Group_List, Image

class AdminForm(Form):
    
    user = SelectField('User')
    subject = SelectField("Title")
    hierarchy = SelectField("Time Hierarchy", choices=(("", ""), ("Weekly", "Weekly"), ("Monthly", "Monthly"), ("Yearly", "Yearly")))
    dateBefore = StringField("Posted Before")
    dateAfter = StringField("Posted After")
    showSearch = BooleanField(default=False)
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        
        users = [""] + [user.user_name for user in User.query.all()]
        subjects = [""] + [image.subject for image in Image.query.filter(Image.subject != "").group_by(Image.subject).all()]
    
        self.subject.choices = zip(subjects, subjects)
        self.user.choices = zip(users, users)
