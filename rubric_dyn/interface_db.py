'''interface db functions (except for Page methods)'''
import sqlite3
from flask import g

def update_pub(id, pub):
    '''update publish state in database'''
    g.db.execute('''UPDATE entries
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()

# --> cleanup gallery_id
def db_insert_image(img_ref, thumb_ref, datetime_norm, exif_json, gallery_id=None):
    '''insert image into db'''
    g.db.execute( '''INSERT INTO images
                      (ref, thumb_ref, datetime_norm, exif_json, gallery_id)
                     VALUES (?,?,?,?,?)''',
                  ( img_ref,
                    thumb_ref,
                    datetime_norm,
                    exif_json,
                    gallery_id ) )
    g.db.commit()

def db_update_image(id, caption, datetime_norm):
    '''update image informations in db'''
    g.db.execute( '''UPDATE images
                     SET caption = ?, datetime_norm = ?
                     WHERE id = ?''',
                  (caption, datetime_norm, id) )
    g.db.commit()

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

def db_insert_gallery(ref, title, date_norm, desc, tags):
    '''create new gallery in db'''
    g.db.execute( '''INSERT INTO galleries
                      (ref, title, date_norm, desc, tags)
                     VALUES (?,?,?,?,?)''',
                  (ref, title, date_norm, desc, tags) )
    g.db.commit()

def db_update_gallery(id, title, date_norm, desc, tags):
    '''update gallery entry in db'''
    g.db.execute( '''UPDATE galleries
                     SET title = ?, date_norm = ?, desc = ?, 
                      tags = ?
                     WHERE id = ?''',
                  (title, date_norm, desc, tags, id) )
    g.db.commit()

def db_pub_gallery(id, pub):
    '''publish/unpublish gallery, db function'''
    g.db.execute('''UPDATE galleries
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()
