#!/usr/bin/python
import os
import sqlite3
from flask import Flask, render_template, g, request, session, redirect, url_for, \
     abort, flash, send_from_directory

# getting flask app

app = Flask(__name__)
app.config.from_object('config')

# (overwrite config from environment example)
#app.config.from_envvar('FLASKR_SETTINGS', silent=True)

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

from rubric_dyn.views.pages import pages
app.register_blueprint(pages)

from rubric_dyn.views.interface import interface
app.register_blueprint(interface)

# media folder (static)

from rubric_dyn.media_static import media_static
app.register_blueprint(media_static)

# --> move into blueprint ==> done
#@app.route('/media/<filename>')
#def media_file(filename):
#    return send_from_directory(app.config['MEDIA_DIR'], filename)

# --> move into blueprint as well ==> done
# for testing only, should be done by the webserver
#@app.route('/media/localfont/Lora/bold/<filename>')
#@app.route('/media/localfont/Lora/bolditalic/<filename>')
#@app.route('/media/localfont/Lora/regular/<filename>')
#@app.route('/media/localfont/Lora/italic/<filename>')
#@app.route('/media/localfont/Lora/<filename>')
#def font_file(filename):
#    return send_from_directory(app.config['FONT_DIR'], filename)


if __name__ == '__main__':
    app.run()
