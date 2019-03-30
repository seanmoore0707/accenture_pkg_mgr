# accenture_pkg_mgr
Accenture myWizard360 - Package Manager team

Team members: Sean Chen, Zach Ho, Ryan Ern, Jack Qiu
Mentor: Ido Zamir

Project Description:

Installation Instructions:

Run the following commands (obviously don't put $ in your commands)

git clone <>

To create a virtual environment (You will need to create your own virtual env):
```
$ python3 -m venv venv
$ source venv/bin/activate
```
Uses WTFForms, Bootstrap, Jinja for frontend

To install used modules:
```
$ pip install flask
$ pip install flask-wtf
$ pip install flask-bootstrap
$ pip install docker
$ pip install boto3
```

To run server:
```
$ export FLASK_APP=main.py
$ flask run
```

To get out of venv
```
$ deactivate
```
