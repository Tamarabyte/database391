"""
Admin Page Forms
- Contains the form for admin report generation.
"""

from flask_wtf import Form
from wtforms import StringField, BooleanField, SelectField
from ..models import User, Image

class AdminForm(Form):
    """Used on the admin page for report generation."""

    # For Fields
    user = SelectField('User')
    subject = SelectField("Title")
    hierarchy = SelectField("Time Hierarchy",
        choices=(("", ""),("Weekly", "Weekly"), ("Monthly", "Monthly"), ("Yearly", "Yearly")))
    dateBefore = StringField("Posted Before")
    dateAfter = StringField("Posted After")
    showSearch = BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

        # Load subjects and users from database to populate select options
        users = ["", "All Users"] + [user.user_name for user in User.query.order_by(User.user_name).all()]

        image_query = Image.query.filter(Image.subject != "").group_by(Image.subject).order_by(Image.subject).all()
        subjects = ["", "All Subjects"] + [image.subject for image in image_query]

        self.subject.choices = zip(subjects, subjects)
        self.user.choices = zip(users, users)
        