from flask import Flask, render_template, session, redirect, url_for, flash, send_file, send_from_directory
from flask_bootstrap import Bootstrap
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, SelectMultipleField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import os
from io import BytesIO
from subprocess import call
from docker import *
import tarfile
import gzip
import shutil
import boto3, botocore
from botocore.client import Config
from config import S3_KEY, S3_SECRET, S3_BUCKET, S3_LOCATION
from werkzeug.utils import secure_filename

# Uses wtfforms, bootstrap, jinja
# python3 -m venv venv
# source venv/bin/activate
# pip install flask
# pip install flask-wtf
# pip install flask-bootstrap
# pip install docker

# Uses code from http://zabana.me/notes/upload-files-amazon-s3-flask.html

app = Flask(__name__)
app.config.from_object("config")
bootstrap = Bootstrap(app)
client = from_env()
s3 = boto3.client("s3", aws_access_key_id=S3_KEY, aws_secret_access_key=S3_SECRET, config=Config(signature_version='s3v4'))
client = APIClient(base_url='unix://var/run/docker.sock')

# Dictionary that maps the name of the app (key) to a list of required images' names (value)
# Customise for each use case
dictionary =  { 'app1' : ['alpine:3.9.2'], 
                'app2' : ['alpine:3.9'], 
                'app3' : ['alpine:3.8.4'], 
                'app4' : ['alpine:3.7.3'], 
                'app5' : ['alpine:3.6.5'],
                'app6' : ['alpine:3.6'] }

imagesDownloaded=[]
filename = 'clientImages.tar'


class SelectForm(FlaskForm):
    # Choices are in (value1, value2) pairs, 
    # the first value in the tuple is the one put into a list and stored in form.filesToDownload.data
    # the second value in the tuple is the one displayed on the web form
    filesToDownload = SelectMultipleField("Choose docker images to download",
                                choices=[('app1','app1'), ('app2','app2'),('app3','app3'),('app4','app4'),('app5','app5'),('app6','app6')],
                                validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    # Need to change session context into another context, annoying to keep data after webpage/server refresh/restart
    form = SelectForm()
    if form.validate_on_submit():
        session['filesToDownload'] = form.filesToDownload.data
        flash("Download will commence shortly")
        return redirect(url_for('download'))
    return render_template('index.html', form=form, filesToDownload=session.get('filesToDownload'))

@app.route('/download', methods=['GET', 'POST'])
def download():
    # Gets data from selectForm and grabs apps selected into a list
    # filesToDownload is a list of strings of app names
    apps = session.get('filesToDownload')

    # Saves the images into a tar file
    tarfile = open(filename, 'wb')
    for selected_app in apps:
        images = dictionary[selected_app]
        for image in images:
            if image not in imagesDownloaded:
                imagesDownloaded.append(image)
                strs = image.split(":")
                client.pull(strs[0], tag=strs[1])

            # we can use get_image directly to get the image with a specific version
            tarball = client.get_image(image)

            for chunk in tarball:

                tarfile.write(chunk)


    tarfile.close()
    # GZip compresses tar file
    # Convert tar file to a file-like object for uploading to S3
    compressedFile = BytesIO()
    with open(filename, 'rb') as f_in:
        with gzip.GzipFile(fileobj=compressedFile, mode="wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    compressedFile.seek(0)

    if f_out:
        output = upload_file_to_s3(compressedFile)

    f_in.close()
    f_out.close()
    
    # Ensures that existings tar files do not get lumped into new download request
    # os.remove should be compatible with all OS
    os.remove(filename)
    
    return str(output)

def upload_file_to_s3(file):

    fileName = filename + '.gz'
    try:
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            fileName,
            ExtraArgs={
                "ContentType": 'application/tar',
                'ContentEncoding' : 'gzip'
            }
        )
    
    # generate the presigned url
        url = s3.generate_presigned_url(
                                        ClientMethod='get_object',
                                        Params={
                                            'Bucket': S3_BUCKET,
                                            'Key': fileName
                                        }
                                    )
    except Exception as e:
        # This is a catch all exception, edit this part to fit your needs.
        print("Something Happened: ", e)
        return e
    
    return url

if __name__ == "__main__":
    app.run()