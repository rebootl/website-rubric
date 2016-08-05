'''Page object'''

from rubric_dyn.common import date_norm2, time_norm
from rubric_dyn.helper_interface import process_input, get_images_from_md

from flask import flash, g

class Page:

    def __init__(self, id, type, title, author,
                 date_str, time_str, tags, body_md,
                 pub=0):
        '''assembling data,
norm and set defaults if necessary'''

        self.id = id
        self.type = type

        if title == "":
            self.title = 'NOT_SET'
            flash("Warning: Title can not be empty. Setting to 'NOT_SET'.")
        else:
            self.title = title

        self.author = author

        self.date_norm = date_norm2(date_str, "%Y-%m-%d")
        if not self.date_norm:
            self.date_norm = "NOT_SET"
            flash("Warning: bad date format..., setting to 'NOT_SET'.")
        self.time_norm = time_norm(time_str, "%H:%M")
        if not self.time_norm:
            self.time_norm = "NOT_SET"
            flash("Warning: bad time format..., setting to 'NOT_SET'.")

        self.tags = tags
        self.body_md = body_md
        self.pub = pub

        # process input
        self.ref, self.body_html = process_input(self.title, self.body_md)

        # backward compatibility data
        # --> remove this crap !!!
        self.date_str = "NOT_SET"
        self.datetime_norm = "NOT_SET"
        self.body_md5sum = "NOT_SET"
        self.meta_json = "NOT_SET"
        self.data1 = None
        self.img_exifs_json = None

        self.update_images()

    def update_images(self):
        self.images = get_images_from_md(self.body_md)

    def db_write_new_entry(self):
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
                      ( self.ref, self.type, self.title, self.author,
                        self.date_str, self.datetime_norm, self.date_norm,
                        self.time_norm, self.body_html, self.body_md5sum,
                        self.meta_json, self.body_md, self.data1,
                        self.pub, self.img_exifs_json, self.tags ) )
        g.db.commit()

    def db_update_entry(self):
        '''update page entry in database,
keeping "backward compatible" for now (using all parameters)'''
        g.db.execute( '''UPDATE entries
                         SET ref = ?, type = ?, title = ?, author = ?,
                          date_str = ?, datetime_norm = ?, date_norm = ?,
                          time_norm = ?, body_html = ?, body_md5sum = ?,
                          meta_json = ?, body_md = ?, data1 = ?,
                          exifs_json = ?, tags = ?
                         WHERE id = ?''',
                      ( self.ref, self.type, self.title, self.author,
                        self.date_str, self.datetime_norm, self.date_norm,
                        self.time_norm, self.body_html, self.body_md5sum,
                        self.meta_json, self.body_md, self.data1,
                        self.img_exifs_json, self.tags, self.id ) )
        g.db.commit()
