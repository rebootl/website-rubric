'''"backend" interface'''
import os
import sqlite3
import json
import datetime
import hashlib
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app, make_response
from werkzeug.utils import secure_filename

from rubric_dyn.common import url_encode_str, datetimesec_norm, date_norm2, \
    time_norm
from rubric_dyn.db_read import db_load_to_edit
from rubric_dyn.db_write import update_pub
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
    cur = g.db.execute('''SELECT id, type, title, date_norm, ref, pub
                          FROM entries
                          ORDER BY date_norm DESC, time_norm DESC''')
    rows = cur.fetchall()

    # create link hrefs
    hrefs = {}
    for row in rows:
        if row['type'] == 'article':
            href = os.path.join('/articles', row['date_norm'], row['ref'])
        elif row['type'] == 'special':
            href = os.path.join('/special', row['ref'])
        elif row['type'] == 'note':
            href = os.path.join('/notes', row['ref'])
        else:
            href = "NOT_DEFINED"
        hrefs.update({ row['id']: href })

    return render_template( 'overview.html',
                            entries = rows,
                            title = "Overview",
                            hrefs = hrefs )

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
                         request.form['author'],
                         request.form['date'],
                         request.form['time'],
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

@interface.route('/new')
def new():
    '''create new page using editor'''
    if not session.get('logged_in'):
        abort(401)

    # --> autom. fill in date and time

    return render_template( 'edit.html', preview=False, id="new", \
                            new=True, page=None )

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

# --> currently not fully functional
#     meta data json is missing
#     rework w/ new export/import
# --> never used it up to now...
@interface.route('/download')
def download_text():
    '''download entry text (markdown)'''
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
    #meta = json.loads(meta_json)
    meta = {}
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
