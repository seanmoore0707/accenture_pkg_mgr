from flask import Flask, render_template, session, redirect, url_for, flash, send_file, send_from_directory
from flask_bootstrap import Bootstrap
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, SelectMultipleField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import os
from subprocess import call
from docker import *
import tarfile
import gzip
import shutil
import boto3, botocore
from config import S3_KEY, S3_SECRET, S3_BUCKET



# Uses wtfforms, bootstrap, jinja
# python3 -m venv venv
# source venv/bin/activate
# pip install flask
# pip install flask-wtf
# pip install flask-bootstrap
# pip install docker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rb4(X~f`Y%#"bF8P'
bootstrap = Bootstrap(app)
client = from_env()

s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)

# Dictionary that maps the name of the app (key) to a list of required images' names (value)
# Customise for each use case
dictionary =  { 'app1' : ['alpine:3.9.2'], 
                'app2' : ['alpine:3.9'], 
                'app3' : ['alpine:3.8.4'], 
                'app4' : ['alpine:3.7.3'], 
                'app5' : ['alpine:3.6.5'],
                'app6' : ['alpine:3.6'] }
imagesDownloaded=[]
client = APIClient(base_url='unix://var/run/docker.sock')


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
        # Bug: Flash not displaying as wanted, currently only displaying after refresh
        flash("Download will commence shortly")
        return redirect(url_for('upload_file_to_s3'))
    return render_template('index.html', form=form, filesToDownload=session.get('filesToDownload'))


@app.route('/upload_file_to_s3', methods=['GET', 'POST'])
def upload_file_to_s3(bucket_name = S3_BUCKET, acl="public-read", contentType = "application/tar"):

    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """
    apps = session.get('filesToDownload')
    file = download(apps)
    try:

        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": contentType,
                "ContentEncoding": "gzip"
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format(app.config["S3_LOCATION"], file.filename)

@app.route('/download', methods=['GET', 'POST'])
def download(apps):
    # Gets data from selectForm and grabs corresponding image objects into a list
    # filesToDownload is a list of strings of image ids
    
    glassory = dictionary

    filename = 'clientImages.tar'

    tarfile = open(filename, 'wb')
    for app in apps:
        images = glassory[app]
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
#    with open (filename, 'rb') as f_in, gzip.open(filename+'.gz', 'wb') as f_out:

#        shutil.copyfileobj(f_in, f_out)

        
    attachment = send_file(filename)
#    f_in.close()
#    f_out.close()
    # Ensures that existings tar files do not get lumped into new download request
    # os.remove should be compatible with all OS
    os.remove(filename)
#    os.remove(filename+'.gz')

    return attachment




#@app.route('/download', methods=['GET', 'POST'])
#def get_input_list():
#    if 'apps' in request.args:
#        return download(request.args['apps'])
#    else:
#        return "Empty or Wrong apps list"




