import datetime, os
import uuid

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask.ext.login import login_required, current_user

from app import app, db
from ..models import User, Image
from ..forms.upload_forms import UploadForm
from werkzeug import secure_filename
import uuid
from PIL import Image as Pil

@app.route('/upload/',  methods=['GET', 'POST'])
@login_required
def uploaded_file():
    form = UploadForm()
    if form.validate_on_submit():

        files = request.files.getlist('image')
        dir_files = request.files.getlist('image_dir')
        file_objs = []
        
        if files is not None:
            file_objs += [file_obj for file_obj in files if file_obj and allowed_file(file_obj.filename)]
        if dir_files is not None:
            file_objs += [file_obj for file_obj in dir_files if file_obj and allowed_file(file_obj.filename)]
        
        if len(file_objs) == 0:
             form.image.errors.append('*upload at least one file')
             return render_template('logged_in/upload.html', title='Upload Pictures', form=form, current_user=current_user)

        count = 0;
        for file_obj in file_objs:
            count += 1;
            filename = str(uuid.uuid1()) + secure_filename(file_obj.filename)
            image_file = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_obj.save(image_file)

            img = Pil.open(image_file)
            thumb_filename = os.path.splitext(filename)[0] + ".thumbnail"
            thumb_file = os.path.splitext(image_file)[0] + ".thumbnail"
            resize(img, thumb_file)
            
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
        db.session.commit()
    
        flash("Successfully uploaded {} file{}!".format(count, "s" if count != 1 else ""), "success")
    
    return render_template('logged_in/upload.html', title='Upload Pictures', form=form, current_user=current_user)

def allowed_file(filename):
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1]
    return extension in app.config['ALLOWED_EXTENSIONS'];


def resize(img, out):
    box = (200, 200)
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *=2
    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Pil.NEAREST)

    #calculate the cropping box and get the cropped part
    x1 = y1 = 0
    x2, y2 = img.size
    wRatio = 1.0 * x2/box[0]
    hRatio = 1.0 * y2/box[1]
    if hRatio > wRatio:
        y1 = int(y2/2-box[1]*wRatio/2)
        y2 = int(y2/2+box[1]*wRatio/2)
    else:
        x1 = int(x2/2-box[0]*hRatio/2)
        x2 = int(x2/2+box[0]*hRatio/2)
    img = img.crop((x1,y1,x2,y2))

    #Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Pil.ANTIALIAS)

    #save it into a file-like object
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(out, "JPEG", quality=75)
    
    
    
    
    
    