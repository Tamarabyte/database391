"""
Picture Forms
- Contains the form for editing Image fields
"""
import datetime
from flask import flash
from flask_wtf import Form
from flask_login import current_user
from wtforms import StringField, TextAreaField, SelectField, validators, BooleanField
from ..models import User, Group

class PictureForm(Form):
    """ Used on the picture page to for existing images owned by the user """

    length128Validator = validators.Length(max=128, message='*max 128 characters')
    length2048Validator = validators.Length(max=2048, message='*max 128 characters')

    # Form Fields
    permitted = SelectField('Allowed Group', coerce=int, validators=[validators.Required('*required')])
    subject = StringField('Title', validators=[length128Validator])
    place = StringField('Location', validators=[length128Validator])
    description = TextAreaField('Description', validators=[length2048Validator])
    # Only editable by the admin
    timing = StringField("Date Added (Only Editable for Admin)")
    # Used by JS to determine whether to show/hide the form
    showForm = BooleanField(default=False)

    def __init__(self, picture, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        # Load user's groups into the permitted select
        groups = Group.query.filter(User.user_name == current_user.user_name).all()
        self.permitted.choices = [(group.group_id, group.group_name) for group in groups]
        self.image_obj = picture


    def validate(self):
        # Validate
        if not super(PictureForm, self).validate():
            return False

        # All is reserved for our admin queries
        if self.subject == "All Subjects" or self.subject == "No Subjects":
            self.subject.errors.append('*invalid subject name')
            return False

        # Validation successful! Update the image with form data.
        self.image_obj.permitted = self.permitted.data
        self.image_obj.subject = self.subject.data
        self.image_obj.place = self.place.data
        self.image_obj.description = self.description.data

        if current_user.user_name == "admin":
            try:
                date = datetime.datetime.strptime(self.timing.data, "%Y-%m-%d").date()
            except ValueError:
                self.timing.errors = ("*invalid date format (use yyyy-mm-dd)",)
                return False

            self.image_obj.timing = self.timing.data

        return True
