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

# Dictionary that maps the name of the app (key) to a list of required images' names (value)
# Customise for each use case
dictionary =  { 'Alpine' : ['alpine:3.9.2'] }
imagesDownloaded=[]
client = docker.APIClient(base_url='unix://var/run/docker.sock')


class SelectForm(FlaskForm):
    # Choices are in (value, key) pairs, ideally value would Image ID and key would be Name
    filesToDownload = SelectMultipleField("Choose docker images to download",
                                choices=choices,
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
        return redirect(url_for('download'))
    return render_template('index.html', form=form, filesToDownload=session.get('filesToDownload'))

@app.route('/download', methods=['GET', 'POST'])
def download(apps, glassory = dictionary):
    # Gets data from selectForm and grabs corresponding image objects into a list
    # filesToDownload is a list of strings of image ids
    root_directory = '/download'
    dirctory = '/download/clientImages.tar'
    filename = 'clientImages.tar'

    tarfile = open(dirctory, 'wb')
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
    with open (directory, 'rb') as f_in, gzip.open(directory+'.gz', 'wb') as f_out:

        shutil.copyfileobj(f_in, f_out)

        

    f_in.close()
    f_out.close()
    # Ensures that existings tar files do not get lumped into new download request
    # os.remove should be compatible with all OS
    os.remdir(directory)
    os.remdir(directory+'.gz')

    return attachment


@app.route('/download', methods=['GET', 'POST'])
def get_input_list():
    if 'apps' in request.args:
        return download(request.args['apps'])
    else:
        return "Empty or Wrong apps list"




