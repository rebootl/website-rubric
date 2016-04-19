'''interface db functions (except for Page methods)'''
from flask import g

def update_pub(id, pub):
    '''update publish state in database'''
    g.db.execute('''UPDATE entries
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()

def db_insert_image(img_ref, datetime_norm, exif_json):
    '''insert image into db'''
    g.db.execute( '''INSERT INTO images
                     (ref, datetime_norm, exif_json)
                     VALUES (?,?,?)''',
                  (img_ref, datetime_norm, exif_json) )
    g.db.commit()

def db_update_image(id, caption, datetime_norm, gallery_id):
    '''update image informations in db'''
    g.db.execute( '''UPDATE images
                     SET caption = ?, datetime_norm = ?, gallery_id = ?
                     WHERE id = ?''',
                  (caption, datetime_norm, gallery_id, id) )
    g.db.commit()
