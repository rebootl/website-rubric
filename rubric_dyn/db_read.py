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

def get_cat_by_ref(cat_ref):
    '''get category data, abort if not exists'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT * FROM categories
                          WHERE ref = ?''', (cat_ref,))
    row = cur.fetchone()
    if row is None:
        abort(404)
    return row

def get_cat_items():
    '''get category items for menu'''
    cur = g.db.execute('''SELECT * FROM categories
                          ORDER BY title ASC''')
    return cur.fetchall()

def get_entries_by_cat(cat_id, n):
    '''get n entries by category (id)'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT * FROM entries
                          WHERE ( type = 'note' OR TYPE = 'blog' )
                           AND pub = 1
                           AND cat_id = ?
                          ORDER BY date_norm DESC, time_norm DESC
                          LIMIT ? ''', (cat_id, n))
    return cur.fetchall()

def get_entries_for_home(n):
    '''get n entries of type blog for the home view'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT * FROM entries
                          WHERE type = 'blog'
                           AND pub = 1
                          ORDER BY date_norm DESC, time_norm DESC
                          LIMIT ?''', (n,))
    return cur.fetchall()

def get_ref(id):
    cur = g.db.execute( '''SELECT ref
                           FROM entries
                           WHERE id = ?''', (id,) )
    row = cur.fetchone()
    if row is None:
        abort(404)

    return row[0]

def get_numentries(date):
    '''get number of untitled entries for date'''
    cur = g.db.execute( '''SELECT id
                           FROM entries
                           WHERE date_norm = ?''',
                        (date,))
    rows = cur.fetchall()
    return len(rows)

def get_entry_by_date_ref(date, ref, published=True):
    '''return entry data from db, by <date>/<ref>'''
    if published == True:
        pub = 1
    else:
        pub = 0
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT * FROM entries
                           WHERE date_norm = ?
                           AND ref = ?
                           AND ( type = 'note' OR type = 'blog' )
                           AND pub = ?''', (date, ref, pub) )
    row = cur.fetchone()
    if row is None:
        abort(404)
    return row

def db_load_category(id):
    '''load category'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, title, tags
                          FROM categories
                          WHERE id = ?''', (id,))
    row = cur.fetchone()
    if row is None:
        abort(404)
    return row

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
    if row is None:
        abort(404)
    return row

# --> use get_entry_by_id above ^^
def db_load_to_edit(id):
    '''gets page data by id'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT ref, title, author, date_norm, time_norm,
                           tags, type, body_md
                          FROM entries
                          WHERE id = ?
                          LIMIT 1''', (id,))
    row = cur.fetchone()
    if row == None:
        abort(404)
    return row
