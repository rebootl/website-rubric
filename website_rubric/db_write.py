'''db write functions (except for Page methods)'''
from datetime import datetime

from flask import g

def db_store_category(id, ref, title, desc, tags):
    '''store category entry'''
    if id == "new":
        g.db.execute('''INSERT INTO categories
                        (ref, title, desc, tags)
                        VALUES
                        (?,?,?,?)''', (ref, title, desc, tags))
        g.db.commit()
    else:
        g.db.execute('''UPDATE categories
                        SET ref = ?, title = ?, desc = ?, tags = ?
                        WHERE id = ?''', (ref, title, desc, tags, id))
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

def update_pub(id, pub):
    '''update publish state in database'''
    g.db.execute('''UPDATE entries
                    SET pub = ?
                    WHERE id = ?''', (pub, id))
    g.db.commit()
