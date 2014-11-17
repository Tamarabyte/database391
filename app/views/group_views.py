import datetime

from flask import render_template, flash, redirect, url_for, request
from flask.ext.login import login_required, current_user
from flask.ext.mail import Message

from app import app, db
from ..models import User, Person, Group, Group_List
from ..forms.group_forms import NewGroup, ExistingGroup, ExistingGroupList

@app.route('/my/groups', methods=['GET', 'POST'])
@login_required
def groups():
    form = NewGroup()
    
    if form.validate_on_submit():
        # commit the new group
        db.session.add(form.group)
        db.session.commit()
        
        # commit the associated group lists
        for group_list in form.group_lists:
            group_list.group_id = form.group.group_id
            db.session.add(group_list)
            db.session.commit()
        # reset the form
        return redirect('/my/groups')
    
    # get the existing groups
    existing_groups = Group.query.filter_by(user_name=current_user.user_name).all()
           
    return render_template('logged_in/my_groups.html', title='My Groups',
                           current_user=current_user, form=form, existing_groups=existing_groups)

@app.route('/my/groups/delete/<group_id>', methods=['GET'])
@login_required
def delete_group(group_id):
    # filter by username to ensure the user is the owner of the group
    existing_group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    
    # redirect to the group page if the group does not exist
    if existing_group is None:
        flash("Group does not exist!")
        return redirect('/my/groups')
    
    flash("Are you sure you want to delete '{}'? "
          '<br><a href="/my/groups/delete/{}/confirmed" class="alert-link">'
          'I am sure!''</a>'.format(existing_group.group_name, existing_group.group_id), "danger")
    
    return redirect('/my/groups')

@app.route('/my/groups/delete/<group_id>/confirmed', methods=['GET'])
@login_required
def delete_group_confirmed(group_id):
    # filter by username to ensure the user is the owner of the group
    existing_group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    existing_group_lists = Group_List.query.filter_by(group_id = group_id).all()
    
    # redirect to the group page if the group does not exist
    if existing_group is None:
        flash("Group does not exist!")
        return redirect('/my/groups')
    
    for group_list in existing_group_lists:
        db.session.delete(group_list)
    db.session.commit()
    
    db.session.delete(existing_group)
    db.session.commit()
    
    return redirect('/my/groups')

@app.route('/my/groups/<group_id>', methods=['GET', 'POST'])
@login_required
def existing_group(group_id):
    # filter by username to ensure the user is the owner of the group
    existing_group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    
    # redirect to the group page if the group does not exist
    if existing_group is None:
        flash("Group does not exist!")
        return redirect('/my/groups')
    
    form = ExistingGroup(existing_group)
    
    if request.method == "GET":
        form.group_name.data = existing_group.group_name
    
    # commit changes
    if form.validate_on_submit():
        flash("Successfully updated group!".format(form.group_name.data), "success")
        existing_group.group_name = form.group_name.data
        for friend_id in form.friends.data:
            new_group_list = Group_List(
                group_id = existing_group.group_id,
                friend_id=friend_id,
                notice=form.notice.data,
                date_added=datetime.date.today()
                )
            db.session.add(new_group_list)
        db.session.commit()
        
        # reset the form
        return redirect('/my/groups/{}'.format(existing_group.group_id))
    
    return render_template('logged_in/group.html', title='My Groups', current_user=current_user, form=form, group=existing_group)


@app.route('/my/groups/<group_id>/<user_name>', methods=['GET', 'POST'])
@login_required
def existing_group_list(group_id, user_name):
    
    # filter by username to ensure the user is the owner of the group
    existing_group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    group_list = Group_List.query.filter_by(group_id=group_id, friend_id=user_name).first()
    
    # redirect to the my groups page if the group does not exist
    if existing_group is None:
        flash("Group does not exist!")
        return redirect('/my/groups')
    
    # redirect to the group page if the group_list does not exist
    if group_list is None:
        flash("Friend '{}' is not part of group!".format(user_name))
        return redirect('/my/groups/{}'.format(group_id));
    
    form = ExistingGroupList(existing_group, group_list)
    
    if request.method == "GET":
        form.notice.data = group_list.notice
    
    # commit changes
    if form.validate_on_submit():
        flash("Successfully updated friend!", "success")
        db.session.commit();
        
    return render_template('logged_in/group_list.html', title='My Groups', current_user=current_user, form=form)

@app.route('/my/groups/<group_id>/<user_name>/delete', methods=['GET'])
@login_required
def delete_group_list(group_id, user_name):
    # filter by username to ensure the user is the owner of the group
    existing_group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    group_list = Group_List.query.filter_by(group_id=group_id, friend_id=user_name).first()
    
    # redirect to the group page if the group does not exist
    if existing_group is None:
        flash("Group does not exist!")
        return redirect('/my/groups')
        # redirect to the group page if the group_list does not exist
    
    if group_list is None:
        flash("Friend '{}' is not part of group!".format(user_name))
        return redirect('/my/groups/{}'.format(group_id));
    
    flash("Are you sure you want to remove '{0}' from this group? "
          '<br><a href="/my/groups/{1}/{0}/delete/confirmed" class="alert-link">'
          'I am sure!''</a>'.format(group_list.friend_id, existing_group.group_id), "danger")
    
    return redirect('/my/groups/{}'.format(group_id))

@app.route('/my/groups/<group_id>/<user_name>/delete/confirmed', methods=['GET'])
@login_required
def delete_group_list_confirmed(group_id, user_name):
    # filter by username to ensure the user is the owner of the group
    existing_group = Group.query.filter_by(user_name=current_user.user_name, group_id=group_id).first()
    group_list = Group_List.query.filter_by(group_id=group_id, friend_id=user_name).first()
    
    # redirect to the group page if the group does not exist
    if existing_group is None:
        flash("Group does not exist!")
        return redirect('/my/groups')
        # redirect to the group page if the group_list does not exist
    
    if group_list is None:
        flash("Friend '{}' is not part of group!".format(user_name))
        return redirect('/my/groups/{}'.format(group_id));
    
    db.session.delete(group_list)
    db.session.commit()

    return redirect('/my/groups/{}'.format(group_id))