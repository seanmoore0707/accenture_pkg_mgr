from flask import Flask, render_template, session, redirect, url_for, flash, send_file, send_from_directory
from flask_bootstrap import Bootstrap
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, SelectMultipleField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import docker


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
    client = docker.from_env()
    client = docker.DockerClient(base_url='tcp://127.0.0.1:1234')

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
    def download(self,apps, glassory):
    # Modified by Haonan Chen
    # Date: 19.03.2019
    # Change the download() method in a more reasonable way
    # @param apps: a list of app names
    # @param glassory: a dictionary of app v.s. image as parameters
    # Each app in the list or the (key, value) in glassory are stored as string
    # Each name of image in the form: (respository : tag)
        images=[]
        for app in apps:
            imgs = glassory[app]
            for img in imgs:
                if img not in images:
                    images.append(img)
                    strs = img.split(":")
                    self.client.images.pull(strs[0], tag=strs[1])

