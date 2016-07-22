'''db write functions (except for Page methods)'''
from flask import g

def update_pub(id, pub):
    '''update publish state in database'''
    g.db.execute('''UPDATE entries
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
