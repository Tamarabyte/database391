"""
Holds views for group pages and helper functions for group pages.
"""

import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import app, db
from ..models import Group, Group_List
from ..forms.group_forms import NewGroup, ExistingGroup, ExistingGroupList

@app.route('/my/groups', methods=['GET', 'POST'])
@login_required
def groups():
    """ This view handles the submission of new groups, and serves up the My Groups page. """

    form = NewGroup()
    
    if form.validate_on_submit():
        # Commit the new group
        db.session.add(form.group)
        db.session.commit()
        
        # Commit the associated group lists
        for group_list in form.group_lists:
            group_list.group_id = form.group.group_id
            db.session.add(group_list)
            db.session.commit()
        # Reset the form
        return redirect(url_for('groups'))
    
    # Get the existing groups
    existing_groups = Group.query.filter_by(user_name=current_user.user_name).all()

    # Render the my_groups.html template with the given variables
    return render_template('logged_in/my_groups.html', title='My Groups',
                           current_user=current_user, form=form, existing_groups=existing_groups)


@app.route('/my/groups/delete/<group_id>', methods=['GET'])
@login_required
def delete_group(group_id):
    """ This view displays a confirmation when a user deletes a group. """

    # Filter by username to ensure the user is the owner of the group
    group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()

    # Redirect to the group page if the group does not exist
    if group is None:
        flash("Group does not exist!")
        return redirect(url_for('groups'))

    # Construct confirmation to show when a user deletes a group
    flash("Are you sure you want to delete '{}'? "
          '<br><a href="/my/groups/delete/{}/confirmed" class="alert-link">'
          'I am sure!''</a>'.format(group.group_name, group.group_id), "danger")
    
    return redirect(url_for('groups'))


@app.route('/my/groups/delete/<group_id>/confirmed', methods=['GET'])
@login_required
def delete_group_confirmed(group_id):
    """ This view handles the deletion of a group and it's associated group_lists """

    # Filter by username to ensure the user is the owner of the group
    group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    existing_group_lists = Group_List.query.filter_by(group_id = group_id).all()
    
    # Redirect to the group page if the group does not exist
    if group is None:
        flash("Group does not exist!")
        return redirect(url_for('groups'))

    # Delete each group_list associated with the group
    for group_list in existing_group_lists:
        db.session.delete(group_list)
    db.session.commit()
    
    # Delete the group
    db.session.delete(group)
    db.session.commit()
    
    return redirect(url_for('groups'))


@app.route('/my/groups/<group_id>', methods=['GET', 'POST'])
@login_required
def existing_group(group_id):
    """This view displays information about an existing group.
    And the form for adding/removing group_lists"""

    # Filter by username to ensure the user is the owner of the group
    group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()

    # Redirect to the group page if the group does not exist
    if group is None:
        flash("Group does not exist!")
        return redirect(url_for('groups'))

    form = ExistingGroup(group)
    
    if request.method == "GET":
        form.group_name.data = group.group_name

    # Commit changes
    if form.validate_on_submit():
        flash("Successfully updated group!", "success")
        group.group_name = form.group_name.data

        # Commit each group list submitted
        for friend_id in form.friends.data:
            new_group_list = Group_List(
                group_id = group.group_id,
                friend_id=friend_id,
                notice=form.notice.data,
                date_added=datetime.date.today()
                )
            db.session.add(new_group_list)
        db.session.commit()
        
        # Reset the form
        return redirect(url_for('existing_group', group_id=group.group_id))
    
    return render_template('logged_in/group.html', title='My Groups',
                           current_user=current_user, form=form, group=group)


@app.route('/my/groups/<group_id>/<user_name>', methods=['GET', 'POST'])
@login_required
def existing_group_list(group_id, user_name):
    """Displays information about an existing Group List. Shows form for editting a group_list."""
    
    # Filter by username to ensure the user is the owner of the group
    group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()

    # Redirect to the my groups page if the group does not exist
    if group is None:
        flash("Group does not exist!")
        return redirect('groups')

    group_list = Group_List.query.filter_by(group_id=group_id, friend_id=user_name).first()
    
    # Redirect to the group page if the group_list does not exist
    if group_list is None:
        flash("Friend '{}' is not part of group!".format(user_name))
        return redirect(url_for('existing_group', group_id = group_id))
    
    form = ExistingGroupList(group, group_list)

    if request.method == "GET":
        form.notice.data = group_list.notice

    # Commit changes
    if form.validate_on_submit():
        flash("Successfully updated friend!", "success")
        db.session.commit()

    return render_template('logged_in/group_list.html', title='My Groups', current_user=current_user, form=form)


@app.route('/my/groups/<group_id>/<user_name>/delete', methods=['GET'])
@login_required
def delete_group_list(group_id, user_name):
    """ This view displays a confirmation when a user deletes a group_list. """

    # Filter by username to ensure the user is the owner of the group
    group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    group_list = Group_List.query.filter_by(group_id=group_id, friend_id=user_name).first()
    
    # Redirect to the groups page if the group does not exist
    if group is None:
        flash("Group does not exist!")
        return redirect(url_for('groups'))

    # Redirect to the group page if the group_list does not exist
    if group_list is None:
        flash("Friend '{}' is not part of group!".format(user_name))
        return redirect(url_for('existing_group', group_id = group_id))
    
    # Confirmation message
    flash("Are you sure you want to remove '{0}' from this group? "
          '<br><a href="/my/groups/{1}/{0}/delete/confirmed" class="alert-link">'
          'I am sure.''</a>'.format(group_list.friend_id, group.group_id), "danger")

    return redirect(url_for('existing_group', group_id = group_id))


@app.route('/my/groups/<group_id>/<user_name>/delete/confirmed', methods=['GET'])
@login_required
def delete_group_list_confirmed(group_id, user_name):
    """ This view handles the deletion of a group_list """

    # Filter by username to ensure the user is the owner of the group
    group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()

    # redirect to the group page if the group does not exist
    if group is None:
        flash("Group does not exist!")
        return redirect(url_for('groups'))

    group_list = Group_List.query.filter_by(group_id=group_id, friend_id=user_name).first()
    # Redirect to the group page if the group_list does not exist
    if group_list is None:
        flash("Friend '{}' is not part of group!".format(user_name))
        return redirect(url_for('existing_group', group_id=group_id))

    db.session.delete(group_list)
    db.session.commit()

    return redirect(url_for('existing_group', group_id=group_id))
