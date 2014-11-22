"""
Holds views for user picture management pages. (My Pictures on the Nav Bar)
As well as utility methods for editing pictures.
"""


import os
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import desc
from app import app, db
from ..models import Image, Popularity
from ..forms.picture_forms import PictureForm


@app.route('/my/pictures/<page>/', methods=['GET'])
@app.route('/my/pictures/<page>/', methods=['GET'])
@app.route('/my/pictures/', methods=['GET'])
@login_required
def pictures(page=1):
    """ Main view for pictures owned by the user. Lists all pictures owned by the user newest first. """

    # Grab all user images
    images = Image.query.filter_by(owner_name=current_user.user_name).order_by(desc(Image.timing)).paginate(int(page), 10, False)
    
    # Show the 'no pictures found' if there are no pictures
    if images.pages == 0:
        return render_template('logged_in/no_pictures.html', title='My Pictures', current_user=current_user)

    # If the user accesses an out of bounds page through the url, redirect
    if int(page) > images.pages and images.pages != 0:
        return redirect(url_for('pictures'))
    
    return render_template('logged_in/my_pictures.html', title='My Pictures', current_user=current_user,
                           images=images, picture=picture, server_folder=app.config['SERVE_FOLDER'])


@app.route('/my/picture/edit/<from_page>/<page>/<id>', methods=['GET', 'POST'])
@login_required
def picture(from_page, page, id):
    """ Main view for EDITING a picture owned by a user. """

    picture = Image.query.get(id)
    form = PictureForm(picture)
    
    # Pull search args to preserve them if accessing from a search page
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    # Redirect to the previous page if the picture does not exist
    if picture is None or (picture.owner_name != current_user.user_name and
                           current_user.user_name != "admin"):
        flash("Picture does not exist!")
        return redirect(url_for(app.config['FROM'][from_page]))
    
    # Set default form field data from the picture
    if request.method == "GET":
        add_viewed_by(id)
        form.permitted.data = picture.permitted
        form.place.data = picture.place
        form.description.data = picture.description
        form.subject.data = picture.subject
        form.timing.data = picture.timing
    
    # Commit changes if a valid form is submitted
    elif form.validate_on_submit():
        db.session.commit()
        flash("Successfully updated '{}'!".format(
            picture.subject if picture.subject else "Untitled Picture"), "success")
    
    return render_template('logged_in/picture.html', title='My Pictures', current_user=current_user, image=picture,
                           page=page, server_folder=app.config['SERVE_FOLDER'], form=form, anchor="picture"+str(id),
                           from_page = app.config['FROM'][from_page], search=search, order=order, before=before, after=after)

@app.route('/my/pictures/<page>/delete/<id>', methods=['GET'])
@login_required
def delete_picture(id, page):
    """ Shows confirmation when deleting a picture from the 'My Pictures' page. """

    confirmation_link = "/my/pictures/{}/delete/{}/confirm".format(page, id)
    return delete_helper(page, id, 'pictures', confirmation_link)


@app.route('/my/pictures/<page>/delete/<id>/confirm', methods=['GET'])
@login_required
def delete_picture_confirm(page, id):
    """ Deletes a picture from the 'My Pictures' page. """

    return delete_confirm_helper(page, id, 'pictures')

def add_viewed_by(id):
    """ Helper function for adding a image/user pair to the `popularities` table. """

    viewed_by = Popularity.query.filter_by(photo_id=id, viewed_by=current_user.user_name).first()
    if viewed_by is None:
        viewed_by = Popularity(photo_id=id, viewed_by=current_user.user_name)
        db.session.add(viewed_by)
        db.session.commit()
    

def delete_helper(page, id, prev_page, confirmation_link,  search=None, order=None, before=None, after=None):
    """ Helper function for displaying a confirmation when deleting a picture """

    picture = Image.query.get(id)
    
    # redirect to the pictures page if the picture does not exist
    if picture is None or (picture.owner_name != current_user.user_name and
                           current_user.user_name != "admin"):
        flash("Picture does not exist!")
        return redirect(url_for(prev_page))
    
    flash("Are you sure you want to delete this picture? "
          '<br><a href="{}" class="alert-link">'
          'I am sure.''</a>'.format(confirmation_link), "danger")

    return redirect(url_for(prev_page, page=page, search=search, order=order, before=before, after=after))


def delete_confirm_helper(page, id, prev_page, search=None, order=None, before=None, after=None):
    """ Helper function for deleting a picture. Redirects to the previous page. """

    # Filter by username to ensure the user is the owner of the picture
    picture = Image.query.get(id)
    
    # Redirect to the previous page if the picture does not exist
    if picture is None or (picture.owner_name != current_user.user_name and
                           current_user.user_name != "admin"):
        flash("Picture does not exist!")
        return redirect(url_for(prev_page))
    
    # Delete popularities, and image
    popularities = Popularity.query.filter_by(photo_id = picture.photo_id).all()
    image = app.config['UPLOAD_FOLDER'] + picture.photo.decode()
    thumbnail = app.config['UPLOAD_FOLDER'] + picture.thumbnail.decode()
    
    try:
        os.remove(image)
        os.remove(thumbnail)
        for popularity in popularities:
            db.session.delete(popularity)
        db.session.delete(picture)
        db.session.commit()
    except:
        flash("Error deleting image.")
    
    return redirect(url_for(prev_page, page=page,  search=search, order=order, before=before, after=after))
