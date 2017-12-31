'''Page object'''

from rubric_dyn.common import date_norm2, time_norm, url_encode_str
from rubric_dyn.helper_interface import process_input, get_images_from_md
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
        self.title = title
        self.author = author

        # --> norm ?
        self.date_norm = date_str
        self.time_norm = time_str

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

    def newref(self, id):
        '''create unique ref'''
        if self.title == "":
            self.newref = "entry-ref_" + str(id)
        else:
            self.newref = url_encode_str(self.title) + "_" + str(id)

    def db_write_new_entry(self):
        '''insert new page entry into database'''

        cur = g.db.cursor()
        cur.execute( '''INSERT INTO entries
                         (ref, type, title, author,
                          date_norm, time_norm,
                          body_html, body_md, tags, pub, 
                          note_cat_id, note_show_home)
                         VALUES
                         (?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ( 'tmpval', self.type, self.title,
                        self.author,
                        self.date_norm, self.time_norm,
                        self.body_html, self.body_md,
                        self.tags, self.pub,
                        self.cat_id, self.show_home ) )
        g.db.commit()

        # get the autoinc. val
        id = cur.lastrowid
        cur.close()
        self.newref(id)

        # write ref
        g.db.execute('''UPDATE entries
                        SET ref = ?
                        WHERE id = ?
                         AND author = ?''',
                     (self.newref, id, self.author))
        g.db.commit()

        # write to changelog
        db_write_change(id, 'n')

    def db_update_entry(self):
        '''update page entry in database'''

        # update ref
        self.newref(self.id)

        g.db.execute( '''UPDATE entries
                         SET ref = ?, type = ?, title = ?,
                          body_html = ?, body_md = ?, tags = ?,
                          note_cat_id = ?, note_show_home = ?
                         WHERE id = ?''',
                      ( self.newref, self.type, self.title,
                        self.body_html, self.body_md,
                        self.tags,
                        self.cat_id, self.show_home,
                        self.id ) )
        g.db.commit()

        # write to changelog
        db_write_change(self.id, 'e')
