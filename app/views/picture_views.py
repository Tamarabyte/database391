import datetime
import os
from flask import render_template, flash, redirect, url_for, request
from flask.ext.login import login_required, current_user
from sqlalchemy import desc
from app import app, db
from ..models import Image, Popularity
from ..forms.picture_forms import PictureForm


@app.route('/my/pictures/<page>', methods=['GET'])
@app.route('/my/pictures/<page>', methods=['GET'])
@app.route('/my/pictures', methods=['GET'])
@login_required
def pictures(page=1):
    images = Image.query.filter_by(owner_name=current_user.user_name).order_by(desc(Image.timing)).paginate(int(page), 10, False)
    
    if images.pages == 0:
        return render_template('logged_in/no_pictures.html', title='My Pictures', current_user=current_user)
        
    if int(page) > images.pages and images.pages != 0:
        return redirect(url_for('pictures'))
    
    return render_template('logged_in/my_pictures.html', title='My Pictures', current_user=current_user,
                           images=images, picture=picture, server_folder=app.config['SERVE_FOLDER'])


@app.route('/my/picture/edit/<from_page>/<page>/<id>', methods=['GET', 'POST'])
@login_required
def picture(from_page, page, id):
    # filter by username to ensure the user is the owner of the group
    picture = Image.query.get(id)
    form = PictureForm(picture)
    
    search = request.args.get("search", None)
    order = request.args.get("order", None)
    before = request.args.get("before", None)
    after = request.args.get("after", None)
    
    # redirect to the pictures page if the picture does not exist
    if picture is None or picture.owner_name != current_user.user_name:
        flash("Picture does not exist!")
        return redirect(url_for(app.config['FROM'][from_page]))
    
    if request.method == "GET":
        add_viewed_by(id)
        form.permitted.data = picture.permitted
        form.place.data = picture.place
        form.description.data = picture.description
        form.subject.data = picture.subject
    
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
    confirmation_link = "/my/pictures/{}/delete/{}/confirm".format(page, id)
    return delete_helper(page, id, 'pictures', confirmation_link)


@app.route('/my/pictures/<page>/delete/<id>/confirm', methods=['GET'])
@login_required
def delete_picture_confirm(page, id):
    return delete_confirm_helper(page, id, 'pictures')

# helper functions for incrementing # of views

def add_viewed_by(id):
    viewed_by = Popularity.query.filter_by(photo_id=id, viewed_by=current_user.user_name).first()
    if viewed_by is None:
        viewed_by = Popularity(photo_id=id, viewed_by=current_user.user_name)
        db.session.add(viewed_by)
        db.session.commit();
    
# helper functions for deleting an image

def delete_helper(page, id, prev_page, confirmation_link,  search=None, order=None, before=None, after=None):
    picture = Image.query.get(id)
    
    # redirect to the pictures page if the picture does not exist
    if picture is None or picture.owner_name != current_user.user_name:
        flash("Picture does not exist!")
        return redirect(url_for(prev_page))
    
    flash("Are you sure you want to delete this picture? "
          '<br><a href="{}" class="alert-link">'
          'I am sure.''</a>'.format(confirmation_link), "danger")

    return redirect(url_for(prev_page, page=page, search=search, order=order, before=before, after=after))


def delete_confirm_helper(page, id, prev_page, search=None, order=None, before=None, after=None):
    # filter by username to ensure the user is the owner of the picture
    picture = Image.query.get(id)
    
    # redirect to the previous page if the picture does not exist
    if picture is None or picture.owner_name != current_user.user_name:
        flash("Picture does not exist!")
        return redirect(url_for(prev_page))
    
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
        flask("Error deleting image.")
    
    return redirect(url_for(prev_page, page=page,  search=search, order=order, before=before, after=after))
