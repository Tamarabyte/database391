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
    dateBefore = StringField("Posted Before")
    dateAfter = StringField("Posted After")
    # Used by JS to determine whether to hide/show the form
    showSearch = BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.date1 = None
        self.date2 = None

    def validate(self):

        db_was_empty = False
        da_was_empty = False

        # Empty before dates validate using the current date
        if self.dateBefore.data == "":
            self.dateBefore.data = datetime.date.today().strftime("%Y-%m-%d")
            db_was_empty = True

        # Empty after dates validate using a date before the database was created
        if self.dateAfter.data == "":
            self.dateAfter.data = "2000-01-01"
            da_was_empty = True

        # Validate date formats
        try:
            self.date1 = datetime.datetime.strptime(self.dateAfter.data, "%Y-%m-%d").date()
            self.date2 = datetime.datetime.strptime(self.dateBefore.data, "%Y-%m-%d").date()
        except ValueError:
            self.dateAfter.errors = ("*invalid date format (use yyyy-mm-dd)",)
            return False

        # Validate that dateAfter is < dateBefore
        if self.date1 > self.date2:
            self.dateAfter.errors = ("*posted after must be earlier than posted before and today's date", )
            return False

        if db_was_empty:
            self.dateBefore.data = None
        if da_was_empty:
            self.dateAfter.data = None

        return True
