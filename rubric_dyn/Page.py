'''page objects for interface operations
(including database methods update and new)'''

from flask import current_app, g
from rubric_dyn.helper_interface import process_edit
from rubric_dyn.common import get_md5sum, date_norm, url_encode_str

class Page:

    def __init__(self, text_input):
        self.text_input = text_input

        self.meta, \
        self.meta_json, \
        self.img_exifs_json, \
        self.body_html, \
        self.body_md = process_edit(self.text_input, True)

        self.title = self.meta['title']
        self.author = self.meta['author']

        self.body_md5sum = get_md5sum(self.body_md)

        self.date_str = self.meta['date']
        self.date_norm, \
        self.time_norm, \
        self.datetime_norm = date_norm( self.date_str,
                                        current_app.config['DATETIME_FORMAT'],
                                        current_app.config['DATE_FORMAT'] )

        self.ref = url_encode_str(self.title)

        self.type = self.meta['type']
        if self.type == 'imagepage':
            self.data1 = self.meta['image']
        else:
            self.data1 = ""

class EditPage(Page):

    def __init__(self, id, text_input):
        self.id = id
        super().__init__(text_input)

    def save_edit(self):
        self.db_update_entry()

    def db_update_entry(self):
        g.db.execute( '''UPDATE entries
                         SET ref = ?, type = ?, title = ?, author = ?,
                          date_str = ?, datetime_norm = ?, date_norm = ?,
                          time_norm = ?, body_html = ?, body_md5sum = ?,
                          meta_json = ?, body_md = ?, data1 = ?,
                          exifs_json = ?
                         WHERE id = ?''',
                      ( self.ref, self.type, self.title, self.author, \
                        self.date_str, self.datetime_norm, self.date_norm, \
                        self.time_norm, self.body_html, self.body_md5sum, \
                        self.meta_json, self.body_md, self.data1, \
                        self.img_exifs_json, self.id ) )
        g.db.commit()

class NewPage(Page):

    def __init__(self, text_input):
        super().__init__(text_input)

        self.published = 0

    def save_new(self):
        self.db_new_entry()

    def db_new_entry(self):
        g.db.execute( '''INSERT INTO entries
                         (ref, type, title, author,
                          date_str, datetime_norm, date_norm,
                          time_norm, body_html, body_md5sum,
                          meta_json, body_md, data1, pub, exifs_json)
                        VALUES
                          (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ( self.ref, self.type, self.title, self.author,
                        self.date_str, self.datetime_norm, self.date_norm,
                        self.time_norm, self.body_html, self.body_md5sum,
                        self.meta_json, self.body_md, self.data1, self.published,
                        self.img_exifs_json ) )
        g.db.commit()
