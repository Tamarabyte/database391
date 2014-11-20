import datetime
import re
from flask import flash
from flask.ext.wtf import Form
from flask.ext.login import current_user
from wtforms import StringField, FileField, TextAreaField, SelectField, BooleanField, SelectMultipleField, DateField, validators
from app import db
from ..models import User, Image, Group

class InlineSearchForm(Form):
    searchSelect = SelectField('Sort By', choices=(
        ("newest first", "Newest First"),
        ("newest last", "Newest Last"),
        ("most views", "Most Views"),
        ("relavence", "Relavence"),
        ))
    searchText = SelectMultipleField("Search Text", choices=[])
    dateBefore = StringField("Posted Before")
    dateAfter = StringField("Posted After")
    showSearch = BooleanField(default=False)
    
    
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        
        db_was_empty = False
        da_was_empty = False
        
        # Validate
        if self.dateBefore.data == "":
            self.dateBefore.data = datetime.date.today().strftime("%Y-%m-%d")
            db_was_empty = True
            

        if self.dateAfter.data == "":
            self.dateAfter.data = "2000-01-01"
            da_was_empty = True
        
        try:
            self.date1 = datetime.datetime.strptime(self.dateAfter.data, "%Y-%m-%d").date()
            self.date2 = datetime.datetime.strptime(self.dateBefore.data, "%Y-%m-%d").date()
        except ValueError:
            self.dateAfter.errors = ("*invalid date format (use yyyy-mm-dd)",)
            return False
        
        if self.date1 > self.date2:
            self.dateAfter.errors = ("*posted after must be earlier than posted before and today's date", )
            return False
        
        if db_was_empty:
            self.dateBefore.data = None
        if da_was_empty:
            self.dateAfter.data = None
            
        return True
