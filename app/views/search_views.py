"""
Contains the view for the Home Page which encompasses searching.
Also contains the view for the picture details page which
displays additional information and the full picture when a user clicks
on a thumbnail.
"""

import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func, desc, asc, between

from app import app, db, picture_views
from ..models import Image, Group, Group_List, Popularity
from ..forms.search_forms import InlineSearchForm

@app.route('/home/<page>', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home(page=1, search=None):
    """
    This view renders the Home Page. It's default configuration is listing images by
    popularity. It also handles the search form, and displays search results based on
    form input.
    """

    form = InlineSearchForm()

    # Default search display by relavence
    if request.method == "GET":
        form.searchSelect.data = "relavence"
    
    # Redirect with form data in the query string when a search form is submitted. This allows us to preserve
    # the search and return to the results after viewing an image in more detail.
    if form.validate_on_submit():
        page=1
        return redirect(url_for('home', search=form.searchText.data, order=form.searchSelect.data, before=form.dateBefore.data, after=form.dateAfter.data))

    # Initialize variables from the query string
    search = request.args.getlist("search") or None
    order = request.args.get("order", "most views")
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    

    # Build image query
    images = Image.query
    
    # Non-"admin" can only see pictures that are public, owned by them
    # or ones they have permissions for
    if current_user.user_name != "admin":
        images = images.outerjoin(Group, Group_List, Popularity) \
                .filter((Image.owner_name==current_user.user_name)
                    | (Image.permitted==1)
                    | (Group_List.friend_id==current_user.user_name))
    else:
        images = images.outerjoin(Popularity)
    
    # If before and after are set in the search form, select based on dates
    if before is not None and after is not None:
        date1 = datetime.datetime.strptime(after, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(before, "%Y-%m-%d").date()
        images = images.filter(between(Image.timing, date1, date2))
        flash(str(images) + after + before)
    elif before is not None:
        date = datetime.datetime.strptime(before, "%Y-%m-%d").date()
        images = images.filter(Image.timing <= date)
    elif after is not None:
        date = datetime.datetime.strptime(after, "%Y-%m-%d").date()
        images = images.filter(Image.timing >= date)
    
    # Group by images to collapse popularities for each image
    images = images.group_by(Image.photo_id)
    
    # Order by the given ordering
    if order == "most views":
        images = images.order_by(desc(func.count(Popularity.viewed_by)), desc(Image.timing))
    elif order == "newest first":
        images = images.order_by(desc(Image.timing), desc(func.count(Popularity.viewed_by))) 
    elif order == "newest last":
        images = images.order_by(asc(Image.timing), desc(func.count(Popularity.viewed_by)))
    
    # Perform a full text search on the given key words using the required weightings
    if search:
        images = images.whoosh_search(" and ".join(search), fields=('subject', 'place', 'description'),
                                      fieldboosts={"subject": 6.0, "place": 3.0})

    # Paginate (wrapper for sql limit/offset)
    images = images.paginate(int(page), 20, False)
    
    # If there are not images (not due to a restrictive search) then
    # alert the user that their are none in the database
    if images.pages == 0 and search==None and before == None and after == None:
        return render_template('logged_in/no_pictures.html', title='My Pictures', current_user=current_user)

    # If the user visits an out of bounds page, redirect to home
    if int(page) > images.pages and images.pages != 0:
        return redirect(url_for('home'))
    
    # Get a list of the popularities for each image to display on each thumbnail
    views = db.session.query(Popularity.photo_id, func.count(Popularity.viewed_by)) \
            .group_by(Popularity.photo_id).all()
    
    views_dict = {}
    for photo_id, count in views:
        views_dict[photo_id] = count

    return render_template('logged_in/home.html', title='Home', current_user=current_user,
                           images=images, server_folder=app.config['SERVE_FOLDER'], views_dict=views_dict,
                           form=form, search=search, order=order, before=before, after=after)

@app.route('/home/picture/<from_page>/<page>/<id>', methods=['GET'])
@login_required
def picture_details(from_page, page, id):
    """ Shows fields related to the image to any user with access to the image """

    image = Image.query.get(id)
    
    # Preserve query string to redirect back to search if it exists
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)

    # Redirect to the pictures page if the picture does not exist
    if image is None or (image.owner_name != current_user.user_name
        and image.permitted != 1 and current_user.user_name != "admin" and
        Group_List.query.filter_by(group_id=image.permitted, friend_id=current_user.user_name) is None):
        
        flash("Picture does not exist!")
        return redirect(url_for(app.config['FROM'][from_page]))
    
    # Helper function to increase number of views
    picture_views.add_viewed_by(id)
    
    return render_template('logged_in/picture_details.html', title='Home', current_user=current_user,
                           image=image, page=page, server_folder=app.config['SERVE_FOLDER'],
                           anchor="picture"+str(id), from_page = app.config['FROM'][from_page], search=search,
                           order=order, before=before, after=after)

@app.route('/home/picture/<from_page>/<page>/delete/<id>', methods=['GET'])
@login_required
def delete_picture_from_details(id, page, from_page):
    """ Show confirmation for picture deletion on the details page """
    
    # Preserve query string to redirect back to search results
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    picture = Image.query.get(id)
    
    # Redirect to the previous page if the picture does not exist
    if picture is None or (picture.owner_name != current_user.user_name and
                           current_user.user_name != "admin"):
        flash("Picture does not exist!")
        return redirect(url_for(app.config['FROM'][from_page]))
    
    # Confirmation method
    confirmation_link = url_for('delete_picture_from_details_confirm', page=page,
        from_page=from_page, id=id, order=order, before=before, after=after)

    flash("Are you sure you want to delete this picture? "
          '<br><a href="{}" class="alert-link">'
          'I am sure.''</a>'.format(confirmation_link), "danger")

    return redirect(url_for('picture_details', id=id, from_page=from_page, page=page,
        search=search, order=order, before=before, after=after))

@app.route('/home/picture/<from_page>/<page>/delete/<id>/confirm', methods=['GET'])
@login_required
def delete_picture_from_details_confirm(page, id, from_page):
    """ Delete the message from the details page and redirect to the previous page """
    
    # Preserver the query string to redirect back to search results
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    # Use the delete helper in picture views
    return picture_views.delete_confirm_helper(page, id, app.config['FROM'][from_page],
        search=search, order=order, before=before, after=after)
