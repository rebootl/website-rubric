'''"backend" interface'''
import os
import sqlite3
import json
import hashlib
from datetime import datetime
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app
from werkzeug.utils import secure_filename

from rubric_dyn.common import url_encode_str, date_norm2, time_norm, gen_hrefs, \
    get_feat
from rubric_dyn.db_read import db_load_to_edit, db_load_category
from rubric_dyn.db_write import update_pub, update_pub_change, db_store_category
from rubric_dyn.helper_interface import process_input, get_images_from_path, \
    gen_image_md, get_images_from_md, gen_image_subpath, allowed_image_file
from rubric_dyn.Page import Page

interface = Blueprint('interface', __name__,
                      template_folder='../templates/interface')

### functions returning a "view"

# (none...)

### routes

@interface.route('/', methods=['GET', 'POST'])
def login():
    '''login page'''
    if session.get('logged_in'):
        return redirect(url_for('interface.overview'))
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
    return render_template('login.html', error=error, title=None)

@interface.route('/logout')
def logout():
    '''logout'''
    session.pop('logged_in', None)
    #flash('You were logged out.')
    return redirect(url_for('interface.login'))

@interface.route('/store-feat')
def store_feat():
    '''store featured id (shown on home page)'''
    if not session.get('logged_in'):
        abort(401)

    feat_id = request.args.get('feat-id')

    # make sure it's int
    try:
        feat_id_int = int(feat_id)
    except ValueError:
        flash('Featuring ID must be an integer, returning...')
        return redirect(url_for('interface.overview'))
    except:
        abort(404)

    # store it
    with open(current_app.config['FEAT_STORE_F'], 'w') as f:
        json.dump(feat_id, f)

    flash('Featuring ID {}'.format(feat_id))

    return redirect(url_for('interface.overview'))

@interface.route('/overview', methods=['GET', 'POST'])
def overview():
    '''interface overview
shows:
- a list of all pages
- new page creation (done in template)
'''
    if not session.get('logged_in'):
        abort(401)

    # get all pages
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, type, title, date_norm, time_norm,
                            ref, pub
                          FROM entries
                          ORDER BY date_norm DESC, time_norm DESC''')
    rows = cur.fetchall()

    # categories
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, title, tags
                          FROM categories
                          ORDER BY id ASC''')
    categories = cur.fetchall()

    # insert changelog
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, entry_id, mod_type,
                           date_norm, time_norm, pub
                          FROM changelog
                          ORDER BY date_norm DESC, time_norm DESC''')
    change_rows = cur.fetchall()

    changes = []
    for change_row in change_rows:
        change = {}
        for i, v in enumerate(change_row):
            change.update( { change_row.keys()[i]: v } )
            cur = g.db.execute('''SELECT title FROM entries
                                  WHERE id = ?''', (change_row['entry_id'],))
            row = cur.fetchone()
            if row == None:
                entry_title = "DELETED_ENTRY"
            else:
                entry_title = row[0]
            change.update( { 'entry_title': entry_title } )
        changes.append(change)

    return render_template( 'overview.html',
                            title = "Overview",
                            entries = rows,
                            categories = categories,
                            changes = changes )

@interface.route('/edit', methods=['GET', 'POST'])
def edit():
    '''edit a page entry'''
    if not session.get('logged_in'):
        abort(401)

    # POST
    # button pressed on edit page (preview / save / cancel)
    if request.method == 'POST':
        action = request.form['actn']
        if action == "cancel":
            return redirect(url_for('interface.overview'))

        # request data and instantiate Page object
        type = request.form['type']
        if type == 'custom':
            custom_type = request.form['custom_type']
            if custom_type == '':
                type = 'undefined'
                flash("Warning: custom type not specified, setting to undefined.")
            else:
                type = custom_type

        page_obj = Page( request.form['id'],
                         type,
                         request.form['title'],
                         current_app.config['AUTHOR_NAME'],
                         #request.form['date'],
                         #request.form['time'],
                         datetime.now().strftime('%Y-%m-%d'),
                         datetime.now().strftime('%H:%M'),
                         request.form['tags'],
                         request.form['text-input'] )

        # actions

        # add images from subpath
        if action == "add_imgs":
            images_subpath = request.form['imagepath']

            # create and add image markdown
            images = get_images_from_path(images_subpath)
            img_md = gen_image_md(images_subpath, images)

            # update object
            page_obj.body_md = page_obj.body_md + img_md
            page_obj.update_images()

            # return
            return render_template( 'edit.html',
                                    preview = False,
                                    id = page_obj.id,
                                    page = page_obj,
                                    images = page_obj.images )

        # upload selected images
        elif action == "upld_imgs":
            if not request.files.getlist("files"):
                abort(404)
            else:
                files = request.files.getlist("files")

            filenames = []
            for file in files:
                if file and allowed_image_file(file.filename):
                    subpath = gen_image_subpath()
                    filename = secure_filename(file.filename)
                    filepath_abs = os.path.join( current_app.config['RUN_ABSPATH'],
                                                 'media',
                                                 subpath,
                                                 filename )
                    if not os.path.isfile(filepath_abs):
                        file.save(filepath_abs)
                    else:
                        flash("File w/ same name already present, not saved: {}".format(filename))

                    filenames.append(filename)

                else:
                    flash("Not a valid image file: {}".format(file.filename))

            if filenames != []:
                # generate markdown
                img_md = gen_image_md(subpath, filenames)

                # update object
                page_obj.body_md = page_obj.body_md + img_md
                page_obj.update_images()

            # return to edit
            return render_template( 'edit.html',
                                    preview = False,
                                    id = page_obj.id,
                                    page = page_obj,
                                    images = page_obj.images )

        elif action == "preview" or action == "save":

            if action == "preview":
                return render_template( 'edit.html',
                                         preview = True,
                                         id = page_obj.id,
                                         page = page_obj,
                                         images = page_obj.images )
            elif action == "save":
                if page_obj.id == "new":
                    page_obj.db_write_new_entry()
                    flash("New Page saved successfully!")
                else:
                    page_obj.db_update_entry()
                    flash("Page ID {} saved successfully!".format(page_obj.id))
                return redirect(url_for('interface.overview'))
        else:
            abort(404)

    # GET
    # (loading from overview)
    else:
        id = request.args.get('id')

        if id == "new":
            # create new
            return render_template( 'edit.html',
                                    preview = False,
                                    id = id,
                                    page = None )
        elif id == None:
            # abort for now
            abort(404)
        else:
            row = db_load_to_edit(id)
            return render_template( 'edit.html',
                                    preview = False,
                                    id = id,
                                    page = row,
                                    images = get_images_from_md(row['body_md']) )

@interface.route('/edit_category', methods=['GET', 'POST'])
def edit_category():
    '''edit/create a category'''
    if not session.get('logged_in'):
        abort(401)

    # POST
    # button pressed on edit page (preview / save / cancel)
    if request.method == 'POST':
        action = request.form['actn']
        if action == "cancel":
            return redirect(url_for('interface.overview'))
        elif action == "store":
            db_store_category( request.form['id'],
                               request.form['title'],
                               request.form['tags'] )
            flash("Category stored: {}".format(request.form['title']))
            return redirect(url_for('interface.overview'))

    # GET
    # (loading from overview)
    else:
        id = request.args.get('id')

        if id == "new":
            # create new
            return render_template( 'edit_category.html',
                                    id = id,
                                    category = None )
        elif id == None:
            # abort for now
            abort(404)
        else:
            #row = db_load_to_edit(id)
            row = db_load_category(id)
            return render_template( 'edit_category.html',
                                    id = id,
                                    category = row )

@interface.route('/new')
def new():
    '''create new page using editor'''
    if not session.get('logged_in'):
        abort(401)

    return render_template( 'edit.html', preview=False, id="new", \
                            new=True, page=None )

@interface.route('/pub-change')
def pub_change():
    '''publish change'''
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    if id == None:
        abort(404)

    # change state
    update_pub_change(id, 1)
    flash('Published change ID: {}'.format(id))

    return redirect(url_for('interface.overview'))

@interface.route('/unpub-change')
def unpub_change():
    '''unpublish change'''
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    if id == None:
        abort(404)

    # change state
    update_pub_change(id, 0)
    flash('Unpublished change ID: {}'.format(id))

    return redirect(url_for('interface.overview'))

@interface.route('/pub')
def pub():
    '''publish entry'''
    # --> make this and unpub below single function
    # ==> this didn't work for galleries ! didn't it ?

    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    if id == None:
        abort(404)

    # change state
    update_pub(id, 1)

    flash('Published ID {}'.format(id))

    return redirect(url_for('interface.overview'))

@interface.route('/unpub')
def unpub():
    '''unpublish entry'''
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    if id == None:
        abort(404)

    # change state
    update_pub(id, 0)

    flash('Unpublished ID {}'.format(id))

    return redirect(url_for('interface.overview'))

@interface.route('/export_entries')
def export_entries():
    '''export db entries to json (on server)'''
    if not session.get('logged_in'):
        abort(401)

    # get the entries to export
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref, type, title, author,
                            date_norm, time_norm, body_html, body_md,
                            tags, pub
                           FROM entries
                           ORDER BY id ASC''' )
    rows = cur.fetchall()

    # create list
    entries = []
    for row in rows:

        entry = {}
        for i, v in enumerate(row):
            entry.update( { row.keys()[i]: v } )

        entries.append(entry)

    # dump json
    #entries_json = json.dumps(entries)

    with open(current_app.config['DB_ENTRIES_JSON_DUMP'], 'w') as f:
        json.dump(entries, f)

    flash("Dumped json to {}".format(current_app.config['DB_ENTRIES_JSON_DUMP']))
    return redirect(url_for('interface.overview'))

@interface.route('/import_entries')
def import_entries():
    '''import db entries from json (on server)'''
    if not session.get('logged_in'):
        abort(401)

    # read json
    with open(current_app.config['DB_ENTRIES_JSON_DUMP'], 'r') as f:
        entries = json.load(f)

    # instantiate pages and write to db

    for entry in entries:

        # check if already present
        cur = g.db.execute( '''SELECT ref
                               FROM entries
                               WHERE id = ?''', (entry['id'],))
        row = cur.fetchone()

        if row != None:
            flash("Entry already in db: ID: {} ref: {}".format( entry['id'],
                                                               row[0] ))
            continue

        page_obj = Page( entry['id'],
                         entry['type'],
                         entry['title'],
                         entry['author'],
                         entry['date_norm'],
                         entry['time_norm'],
                         entry['tags'],
                         entry['body_md'],
                         entry['pub'] )

        page_obj.db_write_new_entry()

        flash("Imported entry ID: {}".format(entry['id']))

    return redirect(url_for('interface.overview'))
