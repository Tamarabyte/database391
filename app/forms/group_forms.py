"""
Group Forms
- Contains the form new groups.
- Contains the form for editing groups.
- Contains the form for editing group-lists.
"""

import datetime
from flask_wtf import Form
from flask_login import current_user
from wtforms import StringField, SelectMultipleField, BooleanField, validators
from wtforms.widgets import TextArea
from ..models import User, Group, Group_List

class NewGroup(Form):
    """ Used on the groups page when creating a new group. """

    # Form fields
    group_name = StringField('Group Name',
        validators=[validators.Required('*required'),validators.Length(max=24, message='*max 24 characters')])
    notice = StringField("Short description about the friends you're adding:", widget=TextArea(),
        validators=[validators.Length(max=1024, message='*max 1024 characters')])
    friends = SelectMultipleField()
    # Boolean value used by JS to determine whether to hide/show the form
    showForm = BooleanField(default=False)


    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

        # Initialize select list options for the 'friends' select
        users = User.query.filter(User.user_name != current_user.user_name, User.date_registered != None).all()
        self.friends.choices = [(user.user_name, user.user_name) for user in users]

        # initialize save group and group_lists in the form object
        self.group = None
        self.group_lists = []


    def validate(self):
        self.showForm.data = True

        # Validate
        if not super(NewGroup, self).validate():
            return False

        # No groups with the same user and same name
        group = Group.query.filter_by(user_name=current_user.user_name, group_name=self.group_name.data).first()
        if group is not None:
            self.group_name.errors.append('*group already exists')
            return False

        # Validation successful! Build Group and Group_List objects
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
    """ Used on the group page when modifying an existing group. """

    # Form Fields
    group_name = StringField('Group Name', validators=[validators.Required('*required'),
        validators.Length(max=24, message='*max 24 characters')])
    notice = StringField("Short description about the friends you're adding:", widget=TextArea(),
        validators=[validators.Length(max=1024, message='*max 1024 characters')])
    friends = SelectMultipleField()
    # Boolean value used by JS to determine which portions of the form to hide/show
    showAddFriendsForm = BooleanField(default=False)
    showChangeNameForm = BooleanField(default=False)

    def __init__(self, existing_group, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

        # Set of select lists and grab group_lists to display on page
        self.group = existing_group
        self.group_lists = Group_List.query.filter_by(group_id=existing_group.group_id).all()

        users = User.query.filter(
            User.user_name != current_user.user_name,
            User.date_registered != None,
            ).all()

        user_names = [user.user_name for user in users]
        group_list_users = [group_list.friend_id for group_list in self.group_lists]

        self.friends.choices = [(name, name) for name in user_names if name not in group_list_users]


    def validate(self):

        # Validate
        if not super(ExistingGroup, self).validate():
            return False

        # No groups with the same user and same name
        group = Group.query.filter_by(user_name=current_user.user_name, group_name=self.group_name.data).first()
        if group is not None and group.group_name != self.group.group_name:
            self.group_name.errors.append('*group with same name already exists')
            return False

        return True


class ExistingGroupList(Form):
    """ Used on the group lists page when editing an existing group list. """

    # Form field
    notice = StringField("Why is this friend is part of this group?", widget=TextArea(), validators=[validators.Length(max=1024, message='*max 1024 characters')])

    def __init__(self, existing_group, existing_group_list, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        # Fill in form with existing fields
        self.group_list = existing_group_list
        self.group = existing_group

    def validate(self):

        # Validate
        if not super(ExistingGroupList, self).validate():
            return False

        # Update group list with notice field data
        self.group_list.notice = self.notice.data

        return True
