"""
Upload Forms
- Contains the form for uploading images/directories
"""

from flask_wtf import Form
from flask_login import current_user
from wtforms import StringField, FileField, TextAreaField, SelectField, validators
from ..models import User, Group

class UploadForm(Form):
    """ Used on the upload page to upload images or directories """

    # Image fields have specific length requirements
    length128Validator = validators.Length(max=128, message='*max 128 characters')
    length2048Validator = validators.Length(max=2048, message='*max 2048 characters')
    
    # Form fields
    permitted = SelectField('Allowed Group', coerce=int)
    subject = StringField('Title', validators=[length128Validator])
    place = StringField('Location', validators=[length128Validator])
    description = TextAreaField('Description', validators=[length2048Validator])
    image = FileField('Upload Images')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        # Possible groups a user can choose from are loaded into the permitted select
        groups = Group.query.filter(User.user_name == current_user.user_name, Group.group_name != "private").all()
        group_private = Group.query.filter(Group.group_name == "private").all()
        # Put the private group first
        self.permitted.choices = [(group.group_id, group.group_name) for group in group_private + groups]
        self.image_obj = None

    def validate(self):
        # Validate
        if not super(UploadForm, self).validate():
            return False

        # All is reserved for our admin queries
        if self.subject == "All Subjects":
            self.subject.errors.append('*invalid subject name')
            return False


        return True
