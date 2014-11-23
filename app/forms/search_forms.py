"""
Search Forms
- Contains the form for searching images
"""

import datetime
from flask_wtf import Form
from wtforms import StringField, SelectField, BooleanField, SelectMultipleField

class InlineSearchForm(Form):
    """ Used on the home page to search and reorder images. """

    # Form fields
    searchSelect = SelectField('Sort By', choices=(
        ("newest first", "Newest First"),
        ("newest last", "Newest Last"),
        ("most views", "Most Views"),
        ("relavence", "Relavence"),
        ))
    searchText = SelectMultipleField("Search Text", choices=[])
    dateBefore = StringField("To")
    dateAfter = StringField("From")
    # Used by JS to determine whether to hide/show the form
    showSearch = BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.date1 = None
        self.date2 = None

    def validate(self):

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


        return True
