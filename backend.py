from flask import Flask, render_template, session, redirect, url_for, flash, send_file, send_from_directory
from flask_bootstrap import Bootstrap
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, SelectMultipleField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import docker
import gzip
import shutil
import os



# Uses wtfforms, bootstrap, jinja
# pip install flask
# pip install flask-wtf
# pip install flask-bootstrap

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rb4(X~f`Y%#"bF8P'
bootstrap = Bootstrap(app)

class SelectForm(FlaskForm):
    # Choices are in (value, key) pairs, ideally value would Image ID and key would be Name
    filesToDownload = SelectMultipleField("Choose docker images to download",
                                choices=[('94e814e2efa8', 'Ubuntu'), ('d8233ab899d4', 'BusyBox'), ('fce289e99eb9', "Hello World")],
                                validators=[DataRequired()])
    submit = SubmitField('Submit')
    client = docker.APIClient(base_url='unix://var/run/docker.sock')
    imagesDownloaded=[]
    dictionary = {}

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404


    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    @app.route('/', methods=['GET', 'POST'])
    def index(self):
    # Need to change session context into another context, annoying to keep data after webpage/server refresh/restart
        form = SelectForm()
        if form.validate_on_submit():
            session['filesToDownload'] = form.filesToDownload.data
        # Bug: Flash not displaying as wanted, currently only displaying after refresh
            flash("Download will commence shortly")
            return redirect(url_for('download'))
        return render_template('index.html', form=form, filesToDownload=session.get('filesToDownload'))

    @app.route('/download', methods=['GET', 'POST'])

    def download(self,apps, glassory = self.dictionary):
    # Modified by Haonan Chen
    # Date: 24.03.2019
    # Change the download() method in a more reasonable way
    # @param apps: a list of app names
    # @param glassory: a dictionary of app v.s. image as parameters
    # Each app in the list or the (key, value) in glassory are stored as string
    # Each name of image in the form: (respository : tag)
        
        root_directory = '/download'
        dirctory = '/download/clientImages.tar'
        filename = 'clientImages.tar'

        tarfile = open(dirctory, 'wb')
        for app in apps:
            images = glassory[app]
            for image in images:
                if image not in self.imagesDownloaded:
                    self.imagesDownloaded.append(image)
                    strs = image.split(":")
                    self.client.pull(strs[0], tag=strs[1])

                # we can use get_image directly to get the image with a specific version
                tarball = self.client.get_image(image)

                for chunk in tarball:

                    tarfile.write(chunk)


        tarfile.close()

        # Modified From version of Jackson Qiu
        # Convert from tar file to gzip file with a smaller size
        
        with open (directory, 'rb') as f_in, gzip.open(directory+'.gz', 'wb') as f_out:

            shutil.copyfileobj(f_in, f_out)

        

        f_in.close()
        f_out.close()

        # a secure way to quickly expose static files from an upload folder or something similar.
        # more efficient than send_file()
        attachment = send_from_directory(root_directory,
                               filename+'.gz', as_attachment=True)
    
        # Ensures that existings tar files do not get lumped into new download request
        # os.remove should be compatible with all OS
        os.remdir(directory)
        os.remdir(directory+'.gz')


        return attachment
    
    # Created by Haonan Chen
    # Date: 24.03.2019
    # A prototype of REST Web API for transfer the apps list input from frontend to backend
    @app.route('/download', methods=['GET', 'POST'])
    def get_input_list():
        if 'apps' in request.args:
            files = self.download(request.args['apps'])
            return files
        else:
            return "Empty or Wrong apps list"



