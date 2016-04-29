'''"backend" interface'''
import os
import sqlite3
import json
import datetime
import hashlib
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app, make_response

from rubric_dyn.common import url_encode_str, datetimesec_norm, date_norm2
from rubric_dyn.db_read import db_load_gallery, db_load_images
from rubric_dyn.db_write import update_pub, db_update_image, \
    db_insert_gallery, db_update_gallery, db_pub_gallery, \
    db_new_entry, db_update_entry
from rubric_dyn.helper_interface import process_image, process_input
from rubric_dyn.ExifNice import ExifNice

interface = Blueprint('interface', __name__,
                      template_folder='../templates/interface')

### functions returning a "view"

def render_preview(id, type, title, author, date_str, time_str, tags, body_md):
    '''process text input into preview and reload the editor page'''

    #meta, body_html, img_exifs_json = process_edit(text_input)
    ref, \
    date_normed, \
    time_normed, \
    body_html, \
    img_exifs_json = process_input(title, date_str, time_str, body_md)

    # --> simplify
    #date_normed, \
    #time_normed, \
    #datetime_normed = date_norm( meta['date'],
    #                             current_app.config['DATETIME_FORMAT'],
    #                             current_app.config['DATE_FORMAT'] )

    # --> needed ?
    #if img_exifs_json == "":
    #    img_exifs_json = False

    # --> simplify !!
    #if 'tags' in meta.keys():
    #    tags = meta['tags']
    #else:
    #    tags = None

    # prepare stuff for post.html template ??
    # --> simplify / streamline
    #db = { 'title': meta['title'],
    #       'date_norm': date_normed,
    #       'body_html': body_html }
    #entry = { 'db': db,
    #          'tags': tags }

    page = { 'id': id,
             'ref': ref,
             'type': type,
             'title': title,
             'author': author,
             'date_norm': date_normed,
             'time_norm': time_normed,
             'body_html': body_html,
             'img_exifs_json': None,
             'tags': tags,
             'body_md': body_md }

    # render stuff
    return render_template( 'edit.html',
                            preview = True,
                            id = id,
                            page = page )
                            #text = text_input,
                            #type = meta['type'],
                            #entry = entry,
                            #img_exifs_json = img_exifs_json )

def load_to_edit(id):
    '''load editor page for id'''
    # --> make this a db function !!

    # get data for the page to edit
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT ref, title, author, date_norm, time_norm,
                           tags, type, body_md
                          FROM entries
                          WHERE id = ?
                          LIMIT 1''', (id,))
    #meta_json, body_md = cur.fetchone()
    page = cur.fetchone()

    # --> catch not found

    # assemble body
    #text = '%%%'.join((meta_json, body_md))

    return render_template( 'edit.html', preview=False, id=id, \
                            page=page )

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
    return render_template('login.html', error=error, title="Login")

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
                          ORDER BY datetime_norm DESC''')
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

    # galleries
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, title, desc, date_norm,
                           tags, pub
                          FROM galleries
                          ORDER BY date_norm DESC''')
    gal_rows = cur.fetchall()

    # images
    # --> commented out for now
    #g.db.row_factory = sqlite3.Row
    #cur = g.db.execute('''SELECT id, ref, caption, datetime_norm,
    #                       gallery_id, thumb_ref
    #                      FROM images
    #                      ORDER BY datetime_norm DESC''')
    #img_rows = cur.fetchall()

    # --> catch not found ?? ==> what for ?

    return render_template( 'overview.html',
                            entries = rows,
                            title = "Overview",
                            hrefs = hrefs,
                            #images = img_rows,
                            galleries = gal_rows )

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

        id = request.form['id']

        # meta
        type = request.form['type']
        title = request.form['title']
        author = request.form['author']
        date_str = request.form['date']
        time_str = request.form['time']
        tags = request.form['tags']

        body_md = request.form['text-input']

        ref, \
        date_normed, \
        time_normed, \
        body_html, \
        img_exifs_json = process_input(title, date_str, time_str, body_md)

        if action == "preview":
            return render_preview(id, type, title, author, date_str, time_str, \
                                  tags, body_md)
        elif action == "save":
            if id == "new":
                #page_inst = NewPage(text_input)
                #page_inst.save_new()
                db_new_entry( ref, type, title, author, date_normed,
                              time_normed, tags, body_md, body_html,
                              img_exifs_json )
                flash("New Page saved successfully!")
            else:
                #page_inst = EditPage(id, text_input)
                #page_inst.save_edit()
                db_update_entry( id, ref, type, title, author, date_normed,
                                 time_normed, tags, body_md, body_html,    
                                 img_exifs_json )
                flash("Page ID {} saved successfully!".format(id))
            return redirect(url_for('interface.overview'))
        else:
            abort(404)

    # GET
    # loading from overview
    else:
        id = request.args.get('id')

        if id == "new":
            # create new
            # --> is this currently ever used/reached ??? ==> yes, why not ?
            type = request.args.get('type')
            return load_to_edit_new(type)

        elif id == None:
            # --> abort for now
            abort(404)

        else:
            return load_to_edit(id)

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

    # change state
    update_pub(id, 0)

    flash('Unublished ID {}'.format(id))

    return redirect(url_for('interface.overview'))

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

# DEPRECATED
# not needed anymore due to new exif processing
#
#@interface.route('/recreate_exifs')
#def recreate_exifs():
#    '''"hidden url" recreate all exif information
#this was used to create exif information for files
#of already existing entries'''
#    if not session.get('logged_in'):
#        abort(401)
#
#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute('''SELECT id, meta_json
#                          FROM entries''')
#    rows = cur.fetchall()
#
#    for row in rows:
#        meta = process_meta_json(row['meta_json'])
#
#        img_exifs_json = create_exifs_json(meta['files'])
#
#        g.db.execute('''UPDATE entries
#                        SET exifs_json = ?
#                        WHERE id = ?''', (img_exifs_json, row['id']))
#        g.db.commit()
#
#    flash('Updated EXIF data successfully.')
#    return redirect(url_for('interface.overview'))

@interface.route('/update_galleries')
def update_galleries():
    '''"hidden url" update galleries from directory: media/galleries,
also inserts images into db and creates thumbnails'''
    if not session.get('logged_in'):
        abort(401)

    # absolute paths
    media_abspath = os.path.join(current_app.config['RUN_ABSPATH'], 'media')
    galleries_abspath = os.path.join(media_abspath, 'galleries')
    thumbs_abspath = os.path.join(media_abspath, 'thumbs')

    # get content of the gallery dir
    galleries_files = os.listdir(galleries_abspath)

    # filter
    gallery_dirs = []
    for file in galleries_files:
        file_abspath = os.path.join(galleries_abspath, file)
        if os.path.isdir(file_abspath):
            gallery_dirs.append(file)

    # get gallery refs from db
    cur = g.db.execute('''SELECT ref
                          FROM galleries''')
    rows = cur.fetchall()
    gallery_refs = [ ref[0] for ref in rows ]

    # create a gallery for each dir if not exists
    for gallery_dir in gallery_dirs:
        if gallery_dir in gallery_refs:
            continue
        date_norm = datetime.date.today().strftime("%Y-%m-%d")
        db_insert_gallery(gallery_dir, "", date_norm, "", "")

    # update images in galleries
    for gallery_dir in gallery_dirs:
        # get id
        cur = g.db.execute('''SELECT id
                              FROM galleries
                              WHERE ref = ?''', (gallery_dir,))
        gallery_id = cur.fetchone()[0]
        # get image refs
        cur = g.db.execute('''SELECT ref
                              FROM images
                              WHERE gallery_id = ?''', (gallery_id,))
        rows = cur.fetchall()
        img_refs = [ ref[0] for ref in rows ]
        # get directory content
        dir_abs = os.path.join(galleries_abspath, gallery_dir)
        files = os.listdir(dir_abs)
        # filter images
        image_files = []
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in current_app.config['IMG_EXTS']:
                image_files.append(file)

        # insert in db if not exists
        for image_file in image_files:
            ref = os.path.join('galleries', gallery_dir, image_file)
            if ref not in img_refs:
                image_dir = os.path.join(galleries_abspath, gallery_dir)
                process_image(image_file, image_dir, ref)
                # (--> evtl. flash message)

    return redirect(url_for('interface.overview'))

# DEPRECATED (for now)
# --> rewrite using process_image
#
#@interface.route('/update_images')
#def update_images():
#    '''DEPRECATED USE update_galleries INSTEAD --> evtl. make both usable
#(using process_image)
#---
#"hidden url" update image in database from media directory,
#create thumbnails under media/thumbs
#'''
#    if not session.get('logged_in'):
#        abort(401)
#
#    media_abspath = os.path.join(current_app.config['RUN_ABSPATH'], 'media')
#
#    # get content of the media dir
#    media_files = os.listdir(media_abspath)
#
#    # filter out images
#    image_files = []
#    for file in media_files:
#        # --> join not needed, think
#        file_ext = os.path.splitext(os.path.join(media_abspath, file))[1]
#        if file_ext in current_app.config['IMG_EXTS']:
#            image_files.append(file)
#
#    # get image refs from db
#    cur = g.db.execute('''SELECT ref
#                          FROM images''')
#    rows = cur.fetchall()
#    refs = [ ref[0] for ref in rows ]
#
#    # insert in db if not exists
#    for image_file in image_files:
#        if image_file not in refs:
#            # extract exif into json
#            if os.path.splitext(image_file)[1] in current_app.config['JPEG_EXTS']:
#                img_exif = ExifNice(os.path.join(media_abspath, image_file))
#                if img_exif.has_exif:
#                    exif_json = img_exif.get_json()
#                    datetime_norm = datetimesec_norm( img_exif.datetime,
#                                                      "%Y:%m:%d %H:%M:%S" )
#                else:
#                    exif_json = ""
#                    datetime_norm = ""
#            else:
#                exif_json = ""
#                datetime_norm = ""
#
#            # insert in db
#            #db_insert_image(image_file, datetime_norm, exif_json)
#            # (--> flash message)
#
#    # create thumbnail if not exists
#    # get thumbs --> ??? not used...
#    thumbs = os.listdir(os.path.join(media_abspath, 'thumbs'))
#
#    for file in image_files:
#        make_thumb_samename( os.path.join(media_abspath, file),
#                             os.path.join(media_abspath, 'thumbs') )
#
#    #return str(image_files)
#    return redirect(url_for('interface.overview'))

@interface.route('/edit_image', methods=[ 'GET', 'POST' ])
def edit_image():

    if not session.get('logged_in'):
        abort(401)

    # POST
    # button pressed on edit page (preview / save / cancel)
    if request.method == 'POST':
        action = request.form['actn']
        id = request.form['id']
        gal_id = request.form['gal-id']
        if action == "cancel":
            return redirect(url_for( 'interface.edit_gallery',
                                     id = gal_id,
                                     _anchor = 'image-'+id ))
        elif action == "save":
            # get stuff
            caption = request.form['caption']
            datetime_str = request.form['datetime']
            datetime_normed = datetimesec_norm(datetime_str, "%Y-%m-%d %H:%M:%S")
            if not datetime_normed:
                datetime_normed = None
                flash("Warning: bad datetime format..., set to None.")
            # --> verify
            #try:
            #    int(gal_id)
            #except ValueError:
            #    gal_id = None
            #    flash("Warning: gallery_id must be an integer, set to None.")
            # save stuff
            db_update_image(id, caption, datetime_normed)
            flash("Updated image meta information: {}".format(id))
            return redirect(url_for( 'interface.edit_gallery',
                                     id = gal_id,
                                     _anchor = 'image-'+id ))
        else:
            abort(404)

    # GET
    id = request.args.get('id')

    # image
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, caption, datetime_norm,
                           exif_json, gallery_id
                          FROM images
                          WHERE id = ?''', (id,))
    row = cur.fetchone()

    if row == None:
        abort(404)

    try:
        exif = json.loads(row['exif_json'])
    except json.decoder.JSONDecodeError:
        exif = None

    return render_template( 'edit_image.html',
                             image = row,
                             image_exif = exif )

@interface.route('/pub_gallery')
def pub_gallery():
    '''publish/unpublish gallery'''
    if not session.get('logged_in'):
        abort(401)

    id = request.args.get('id')
    pub = request.args.get('pub')

    if id == None:
        abort(404)

    # change state
    if pub == "1":
        db_pub_gallery(id, '1')
        flash('Published Gallery ID {}'.format(id))
    elif pub == "0":
        db_pub_gallery(id, '0')
        flash('Unpublished Gallery ID {}'.format(id))
    else:
        abort(404)

    return redirect(url_for('interface.overview'))


@interface.route('/edit_gallery', methods=[ 'GET', 'POST' ])
def edit_gallery():

    if not session.get('logged_in'):
        abort(401)

    # POST
    if request.method == 'POST':
        action = request.form['actn']
        id = request.form['id']
        if action == "cancel":
            return redirect(url_for('interface.overview'))
        elif action == "save":
            # get stuff
            #caption = request.form['caption']
            title = request.form['title']
            date = request.form['date']
            desc = request.form['desc']
            tags = request.form['tags']
            # --> evtl. process tags ==> maybe not... ??
            # process
            # --> is ref really needed here ???
            date_normed = date_norm2(date, "%Y-%m-%d")
            # (debug)
            #return str(action)
            if not date_normed:
                date_normed = None
                flash("Warning: bad date format..., set to None.")
            if not title or title == "":
                flash("Warning: title must be set, returning.")
                return redirect(url_for('interface.edit_gallery', id=id))
            if id == "new":
                ref = url_encode_str(title)
                db_insert_gallery(ref, title, date_normed, desc, tags)
                flash("Created new gallery {}.".format(title))
                return redirect(url_for('interface.overview'))
            else:
                db_update_gallery(id, title, date_normed, desc, tags)
                flash("Updated Gallery information, id: {}".format(id))
                return redirect(url_for('interface.overview'))
        else:
            abort(404)

    # GET
    id = request.args.get('id')

    if id == None:
        abort(404)

    if id != "new":
        # load stuff
        row = db_load_gallery(id)
    else:
        row = { 'id': id }

    # get images
    images = db_load_images(id)

    return render_template( 'edit_gallery.html',
                            gallery = row,
                            images = images )
