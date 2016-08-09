'''db read functions'''
import os
import sqlite3
from flask import g, abort

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

def get_latest():
    '''get latest entry id (used for changelog)'''
    cur = g.db.execute('''SELECT id FROM entries
                          ORDER BY id DESC
                          LIMIT 1''')
    row = cur.fetchone()
    if row != []:
        return row[0]
    else:
        return None

def get_entrylist(type):
    '''return rows of entries'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT body_html, date_norm
                           FROM entries
                           WHERE type = ?
                           AND pub = 1
                           ORDER BY date_norm DESC''',
                           (type,) )
    rows = cur.fetchall()
    return rows

def get_entrylist_limit(type, limit):
    '''return rows of entries'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT body_html, date_norm
                           FROM entries
                           WHERE type = ?
                           AND pub = 1
                           ORDER BY date_norm DESC
                           LIMIT ?''',
                           (type, limit) )
    rows = cur.fetchall()
    return rows

def get_entry_by_date_ref_path(date_ref_path, type, published=True):
    '''return entry data from db, by <date>/<ref> path'''
    date, ref = os.path.split(date_ref_path)

    if published == True:
        pub = 1
    else:
        pub = 0

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, type, ref, title, date_norm, time_norm,
                            body_html, tags
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
                            body_html, tags
                           FROM entries
                           WHERE ref = ?
                           AND type = ?
                           AND pub = ?''', (ref, type, pub))
    row = cur.fetchone()
    # (catch not found !!!)
    if row is None:
        abort(404)

    return row

def db_load_to_edit(id):
    '''load editor page for id'''
    # get data for the page to edit
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT ref, title, author, date_norm, time_norm,
                           tags, type, body_md
                          FROM entries
                          WHERE id = ?
                          LIMIT 1''', (id,))
    row = cur.fetchone()
    # catch not found
    if row == None:
        abort(404)

    return row
