'''"backend" interface'''
import os
import sqlite3
import json
from datetime import datetime
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app
from werkzeug.utils import secure_filename

from rubric_dyn.db_read import db_load_category, get_entries_info, \
    get_cat_items, get_changes, get_entry_by_id
from rubric_dyn.db_write import update_pub, db_store_category
from rubric_dyn.common import url_encode_str
from rubric_dyn.helper_interface import gen_image_md, get_images_from_md, \
    upload_images
from rubric_dyn.Page import Page, NewPage

interface = Blueprint('interface', __name__,
                      template_folder='../templates/interface')

### global access control

@interface.before_request
def restrict_access():
    if not session.get('logged_in'):
        abort(401)

### interface overview

@interface.route('/overview', methods=['GET', 'POST'])
def overview():
    '''interface overview'''
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

    id = request.args.get('id')
    if id == None:
        abort(404)

    if id == "new":
        rows = NewPage()
        images = None
    else:
        rows = get_entry_by_id(id)
        images = get_images_from_md(rows['body_md'])

    return render_template('edit.html',
                            preview = False,
                            id = id,
                            page = rows,
                            types = current_app.config['ENTRY_TYPES'],
                            categories = get_cat_items(),
                            images = images)

@interface.route('/edit', methods=['POST'])
def edit_post():
    '''action invoked by buttons on edit page
preview / save / cancel / upload images'''

    # actions
    action = request.form['actn']

    # cancel
    if action == "cancel":
        return redirect(url_for('interface.overview'))

    # instantiate Page object
    page_obj = Page( request.form.get('id'),
                     request.form.get('type'),
                     request.form.get('title'),
                     current_app.config['AUTHOR_NAME'],
                     datetime.now().strftime('%Y-%m-%d'),
                     datetime.now().strftime('%H:%M'),
                     request.form.get('tags'),
                     request.form.get('text-input'),
                     request.form.get('cat_id'),
                     1 if request.form.get('show_home') else 0 )

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
                                types = current_app.config['ENTRY_TYPES'],
                                categories = get_cat_items(),
                                images = page_obj.images )

    elif action == "preview":
        return render_template( 'edit.html',
                                 preview = True,
                                 id = page_obj.id,
                                 page = page_obj,
                                 types = current_app.config['ENTRY_TYPES'],
                                 categories = get_cat_items(),
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
    id = request.args.get('id')
    if id == None:
        abort(404)

    if id == "new":
        row = None
    else:
        row = db_load_category(id)

    return render_template('edit_category.html',
                            id = id,
                            category = row)

@interface.route('/edit_category', methods=['POST'])
def edit_category_post():
    '''actions invoked on edit category page
store / cancel'''

    action = request.form['actn']

    if action == "cancel":
        return redirect(url_for('interface.overview'))
    elif action == "store":
        db_store_category( request.form['id'],
                           url_encode_str(request.form['title']),
                           request.form['title'],
                           request.form['desc'],
                           request.form['tags'] )
        flash("Category stored: {}".format(request.form['title']))
    else:
        abort(404)

    return redirect(url_for('interface.overview'))

### import / export

@interface.route('/export_entries')
def export_entries():
    '''export db entries to json (on server)'''

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
