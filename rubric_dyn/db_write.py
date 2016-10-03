'''db write functions (except for Page methods)'''
from datetime import datetime

from flask import g

def db_store_category(id, title, tags):
    '''store category entry'''
    if id == "new":
        g.db.execute('''INSERT INTO categories
                        (title, tags)
                        VALUES
                        (?,?)''', (title, tags))
        g.db.commit()
    else:
        g.db.execute('''UPDATE categories
                        SET title = ?, tags = ?
                        WHERE id = ?''', (title, tags, id))
        g.db.commit()

def db_write_change(id, type):
    '''write to changelog'''
    # get current date and time
    date_curr = datetime.now().strftime('%Y-%m-%d')
    time_curr = datetime.now().strftime('%H:%M')

    g.db.execute( '''INSERT INTO changelog
                     (entry_id, mod_type, date_norm, time_norm)
                     VALUES
                     (?,?,?,?)''',
                  ( id, type, date_curr, time_curr ) )
    g.db.commit()

def update_pub_change(id, pub):
    '''update publish state in database'''
    g.db.execute('''UPDATE changelog
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()

def update_pub(id, pub):
    '''update publish state in database'''
    g.db.execute('''UPDATE entries
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()

# --> deprecated, done in Page class now
def db_new_entry(page_ret):
    '''insert new page entry into database,
keeping "backward compatible" for now (using all parameters)'''

    # retrieve information
    # this is doubling stuff but it helps keeping an overview
    # --> probably a better way would be to use an object !!
    ref = page_ret['ref']
    type = page_ret['type']
    title = page_ret['title']
    author = page_ret['author']
    date_norm = page_ret['date_norm']
    time_norm = page_ret['time_norm']
    tags = page_ret['tags']
    body_md = page_ret['body_md']
    body_html = page_ret['body_html']

    published = 0

    # backward compatibility data
    # --> remove this crap !!!
    date_str = "NOT_SET"
    datetime_norm = "NOT_SET"
    body_md5sum = "NOT_SET"
    meta_json = "NOT_SET"
    data1 = None
    img_exifs_json = None

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

# --> deprecated, done in Page class now
def db_update_entry(page_ret):
    '''update page entry in database,
keeping "backward compatible" for now (using all parameters)'''

    # retrieve information
    # this is doubling stuff but it helps keeping an overview
    # --> probably a better way would be to use an object !!
    id = page_ret['id']
    ref = page_ret['ref']
    type = page_ret['type']
    title = page_ret['title']
    author = page_ret['author']
    date_norm = page_ret['date_norm']
    time_norm = page_ret['time_norm']
    tags = page_ret['tags']
    body_md = page_ret['body_md']
    body_html = page_ret['body_html']

    published = 0

    # backward compatibility data
    # --> remove this crap !!!
    date_str = "NOT_SET"
    datetime_norm = "NOT_SET"
    body_md5sum = "NOT_SET"
    meta_json = "NOT_SET"
    data1 = None
    img_exifs_json = None

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
