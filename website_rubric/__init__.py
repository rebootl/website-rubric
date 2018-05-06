#!/usr/bin/python
# --> do we need this ^^^ ???
import os
import sqlite3
from flask import Flask, render_template, g, request, session, redirect, url_for, \
     abort, flash, send_from_directory

# getting flask app

app = Flask(__name__, static_url_path="/media", static_folder="media")
app.config.from_object('config')
app.config.from_envvar('RUBRIC_ADD_SETTINGS', silent=True)
#app.config['DEBUG'] = True

# some db stuff

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# getting views

from website_rubric.views.pages import pages
app.register_blueprint(pages)

from website_rubric.views.interface import interface
app.register_blueprint(interface, url_prefix='/interface')

# media folder (static)
# ==> setting above
#from website_rubric.media_static import media_static
#app.register_blueprint(media_static)



if __name__ == '__main__':
    app.run()
