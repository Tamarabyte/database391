import datetime
import re
from flask import flash
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import StringField, FileField, TextAreaField, SelectField, validators, BooleanField
from app import db
from ..models import User, Image, Group

class PictureForm(Form):
    
    length128Validator = validators.Length(max=128, message='*max 128 characters')
    length2048Validator = validators.Length(max=2048, message='*max 128 characters')
    
    permitted = SelectField('Allowed Group', coerce=int, validators=[validators.Required('*required')])
    subject = StringField('Title', validators=[length128Validator])
    place = StringField('Location', validators=[length128Validator])
    description = TextAreaField('Description', validators=[length2048Validator])
    showForm = BooleanField(default=False)
    
    def __init__(self, picture, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        groups = Group.query.filter(User.user_name == current_user.user_name).all();
        self.permitted.choices = [(group.group_id, group.group_name.capitalize()) for group in groups]
        self.image_obj = picture
        
        
    def validate(self):
        # Validate
        if not super(PictureForm, self).validate():
            return False
        
        self.image_obj.permitted = self.permitted.data
        self.image_obj.subject = self.subject.data
        self.image_obj.place = self.place.data
        self.image_obj.description = self.description.data
        
        return True;
    
