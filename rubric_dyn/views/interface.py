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
from rubric_dyn.db_write import db_new_entry, db_update_entry, update_pub
from rubric_dyn.helper_interface import process_input, get_images, \
    gen_image_md, get_images_from_md, gen_image_subpath, allowed_image_file
from rubric_dyn.ExifNice import ExifNice

interface = Blueprint('interface', __name__,
                      template_folder='../templates/interface')

FLASH_WARN_EMPTY_STR = "Warning: {} can not be empty. Setting to 'NOT_SET'."

### functions returning a "view"

# --> deprecated
#def render_preview(id, ref, type, title, author, date_normed, time_normed, 
#                   tags, body_html, body_md):
#    '''process text input into preview and reload the editor page'''
#
#    page = { 'id': id,
#             'ref': ref,
#             'type': type,
#             'title': title,
#             'author': author,
#             'date_norm': date_normed,
#             'time_norm': time_normed,
#             'body_html': body_html,
#             'img_exifs_json': None,
#             'tags': tags,
#             'body_md': body_md }
#
#    # render stuff
#    return render_template( 'edit.html',
#                            preview = True,
#                            id = id,
#                            page = page,
#                            images = get_images_from_md(body_md) )

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

        # request data, check and set defaults if necessary
        # --> check and defaults could go in a helper func.... ?!?!
        type = request.form['type']
        if type == 'custom':
            custom_type = request.form['custom_type']
            if custom_type == '':
                type = 'undefined'
                flash("Warning: custom type not specified, setting to undefined.")
            else:
                type = custom_type

        title = request.form['title']
        if title == "":
            title = 'NOT_SET'
            flash(FLASH_WARN_EMPTY_STR.format("Title"))

        # --> simplify
        date_str = request.form['date']
        date_normed = date_norm2(date_str, "%Y-%m-%d")
        if not date_normed:
            date_normed = "NOT_SET"
            flash("Warning: bad date format..., setting to 'NOT_SET'.")
        time_str = request.form['time']
        time_normed = time_norm(time_str, "%H:%M")
        if not time_normed:
            time_normed = "NOT_SET"
            flash("Warning: bad time format..., setting to 'NOT_SET'.")

        # assembly data
        # --> evtl. make obj. for this, e.g. page object
        page_return = { 'id': request.form['id'],
                        'ref': request.form['ref'],
                        'title': title,
                        'author': request.form['author'],
                        'date_norm': date_normed,
                        'time_norm': time_normed,
                        'tags': request.form['tags'],
                        'type': type,
                        'body_md': request.form['text-input'] }

        # actions

        if action == "add_imgs":
            images_subpath = request.form['imagepath']

            # create and add image markdown
            images = get_images(images_subpath)
            img_md = gen_image_md(images_subpath, images)
            body_md_add = page_return['body_md'] + img_md

            # return
            page_return['body_md'] = body_md_add

            images = get_images_from_md(body_md_add)
            return render_template( 'edit.html',
                                    preview = False,
                                    id = page_return['id'],
                                    page = page_return,
                                    images = images )

        elif action == "upld_imgs":
            # --> move into separate func., at least partially ?!?!
            if 'file' not in request.files:
                # --> return unchanged
                # ==> that's illegal, just abort
                abort(404)

            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename (from flask docs)
            if file.filename == '':
                flash('No selected file...')
                # return unchanged
                # --> test
                images = get_images_from_md(page_return['body_md'])
                return render_template( 'edit.html',
                                    preview = False,
                                    id = page_return['id'],
                                    page = page_return,
                                    images = images )

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
                    flash("File w/ same name already present, not saved.")

                # generate markdown
                img_md = gen_image_md(subpath, [ filename ])
                body_md_add = page_return['body_md'] + img_md
                page_return['body_md'] = body_md_add

                # return to edit
                images = get_images_from_md(body_md_add)
                return render_template( 'edit.html',
                                        preview = False,
                                        id = page_return['id'],
                                        page = page_return,
                                        images = images )
            else:
                flash('Not a valid image file...')
                # return unchanged
                # --> test
                images = get_images_from_md(page_return['body_md'])
                return render_template( 'edit.html',
                                        preview = False,
                                        id = page_return['id'],
                                        page = page_return,
                                        images = images )

        elif action == "preview" or action == "save":

            ref_new, body_html = process_input(title, page_return['body_md'])

            page_return.update({ 'ref': ref_new,
                                 'body_html': body_html })

            if action == "preview":
                images = get_images_from_md(page_return['body_md'])
                return render_template( 'edit.html',
                                         preview = True,
                                         id = page_return['id'],
                                         page = page_return,
                                         images = images )
            elif action == "save":
                id = page_return['id']
                if id == "new":
                    db_new_entry(page_return)
                    flash("New Page saved successfully!")
                else:
                    db_update_entry(page_return)
                    flash("Page ID {} saved successfully!".format(id))
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

    # --> fill in date and time

    return render_template( 'edit.html', preview=False, id="new", \
                            new=True, page=None )

@interface.route('/pub')
def pub():
    '''publish entry'''
    # --> make this and unpub below single function

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
