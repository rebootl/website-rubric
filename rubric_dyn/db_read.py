'''db read functions'''
import os
import sqlite3
from flask import g

# (curr. not used)
#def get_entry_by_id(id):
#    '''return entry data from database'''
#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute( '''SELECT type, ref, title, date_norm,
#                            datetime_norm, body_html, data1, exifs_json,
#                            meta_json
#                           FROM entries
#                           WHERE id = ?''', (id,))
#    return cur.fetchone()

def get_entry_by_date_ref_path(date_ref_path, type, published=True):
    '''return entry data from db, by <date>/<ref> path'''

    date, ref = os.path.split(date_ref_path)

    if published == True:
        pub = 1
    else:
        pub = 0

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT type, ref, title, date_norm,
                            datetime_norm, body_html, data1, exifs_json,
                            meta_json
                           FROM entries
                           WHERE date_norm = ?
                           AND ref = ?
                           AND type = ?
                           AND pub = ?''', (date, ref, type, pub))
    row = cur.fetchone()
    # (catch not found !!!)
    if row is None:
        abort(404)

    return row

def get_entry_by_ref(ref, type, published=True):
    '''return entry data from db, by ref'''

    if published == True:
        pub = 1
    else:
        pub = 0

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT type, ref, title, date_norm,
                            datetime_norm, body_html, data1, exifs_json,
                            meta_json
                           FROM entries
                           WHERE ref = ?
                           AND type = ?
                           AND pub = ?''', (ref, type, pub))
    row = cur.fetchone()
    # (catch not found !!!)
    if row is None:
        abort(404)

    return row

def db_load_gallery(id):
    '''load gallery stuff from db'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, title, desc, date_norm,
                           tags
                          FROM galleries
                          WHERE id = ?''', (id,))
    row = cur.fetchone()

    # catch not found
    if row == None:
        abort(404)

    return row

def db_load_images(gallery_id):
    '''load images for given gallery (id)'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, caption, datetime_norm,
                           exif_json, gallery_id, thumb_ref
                          FROM images
                          WHERE gallery_id = ?
                          ORDER BY datetime_norm ASC''', (gallery_id,))
    return cur.fetchall()
