'''Page object'''

from rubric_dyn.common import date_norm2, time_norm, url_encode_str
from rubric_dyn.helper_interface import process_input, get_images_from_md
from rubric_dyn.db_read import get_latest, get_numentries, get_ref
from rubric_dyn.db_write import db_write_change

from flask import flash, g

class Page:

    def __init__(self, id, type, title, author,
                 date_str, time_str, tags, body_md,
                 show_home, pub=0):
        '''assembling data,
norm and set defaults if necessary'''

        self.id = id
        self.type = type

        if title == "":
            self.title = 'NOT_SET'
            flash("Warning: No title given, setting to 'NOT_SET'.")
        else:
            self.title = title

        self.date_norm = date_norm2(date_str, "%Y-%m-%d")
        if not self.date_norm:
            self.date_norm = "NOT_SET"
            flash("Warning: bad date format..., setting to 'NOT_SET'.")
        self.time_norm = time_norm(time_str, "%H:%M")
        if not self.time_norm:
            self.time_norm = "NOT_SET"
            flash("Warning: bad time format..., setting to 'NOT_SET'.")

        self.author = author

        self.tags = tags
        self.body_md = body_md
        self.show_home = show_home
        self.pub = pub

        # process input
        self.body_html = process_input(self.body_md)

        self.update_images()

    def update_images(self):
        self.images = get_images_from_md(self.body_md)

    def db_write_new_entry(self):
        '''insert new page entry into database,
keeping "backward compatible" for now (using all parameters)'''
        # 'entry-ref_' + increment number of entries
        #  from that date evtl. where title is NOT_SET
        if self.title == 'NOT_SET':
            num = get_numentries(self.date_norm) + 1
            ref = "entry-ref_" + str(num)
        else:
            ref = url_encode_str(self.title)

        g.db.execute( '''INSERT INTO entries
                         (ref, type, title, author,
                          date_norm, time_norm,
                          body_html, body_md, tags, pub)
                         VALUES
                         (?,?,?,?,?,?,?,?,?,?)''',
                      ( ref, self.type, self.title, self.author,
                        self.date_norm, self.time_norm,
                        self.body_html, self.body_md,
                        self.tags, self.pub ) )
        g.db.commit()

        # write to changelog
        db_write_change(get_latest(), 'n')

    def db_update_entry(self):
        '''update page entry in database,
keeping "backward compatible" for now (using all parameters)'''
        # if title is NOT_SET never change the ref!
        # else url_enc...
        if self.title == 'NOT_SET':
            ref = get_ref(self.id)
        else:
            ref = url_encode_str(self.title)

        g.db.execute( '''UPDATE entries
                         SET ref = ?, type = ?, title = ?,
                          body_html = ?, body_md = ?, tags = ?
                         WHERE id = ?''',
                      ( ref, self.type, self.title,
                        self.body_html, self.body_md,
                        self.tags, self.id ) )
        g.db.commit()

        # write to changelog
        db_write_change(self.id, 'e')
