'''db write functions (except for Page methods)'''
#import sqlite3
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

def db_new_entry( ref, type, title, author, date_norm, time_norm,
                  tags, body_md, body_html, img_exifs_json,
                  published = 0,
                  date_str = "NOT_SET", datetime_norm = "NOT_SET",
                  body_md5sum = "NOT_SET", meta_json = "NOT_SET",
                  data1 = None ):
    '''insert new page entry into database,
keeping "backward compatible" for now (using all parameters)'''
    g.db.execute( '''INSERT INTO entries
                     (ref, type, title, author,
                      date_str, datetime_norm, date_norm,
                      time_norm, body_html, body_md5sum,
                      meta_json, body_md, data1, pub, exifs_json,
                      tags)
                     VALUES
                     (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                  ( ref, type, title, author,
                    date_str, datetime_norm, date_norm,
                    time_norm, body_html, body_md5sum,
                    meta_json, body_md, data1,
                    published, img_exifs_json, tags ) )
    g.db.commit()

def db_update_entry( id, ref, type, title, author, date_norm,
                     time_norm, tags, body_md, body_html,
                     img_exifs_json,
                     date_str = "NOT_SET", datetime_norm = "NOT_SET",
                     body_md5sum = "NOT_SET", meta_json = "NOT_SET",
                     data1 = None ):
    '''update page entry in database,
keeping "backward compatible" for now (using all parameters)'''
    g.db.execute( '''UPDATE entries
                     SET ref = ?, type = ?, title = ?, author = ?,
                      date_str = ?, datetime_norm = ?, date_norm = ?,
                      time_norm = ?, body_html = ?, body_md5sum = ?,
                      meta_json = ?, body_md = ?, data1 = ?,
                      exifs_json = ?, tags = ?
                     WHERE id = ?''',
                  ( ref, type, title, author,
                    date_str, datetime_norm, date_norm,
                    time_norm, body_html, body_md5sum,
                    meta_json, body_md, data1,
                    img_exifs_json, tags, id ) )
    g.db.commit()
