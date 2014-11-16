import datetime
import re

from flask.ext.wtf import Form
from flask import flash
from flask.ext.login import current_user
from wtforms import StringField, SelectMultipleField, BooleanField, ValidationError, validators
from wtforms.widgets import TextArea
from werkzeug.datastructures import MultiDict
from app import db
from ..models import User, Group, Group_List

class NewGroup(Form):

    group_name = StringField('Group Name', validators=[validators.Required('*required'), validators.Length(max=24, message='*max 24 characters')])
    notice = StringField("Short description about the friends you're adding:", widget=TextArea(), validators=[validators.Length(max=1024, message='*max 1024 characters')])
    friends = SelectMultipleField()
    showForm = BooleanField(default=False)

    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        
        users = User.query.filter(User.user_name != current_user.user_name, User.date_registered != None).all()
        
        self.friends.choices =  [(user.user_name, user.user_name.capitalize()) for user in users]
        
        distinct_notices = Group_List.query.join(Group).filter(
            Group.user_name == current_user.user_name,
            Group_List.notice != "",
            Group_List.notice is not None,
            ).group_by(Group_List.notice)
        
        self.notice_list = sorted([group_list.notice for group_list in distinct_notices], key=str.lower)
        self.group = None
        self.group_lists = []
        

    def validate(self):

        # Validate
        if not super(NewGroup, self).validate():
            return False
        
        # No groups with the same user and same name
        group = Group.query.filter_by(user_name=current_user.user_name, group_name=self.group_name.data).first()
        if group is not None:
            self.group_name.errors.append('*group already exists')
            return False
    
    
        self.group = Group(
            user_name=current_user.user_name,
            group_name=self.group_name.data,
            date_created=datetime.date.today()
        )
        
        for friend_id in self.friends.data:
           self.group_lists.append(
                Group_List(
                friend_id=friend_id,
                notice=self.notice.data,
                date_added=datetime.date.today()
                )
            )
           
        return True
    
class ExistingGroup(Form):

    group_name = StringField('Group Name', validators=[validators.Required('*required'), validators.Length(max=24, message='*max 24 characters')])
    notice = StringField("Short description about the friends you're adding:", widget=TextArea(), validators=[validators.Length(max=1024, message='*max 1024 characters')])
    friends = SelectMultipleField()
    showAddFriendsForm = BooleanField(default=False)
    showChangeNameForm = BooleanField(default=False)
    
    def __init__(self, existing_group, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        
        # set values
        self.group = existing_group
        
        distinct_notices = Group_List.query.join(Group).filter(
            Group.user_name == current_user.user_name,
            Group_List.notice != "",
            Group_List.notice is not None,
            ).group_by(Group_List.notice)
        
        self.notice_list = sorted([group_list.notice for group_list in distinct_notices], key=str.lower)
        self.group_lists = Group_List.query.filter_by(group_id = existing_group.group_id).all()
        
        users = User.query.filter(
            User.user_name != current_user.user_name,
            User.date_registered != None,
            ).all()
        
        user_names = [user.user_name for user in users]
        group_list_users = [group_list.friend_id for group_list in self.group_lists]
        
        self.friends.choices = [(name, name.capitalize()) for name in user_names if (name not in group_list_users)]
        

    def validate(self):

        # Validate
        if not super(ExistingGroup, self).validate():
            return False
        
        # No groups with the same user and same name
        group = Group.query.filter_by(user_name=current_user.user_name, group_name=self.group_name.data).first()
        if group is not None and group.group_name != self.group.group_name:
            flash("group name: " + group.group_name + " group name data: " + self.group_name.data)
            self.group_name.errors.append('*group with same name already exists')
            return False
        
        



        existing_friend_ids = [group_list.friend_id for group_list in self.group_lists]
        for friend_id in self.friends.data:
            if friend_id not in existing_friend_ids:
                
                new_group_list = Group_List(
                    group_id = self.group.group_id,
                    friend_id=friend_id,
                    notice=self.notice.data,
                    date_added=datetime.date.today()
                    )
                self.group_lists.append(new_group_list)
                db.session.add(new_group_list)
        db.session.commit()
        return True
    
