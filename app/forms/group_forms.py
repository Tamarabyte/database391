from flask.ext.wtf import Form
from wtforms import StringField, SelectMultipleField, ValidationError, validators
from wtforms.widgets import TextArea
import re

from ..models import Group, Group_List

class NewGroup(Form):


    group_name = StringField('Group Name', validators=[validators.Required('*required'),])
    notice = StringField('Description', widget=TextArea(), validators=[validators.Required('*required'),])
    friends = SelectMultipleField(validators=[validators.Required('*required'),])
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.choices = [('tam', 'tam'.capitalize()), ('maciej', 'maciej'.capitalize())]
        self.friends.choices = self.choices
        
        self.group = None
        self.group_list = None
        

    def validate(self):

        # Validate
        if not super(NewGroup, self).validate():
            return False

        return True
    
class ExistingGroup(Form):


    group_name = StringField('Group Name', validators=[validators.Required('*required'),])
    notice = StringField('Description', widget=TextArea(), validators=[validators.Required('*required'),])
    friends = SelectMultipleField(validators=[validators.Required('*required'),])
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.choices = [('tam', 'tam'.capitalize()), ('maciej', 'maciej'.capitalize())]
        self.defaults = ['tam']
        self.friends.choices = self.choices
        self.friends.data = self.defaults
        
        self.group = None
        self.group_list = None
        

    def validate(self):

        # Validate
        if not super(NewGroup, self).validate():
            return False

        return True
    
