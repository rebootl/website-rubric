import os
import sqlite3
import json
import datetime
import hashlib
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app, make_response
from rubric_dyn.common import pandoc_pipe, get_md5sum, date_norm, url_encode_str
from rubric_dyn.ExifNice import ExifNiceStr

# (example from tutorial)
#simple_page = Blueprint('simple_page', __name__,
#                        template_folder='templates')
#
#@simple_page.route('/', defaults={'page': 'index'})
#@simple_page.route('/<page>')
#def show(page):
#    try:
#        return render_template('pages/%s.html' % page)
#    except TemplateNotFound:
#        abort(404)

interface = Blueprint('interface', __name__)

# restrict all views example
# --> login needs to be adapted for this so that login is possible
#@interface.before_request
#def restrict_access():
#    if not session.get('logged_in'):
#        abort(401)

@interface.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        passwd_str = request.form['password']
        passwd_hash = hashlib.sha1(passwd_str.encode()).hexdigest()
        if request.form['username'] != current_app.config['USERNAME'] \
          or passwd_hash != current_app.config['PASSWD_SHA1']:
            error = "Invalid username or password..."
        else:
            session['logged_in'] = True
            flash('Login successful.')
            return redirect(url_for('interface.overview'))
    return render_template('login.html', error=error, title="Login")

@interface.route('/overview', methods=['GET', 'POST'])
def overview():
    if not session.get('logged_in'):
        abort(401)

    # get all pages
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, type, title, date_norm, ref, pub
                          FROM entries
                          ORDER BY datetime_norm DESC''')
    rows = cur.fetchall()

    # create link hrefs
    hrefs = {}
    for row in rows:
        hrefs.update({ row['id']: os.path.join(row['date_norm'], row['ref']) })

    return render_template( 'overview.html', entries=rows, \
                            title="Overview", hrefs=hrefs )

@interface.route('/edit', methods=['GET', 'POST'])
def edit():
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'POST':
        action = request.form['actn']
        if action == "cancel":
            return redirect(url_for('interface.overview'))
        elif action == "preview":
            id = request.form['id']
            text_input = request.form['text-input']
            return render_preview(id, text_input)
            #return text_input
        elif action == "save":
            id = request.form['id']
            if id == "new":
                text_input = request.form['text-input']
                page_inst = NewPage(text_input)
                page_inst.save_new()
                flash("New Page saved successfully!")
                return redirect(url_for('interface.overview'))
            else:
                text_input = request.form['text-input']
                page_inst = EditPage(id, text_input)
                page_inst.save_edit()
                flash("Page ID {} saved successfully!".format(id))
                return redirect(url_for('interface.overview'))
        else:
            abort(404)
    else:
        id = request.args.get('id')

        if id == "new":
            # create new
            type = request.args.get('type')
            return load_to_edit_new(type)
            #abort(404)

        elif id == None:
            # --> abort for now
            abort(404)

        else:
            return load_to_edit(id)

@interface.route('/new')
def new():
    if not session.get('logged_in'):
        abort(401)

    type = request.args.get('type')

    return load_to_edit_new(type)

@interface.route('/pub')
def pub():
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    # --> change state
    #flash('published {} id {}'.format(publ, id))
    update_pub(id, 1)
    flash('Published ID {}'.format(id))

    return redirect(url_for('interface.overview'))

@interface.route('/unpub')
def unpub():
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    # --> change state
    #flash('published {} id {}'.format(publ, id))
    update_pub(id, 0)
    flash('Unublished ID {}'.format(id))

    return redirect(url_for('interface.overview'))

@interface.route('/download')
def download_text():
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')

    # get text
    cur = g.db.execute('''SELECT ref, meta_json, body_md
                          FROM entries
                          WHERE id = ?
                          LIMIT 1''', (id,))
    ref, meta_json, body_md = cur.fetchone()

    # add 'id' to meta
    meta = json.loads(meta_json)
    if 'id' not in meta.keys():
        meta['id'] = id
        meta_json_full = json.dumps(meta)
    else:
        meta_json_full = meta_json

    text = '\n%%%\n'.join((meta_json_full, body_md))

    datetime_str = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%Mm%S')
    filename = ref + "_" + datetime_str + ".page"

    response = make_response(text)
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
    return response

@interface.route('/recreate_exifs')
def recreate_exifs():
    if not session.get('logged_in'):
        abort(401)

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, meta_json
                          FROM entries''')
    rows = cur.fetchall()

    for row in rows:
        meta = process_meta_json(row['meta_json'])

        img_exifs_json = create_exifs_json(meta['files'])

        g.db.execute('''UPDATE entries
                        SET exifs_json = ?
                        WHERE id = ?''', (img_exifs_json, row['id']))
        g.db.commit()

    flash('Updated EXIF data successfully.')
    return redirect(url_for('interface.overview'))

    # (debug)
    #text = ""
    #for row in rows:
    #    text += "id: " + str(row['id']) + "\n"

    #return "FOO"

def update_pub(id, pub):
    g.db.execute('''UPDATE entries
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()

def render_preview(id, text_input):

    meta, body_html, img_exifs_json = process_edit(text_input)

    # set imagepage specifics
    if meta['type'] == "imagepage":
        img_src = os.path.join("/media", meta['image'])
        article_class = "imagepage"
    else:
        img_src = ""
        article_class = ""

    if img_exifs_json == "":
        img_exifs_json = False

    # render stuff
    return render_template( 'edit.html',
                            preview=True,
                            id=id,
                            text=text_input,
                            title="Edit",
                            preview_type=meta['type'],
                            preview_title=meta['title'],
                            preview_body_html=body_html,
                            preview_article_class=article_class,
                            preview_img_src=img_src,
                            img_exifs_json=img_exifs_json )

def process_edit(text_input, return_md=False):

    # escape shit ?

    # split text in json and markdown block
    meta_json, body_md = text_input.split('%%%', 1)

    meta = process_meta_json(meta_json)

    # process text through pandoc
    body_html = pandoc_pipe( body_md,
                             [ '--to=html5',
                               '--filter=rubric_dyn/filter_img_path.py' ] )

    img_exifs_json = create_exifs_json(meta['files'])

    if not return_md:
        return meta, body_html, img_exifs_json
    else:
        return meta, meta_json, img_exifs_json, body_html, body_md

def create_exifs_json(files):
    # create image info (EXIF data)
    img_exifs = {}
    for file in files:
        if os.path.splitext(file)[1] in current_app.config['JPEG_EXTS']:
            img_filepath = os.path.join( current_app.config['RUN_PATH'],
                                         current_app.config['MEDIA_FOLDER'],
                                         file )
            exif = ExifNiceStr(img_filepath)
            if exif.display_str:
                image_exif = { os.path.join( '/',
                                             current_app.config['MEDIA_FOLDER'],
                                             file ) : exif.display_str }
                img_exifs.update(image_exif)
    if img_exifs:
        return json.dumps(img_exifs)
    else:
        return ""

def process_meta_json(meta_json):
    try:
        meta = json.loads(meta_json)
    except json.decoder.JSONDecodeError:
        flash("Warning: Error in JSON data, using defaults...")
        meta = {}

    # set defaults
    for key, value in current_app.config['META_DEFAULTS'].items():
            if key not in meta.keys():
                meta[key] = value

    if type == "imagepage":
        if meta['image'] == "" or meta['image'] == None:
            meta['image'] = "NO IMAGE SET"

    return meta

def load_to_edit(id):

    # get data for the page to edit
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT meta_json, body_md
                          FROM entries
                          WHERE id = ?
                          LIMIT 1''', (id,))
    meta_json, body_md = cur.fetchone()

    # --> catch not found

    # assemble body
    text = '%%%'.join((meta_json, body_md))

    return render_template( 'edit.html', preview=False, id=id, \
                            text=text, title="Edit" )

def load_to_edit_new(type):
    return render_template( 'edit.html', preview=False, id="new", \
                            title="Edit", new=True, type=type )

class Page:

    def __init__(self, text_input):
        self.text_input = text_input

        self.meta, \
        self.meta_json, \
        self.img_exifs_json, \
        self.body_html, \
        self.body_md = process_edit(self.text_input, True)

        self.title = self.meta['title']
        self.author = self.meta['author']

        self.body_md5sum = get_md5sum(self.body_md)

        self.date_str = self.meta['date']
        self.date_norm, \
        self.time_norm, \
        self.datetime_norm = date_norm( self.date_str,
                                        current_app.config['DATETIME_FORMAT'],
                                        current_app.config['DATE_FORMAT'] )

        self.ref = url_encode_str(self.title)

        self.type = self.meta['type']
        if self.type == 'imagepage':
            self.data1 = self.meta['image']
        else:
            self.data1 = ""

#    def save(self):
#        raise NotImplementedError

class EditPage(Page):

    def __init__(self, id, text_input):
        self.id = id
        super().__init__(text_input)

    def save_edit(self):
        self.db_update_entry()

    def db_update_entry(self):
        g.db.execute( '''UPDATE entries
                         SET ref = ?, type = ?, title = ?, author = ?,
                          date_str = ?, datetime_norm = ?, date_norm = ?,
                          time_norm = ?, body_html = ?, body_md5sum = ?,
                          meta_json = ?, body_md = ?, data1 = ?,
                          img_exifs_json = ?
                         WHERE id = ?''',
                      ( self.ref, self.type, self.title, self.author, \
                        self.date_str, self.datetime_norm, self.date_norm, \
                        self.time_norm, self.body_html, self.body_md5sum, \
                        self.meta_json, self.body_md, self.data1, \
                        self.img_exifs_json, self.id ) )
        g.db.commit()

class NewPage(Page):

#    def __init__(self, text_input):
#        super().__init__(text_input)

    def save_new(self):
        self.db_new_entry()

    def db_new_entry(self):
        g.db.execute( '''INSERT INTO entries
                         (ref, type, title, author,
                          date_str, datetime_norm, date_norm,
                          time_norm, body_html, body_md5sum,
                          meta_json, body_md, data1, img_exifs_json)
                        VALUES
                          (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ( self.ref, self.type, self.title, self.author,
                        self.date_str, self.datetime_norm, self.date_norm,
                        self.time_norm, self.body_html, self.body_md5sum,
                        self.meta_json, self.body_md, self.data1,
                        img_exifs_json ) )
        g.db.commit()


# (examples from tutorial)
#
#@app.route('/add', methods=['POST'])
#def add_entry():
#    if not session.get('logged_in'):
#        abort(401)
#    g.db.execute('insert into entries (title, text) values (?, ?)',
#                 [request.form['title'], request.form['text']])
#    g.db.commit()
#    flash('New entry was successfully posted')
#    return redirect(url_for('show_entries'))
#
#@app.route('/logout')
#def logout():
#    session.pop('logged_in', None)
#    flash('You were logged out')
#    return redirect(url_for('show_entries'))
