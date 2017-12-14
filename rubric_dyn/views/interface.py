'''"backend" interface'''
import os
import sqlite3
import json
import hashlib
from datetime import datetime
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app
from werkzeug.utils import secure_filename

from rubric_dyn.db_read import db_load_category, get_entries_info, \
    get_cat_items, get_changes, get_entry_by_id
from rubric_dyn.db_write import update_pub, db_store_category
from rubric_dyn.helper_interface import gen_image_md, get_images_from_md, \
    upload_images
from rubric_dyn.Page import Page

interface = Blueprint('interface', __name__,
                      template_folder='../templates/interface')

### login / logout

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
    return redirect(url_for('interface.login'))

### interface overview

@interface.route('/overview', methods=['GET', 'POST'])
def overview():
    '''interface overview'''
    if not session.get('logged_in'):
        abort(401)

    # get all pages
    rows = get_entries_info()

    # categories
    categories = get_cat_items()

    # insert changelog
    changes = get_changes()

    return render_template( 'overview.html',
                            title = "Overview",
                            entries = rows,
                            categories = categories,
                            changes = changes )

### edit / new page

@interface.route('/edit')
def edit():
    '''shows the edit page
edit button / new page'''
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')

    if id == "new":
        return render_template('edit.html',
                                preview = False,
                                id = id,
                                page = None)
    elif id == None:
        abort(404)
    else:
        row = get_entry_by_id(id)
        return render_template('edit.html',
                                preview = False,
                                id = id,
                                page = row,
                                types = current_app.config['ENTRY_TYPES'],
                                categories = get_cat_items(),
                                images = get_images_from_md(row['body_md']))

@interface.route('/edit', methods=['POST'])
def edit_post():
    '''action invoked by buttons on edit page
preview / save / cancel / upload images'''
    if not session.get('logged_in'):
        abort(401)

    # actions
    action = request.form['actn']

    # cancel
    if action == "cancel":
        return redirect(url_for('interface.overview'))

    # instantiate Page object
    page_obj = Page( request.form['id'],
                     request.form['type'],
                     request.form['custom_type'],
                     request.form['title'],
                     current_app.config['AUTHOR_NAME'],
                     datetime.now().strftime('%Y-%m-%d'),
                     datetime.now().strftime('%H:%M'),
                     request.form['tags'],
                     request.form['text-input'] )

    # upload selected images
    if action == "upld_imgs":
        if not request.files.getlist("files"):
            abort(404)

        filenames = upload_images(request.files.getlist("files"))

        # generate markdown
        if filenames != []:
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

### publish / unpublish buttons

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

### edit categories

@interface.route('/edit_category')
def edit_category():
    '''show the edit category page
edit / new category buttons'''
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    if id == "new":
        return render_template( 'edit_category.html',
                                id = id,
                                category = None )
    elif id == None:
        abort(404)
    else:
        row = db_load_category(id)
        return render_template( 'edit_category.html',
                                id = id,
                                category = row )

@interface.route('/edit_category', methods=['POST'])
def edit_category_post():
    '''actions invoked on edit category page
store / cancel'''
    action = request.form['actn']
    if action == "cancel":
        return redirect(url_for('interface.overview'))
    elif action == "store":
        db_store_category( request.form['id'],
                           request.form['title'],
                           request.form['tags'] )
        flash("Category stored: {}".format(request.form['title']))
        return redirect(url_for('interface.overview'))

### import / export

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
