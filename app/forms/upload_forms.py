import datetime
import re
from flask import flash
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import StringField, FileField, TextAreaField, SelectField, validators
from app import db
from ..models import User, Image, Group

class UploadForm(Form):
    
    length128Validator = validators.Length(max=128, message='*max 128 characters')
    length2048Validator = validators.Length(max=2048, message='*max 128 characters')
    
    permitted = SelectField('Allowed Groups', coerce=int)
    subject = StringField('Subject', validators=[length128Validator])
    place = StringField('Location', validators=[length128Validator])
    description = TextAreaField('Description', validators=[length2048Validator])
    image = FileField('Upload Images')
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        groups = Group.query.filter(User.user_name == current_user.user_name).all();
        self.permitted.choices = [(group.group_id, group.group_name) for group in groups]
        self.image_obj = None
        
    def validate(self):
        # Validate
        if not super(UploadForm, self).validate():
            return False
        
        return True;
    
