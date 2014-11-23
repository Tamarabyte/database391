"""
Admin Page Forms
- Contains the form for admin report generation.
"""
import datetime
from flask import flash
from flask_wtf import Form
from wtforms import StringField, BooleanField, SelectField, IntegerField
from ..models import User, Image

class AdminForm(Form):
    """Used on the admin page for report generation."""

    # For Fields
    user = SelectField('User')
    subject = SelectField("Title")
    hierarchy = SelectField("Time Hierarchy",
        choices=(("All Time", "All Time"),("Weekly", "Weekly"), ("Monthly", "Monthly"), ("Yearly", "Yearly")))
    dateBefore = StringField("To")
    dateAfter = StringField("From")
    showSearch = BooleanField(default=False)
    generate = IntegerField(default=1)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

        # Load subjects and users from database to populate select options
        users = ["All Users"] + [user.user_name for user in User.query.order_by(User.user_name).all()]

        image_query = Image.query.group_by(Image.subject).order_by(Image.subject).all()
        subjects = ["All Subjects"] + [image.subject for image in image_query]

        self.subject.choices = [["No Subjects", "Any Subject"]] + list(zip(subjects, subjects))
        self.user.choices = [["No Users", "Any User"]] + list(zip(users, users))

    def validate(self):
        self.showSearch.data = True

        if (self.user.data == "" and self.subject.data == "" and
            self.hierarchy.data == "" and self.dateBefore == "" and self.dateAfter == ""):

            self.hierarchy.errors = "Form cannot be empty."
            return False

        if self.user.data == "All Users" and self.subject.data == "All Subjects" \
            and self.hierarchy.data != "All Time":
            self.hierarchy.errors = ("""*hiearchy can't be 'All' for both Users and Titles when searching by Year/Week/Month
                                     (try 'All' for the result you want to display and 'Any' for the other)""",)
            return False

        # Validate date formats
        try:
            if self.dateAfter.data != "":
                date1 = datetime.datetime.strptime(self.dateAfter.data, "%Y-%m-%d").date()
            if self.dateBefore.data != "":
                date2 = datetime.datetime.strptime(self.dateBefore.data, "%Y-%m-%d").date()
        except ValueError:
            self.dateAfter.errors = ("*invalid date format (use yyyy-mm-dd)",)
            return False

        # Validate that dateAfter is < dateBefore
        if self.dateAfter.data != "" and self.dateBefore.data != "":
            if date1 > date2:
                self.dateAfter.errors = ("*posted after must be earlier than posted before and today's date", )
                return False

        if self.dateAfter.data == "":
            self.dateAfter.data = None
        if self.dateBefore.data == "":
            self.dateBefore.data = None

        self.generate.data = 1
        
        return True
