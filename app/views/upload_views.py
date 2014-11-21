"""
Holds views for uploading images or a directory. Handles
submission of the upload form. Contains helper method
for generating thumbnails.
"""

import datetime, os
import uuid
from flask import render_template, flash, request
from flask_login import login_required, current_user
from app import app, db
from ..models import Image
from ..forms.upload_forms import UploadForm
from werkzeug import secure_filename
from PIL import Image as Pil

@app.route('/upload/',  methods=['GET', 'POST'])
@login_required
def uploaded_file():
    """ Handles the upload form submission, generating thumbnails, and saving images. """

    form = UploadForm()

    if form.validate_on_submit():
        files = request.files.getlist('image')
        dir_files = request.files.getlist('image_dir')
        file_objs = []
        
        # Combine any files uploaded through the directory input field
        # With files uploaded through the file list input field
        if files is not None:
            # allowed_file ensures only allowed formats are included in the list
            file_objs += [file_obj for file_obj in files if file_obj and allowed_file(file_obj.filename)]
        if dir_files is not None:
            file_objs += [file_obj for file_obj in dir_files if file_obj and allowed_file(file_obj.filename)]
        
        # Validate that at least one image was uploaded
        if len(file_objs) == 0:
             form.image.errors.append('*upload at least one file')
             return render_template('logged_in/upload.html', title='Upload Pictures', form=form, current_user=current_user)

        # Iterate through our list of file objects, generate thumbnails and
        # save form input in the `images` table
        count = 0;
        for file_obj in file_objs:
            count += 1;
            filename = str(uuid.uuid1()) + secure_filename(file_obj.filename)
            image_file = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_obj.save(image_file)
            img = Pil.open(image_file)
            thumb_filename = os.path.splitext(filename)[0] + ".thumbnail"
            thumb_file = os.path.splitext(image_file)[0] + ".thumbnail"

            # Create thumbnails for the image
            resize(img, thumb_file)
            
            # Create new Image ORM
            image_obj = Image(
                owner_name = current_user.user_name,
                permitted = form.permitted.data,
                subject = form.subject.data,
                place = form.place.data,
                description = form.description.data,
                timing = datetime.date.today(),
                photo = filename.encode('utf-8'),
                thumbnail = thumb_filename.encode('utf-8')
            )

            db.session.add(image_obj)

        # Commit results to the database
        db.session.commit()

        # Show success message
        flash("Successfully uploaded {} file{}!".format(count, "s" if count != 1 else ""), "success")
    
    return render_template('logged_in/upload.html', title='Upload Pictures', form=form, current_user=current_user)

def allowed_file(filename):
    """ Checks that the file uploaded is one of the allowed extensions """
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1]
    return extension in app.config['ALLOWED_EXTENSIONS']


def resize(image, out):
    """ Provided for use by http://united-coders.com/christian-harms/image-resizing-tips-every-coder-should-know/ """

    box = (200, 200)

    # Preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while image.size[0]/factor > 2*box[0] and image.size[1]*2/factor > 2*box[1]:
        factor *=2
    if factor > 1:
        image.thumbnail((image.size[0]/factor, image.size[1]/factor), Pil.NEAREST)

    # Calculate the cropping box and get the cropped part
    x1 = y1 = 0
    x2, y2 = image.size
    wRatio = 1.0 * x2/box[0]
    hRatio = 1.0 * y2/box[1]
    if hRatio > wRatio:
        y1 = int(y2/2-box[1]*wRatio/2)
        y2 = int(y2/2+box[1]*wRatio/2)
    else:
        x1 = int(x2/2-box[0]*hRatio/2)
        x2 = int(x2/2+box[0]*hRatio/2)
    image = image.crop((x1,y1,x2,y2))

    # Resize the image with best quality algorithm ANTI-ALIAS
    image.thumbnail(box, Pil.ANTIALIAS)

    # Save it into a file-like object
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(out, "JPEG", quality=75)
    
    
    
    
    
    