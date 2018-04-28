'''Page object'''

from flask import flash, g, current_app

from rubric_dyn.common import date_norm2, time_norm, url_encode_str
from rubric_dyn.helper_interface import process_input, get_images_from_md
from rubric_dyn.db_write import db_write_change


class Page:

    def __init__(self, id, type, title, author,
                 date_str, time_str, tags, body_md,
                 note_cat_id, note_show_home, pub=1):
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
        self.note_cat_id = int(note_cat_id)
        self.note_show_home = int(note_show_home)
        self.pub = int(pub)

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
                        self.note_cat_id, self.note_show_home ) )
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
                        self.note_cat_id, self.note_show_home,
                        self.id ) )
        g.db.commit()

        # write to changelog
        db_write_change(self.id, 'e')


class NewPage(Page):

    def __init__(self):
        '''initialize an empty page obj. w/ default values'''

        self.id = "new"
        self.type = current_app.config['DEFAULT_PAGE_TYPE']
        self.title = ""
        self.author = current_app.config['AUTHOR_NAME']

        # --> norm ?
        # (date is set when saving)
        # --> set it here
        self.date_norm = ""
        self.time_norm = ""

        self.tags = ""
        self.body_md = ""
        self.note_cat_id = current_app.config['DEFAULT_CAT_ID']
        self.note_show_home = 0
        self.pub = 1    # (re-set in init above)

        # process input
        self.body_html = ""

        self.images = []
