import datetime
import os
from flask import render_template, flash, redirect, url_for, request
from flask.ext.login import login_required, current_user
from sqlalchemy import func, desc, asc

from app import app, db, picture_views
from ..models import Image, Group, Group_List, Popularity
from ..forms.search_forms import InlineSearchForm

@app.route('/home/<page>', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home(page=1, search=None):
    form = InlineSearchForm()

    if request.method == "GET":
        form.searchSelect.data = "relavence"
    
    if form.validate_on_submit():
        page=1
        return redirect(url_for('home', search=form.searchText.data, order=form.searchSelect.data, before=form.dateBefore.data, after=form.dateAfter.data))

    search = request.args.get("search", None)
    order = request.args.get("order", "most views")
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    images = Image.query
    
    if current_user.user_name != "admin":
        images = images.outerjoin(Group, Group_List, Popularity) \
                .filter((Image.owner_name==current_user.user_name)
                    | (Image.permitted==1)
                    | (Group_List.friend_id==current_user.user_name))
    else:
        images = images.outerjoin(Popularity)
    
    if before is not None and after is not None:
        date1 = datetime.datetime.strptime(after, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(before, "%Y-%m-%d").date()
        images = images.filter(Image.timing > date1, Image.timing < date2)
    elif before is not None:
        date = datetime.datetime.strptime(before, "%Y-%m-%d").date()
        images = images.filter(Image.timing < date)
    elif after is not None:
        date = datetime.datetime.strptime(after, "%Y-%m-%d").date()
        images = images.filter(Image.timing > date)
    
    images = images.group_by(Image.photo_id)
    
    if order == "most views":
        images = images.order_by(desc(func.count(Popularity.viewed_by)), desc(Image.timing))
    elif order == "newest first":
        images = images.order_by(desc(Image.timing), desc(func.count(Popularity.viewed_by))) 
    elif order == "newest last":
        images = images.order_by(asc(Image.timing), desc(func.count(Popularity.viewed_by)))
    
    if search:
        images = images.whoosh_search(" and ".join(search), fields=('subject', 'place', 'description'),
                                      fieldboosts={"subject": 6.0, "place": 3.0})
        
    images = images.paginate(int(page), 20, False)
    
    if images.pages == 0 and search==None and before == None and after == None:
        return render_template('logged_in/no_pictures.html', title='My Pictures', current_user=current_user)
        
    if int(page) > images.pages and images.pages != 0:
        return redirect(url_for('home'))
    
    views = db.session.query(Popularity.photo_id, func.count(Popularity.viewed_by)) \
            .group_by(Popularity.photo_id).all()
    
    views_dict = {}
    for photo_id, count in views:
        views_dict[photo_id] = count

    query_string = ""
    if len(request.query_string)!=0:
        query_string = str(request.query_string)
    return render_template('logged_in/home.html', title='Home', current_user=current_user,
                           images=images, server_folder=app.config['SERVE_FOLDER'], views_dict=views_dict,
                           form=form, search=search, order=order, before=before, after=after)

@app.route('/home/picture/<from_page>/<page>/<id>', methods=['GET'])
@login_required
def picture_details(from_page, page, id):
    image = Image.query.get(id)
    
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)

    # redirect to the pictures page if the picture does not exist
    if image is None or (image.owner_name != current_user.user_name and image.permitted != 1 and current_user.user_name != "admin" and
        Group_List.query.filter_by(group_id=image.permitted, friend_id=current_user.user_name) is None):
        
        flash("Picture does not exist!")
        return redirect(url_for(app.config['FROM'][from_page]))
    
    picture_views.add_viewed_by(id)
    
    return render_template('logged_in/picture_details.html', title='Home', current_user=current_user,
                           image=image, page=page, server_folder=app.config['SERVE_FOLDER'], anchor="picture"+str(id),
                           from_page = app.config['FROM'][from_page], search=search, order=order, before=before, after=after)

@app.route('/home/picture/<from_page>/<page>/delete/<id>', methods=['GET'])
@login_required
def delete_picture_from_details(id, page, from_page):
    
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    picture = Image.query.get(id)
    
    # redirect to the pictures page if the picture does not exist
    if picture is None or picture.owner_name != current_user.user_name:
        flash("Picture does not exist!")
        return redirect(url_for(prev_page))
    
    confirmation_link = url_for('delete_picture_from_details_confirm', page=page, from_page=from_page, id=id, order=order, before=before, after=after)
    flash("Are you sure you want to delete this picture? "
          '<br><a href="{}" class="alert-link">'
          'I am sure.''</a>'.format(confirmation_link), "danger")

    return redirect(url_for('picture_details', id=id, from_page=from_page, page=page, search=search, order=order, before=before, after=after))

@app.route('/home/picture/<from_page>/<page>/delete/<id>/confirm', methods=['GET'])
@login_required
def delete_picture_from_details_confirm(page, id, from_page):
    
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    return picture_views.delete_confirm_helper(page, id, app.config['FROM'][from_page], search=search, order=order, before=before, after=after)