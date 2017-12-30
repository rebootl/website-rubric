'''Page object'''

from rubric_dyn.common import date_norm2, time_norm, url_encode_str
from rubric_dyn.helper_interface import process_input, get_images_from_md
from rubric_dyn.db_read import get_latest, get_numentries, get_ref
from rubric_dyn.db_write import db_write_change

from flask import flash, g

class Page:

    def __init__(self, id, type, title, author,
                 date_str, time_str, tags, body_md,
                 cat_id, show_home, pub=0):
        '''assembling data,
norm and set defaults if necessary'''

        self.id = id
        self.type = type

        if title == "":
            self.title = 'NOT_SET'
        else:
            self.title = title

        self.author = author
        self.tags = tags
        self.body_md = body_md
        self.cat_id = cat_id
        self.show_home = show_home
        self.pub = pub

        # process input
        self.body_html = process_input(self.body_md)

        self.update_images()

    def update_images(self):
        self.images = get_images_from_md(self.body_md)

    def db_write_new_entry(self):
        '''insert new page entry into database'''
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
                          body_html, body_md, tags, pub, 
                          note_cat_id, note_show_home)
                         VALUES
                         (?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ( ref, self.type, self.title, self.author,
                        self.date_norm, self.time_norm,
                        self.body_html, self.body_md,
                        self.tags, self.pub,
                        self.cat_id, self.show_home ) )
        g.db.commit()

        # write to changelog
        db_write_change(get_latest(), 'n')

    def db_update_entry(self):
        '''update page entry in database'''
        # if title is NOT_SET never change the ref!
        # else url_enc...
        if self.title == 'NOT_SET':
            ref = get_ref(self.id)
        else:
            ref = url_encode_str(self.title)

        g.db.execute( '''UPDATE entries
                         SET ref = ?, type = ?, title = ?,
                          body_html = ?, body_md = ?, tags = ?,
                          note_cat_id = ?, note_show_home = ?
                         WHERE id = ?''',
                      ( ref, self.type, self.title,
                        self.body_html, self.body_md,
                        self.tags,
                        self.cat_id, self.show_home,
                        self.id ) )
        g.db.commit()

        # write to changelog
        db_write_change(self.id, 'e')
