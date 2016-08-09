#!/usr/bin/python
'''import pages from files'''

import os
import json
import sqlite3
import hashlib
from datetime import datetime

import config
from rubric_dyn.common import pandoc_pipe, copy_file, make_thumb, url_encode_str

def connect_db():
    return sqlite3.connect(config.DATABASE)

class File:

    def __init__(self, filename, dir):
        self.filename = filename
        self.dir = dir

        self.filepath_abs = os.path.join(self.dir, self.filename)
        print("CONTENT FILE", self.filepath_abs)

        self.meta_json, \
        self.body_md = read_content_file(self.filepath_abs)

        self.meta = json.loads(self.meta_json)

        self.set_meta_defaults()
        self.create_page_instance()

    def set_meta_defaults(self):
        for key, value in config.META_DEFAULTS.items():
            if key not in self.meta.keys():
                self.meta[key] = value

        if type == "imagepage":
            if self.meta['image'] == "" or self.meta['image'] == None:
                print("Warning: imagepage has no image set:", self.filepath_abs)
                self.meta['image'] = "NO IMAGE SET"

    def create_page_instance(self):
        type = self.meta['type']
        if type == 'imagepage':
            self.page_inst = ImagePage(self)
        else:
            self.page_inst = Page(self)


def read_content_file(filepath_abs):
    with open(filepath_abs, 'r') as f:
        content = f.read()
    meta_json, body_md = content.split('%%%', 1)
    return meta_json, body_md


class Page:

    def __init__(self, file):
        self.file = file

        self.meta = self.file.meta
        self.type = self.meta['type']
        self.title = self.meta['title']
        self.author = self.meta['author']
        self.date_str = self.meta['date']

        self.date_norm()
        self.ref = url_encode_str(self.title)

        self.meta_json = self.file.meta_json
        self.body_md = self.file.body_md

        # set some more defaults
        self.body_md5sum = ""
        self.body_html = "THIS IS HTML"
        self.data1 = ""

    def date_norm(self):
        try:
            date_obj = datetime.strptime( self.date_str,
                                          config.DATETIME_FORMAT )
            self.date_norm = date_obj.strftime("%Y-%m-%d")
            self.time_norm = date_obj.strftime("%H:%M")
            self.datetime_norm = date_obj.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            try:
                date_obj = datetime.strptime( self.date_str,
                                              config.DATE_FORMAT )
                self.date_norm = date_obj.strftime("%Y-%m-%d")
                self.time_norm = "NOT SET"
                self.datetime_norm = date_obj.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                print("Warning: ERRONEOUS DATE...")
                self.date_norm = "ERRONEOUS_DATE"
                self.time_norm = "NOT SET"
                self.datetime_norm = "ERRONEOUS_DATE"

    def process(self):
        self.process_body_md()
        self.insert_into_db('body_md5sum', self.body_md5sum)
        self.copy_files()

    def process_body_md(self):
        self.body_md5sum = hashlib.md5(self.body_md.encode()).hexdigest()
        self.body_html = pandoc_pipe( self.body_md,
                                      [ '--to=html5',
                                        '--filter=rubric_dyn/filter_img_path.py' ] )

    def insert_into_db(self, compare_field, compare_with):
        '''only new or changed entries are written,
the title is used to determine if an entry is already there

compare_field is read out and compared with compare_with,
if it has changed the entry is updated (rewritten)
'''

        # --> compare several fields

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT id, " + compare_field + " FROM entries WHERE ref = ?", (self.ref,))
        result = cur.fetchone()

        if result is None:
            self.db_new_entry(cur)
            conn.commit()
        elif result[1] != compare_with:
            self.db_update_entry(cur, result)
            conn.commit()
        else:
            #print("RESULT 1", result[1])
            #print("COMP WITH", compare_with)
            print("Entry already in database:", self.title)

        conn.close()

    def db_new_entry(self, cur):
        print("Adding new database entry:", self.title)
        cur.execute( "INSERT INTO entries (ref, type, title, author, date_str, datetime_norm, date_norm, time_norm, body_html, body_md5sum, meta_json, body_md, data1, pub) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ( self.ref,
                      self.type,
                      self.title,
                      self.author,
                      self.date_str,
                      self.datetime_norm,
                      self.date_norm,
                      self.time_norm,
                      self.body_html,
                      self.body_md5sum,
                      self.meta_json,
                      self.body_md,
                      self.data1,
                      0 ) )

    def db_update_entry(self, cur, result):
        print("Entry has changed, updating database:", self.title)
        cur.execute( "UPDATE entries SET ref = ?, type = ?, title = ?, author = ?, date_str = ?, datetime_norm = ?, date_norm = ?, time_norm = ?, body_html = ?, body_md5sum = ?, meta_json = ?, body_md = ?, data1 = ? WHERE id = ?",
                     ( self.ref,
                       self.type,
                       self.title,
                       self.author,
                       self.date_str,
                       self.datetime_norm,
                       self.date_norm,
                       self.time_norm,
                       self.body_html,
                       self.body_md5sum,
                       self.meta_json,
                       self.body_md,
                       self.data1,
                       result[0] ) )

    def copy_files(self):
        for file in self.meta['files']:
            in_path_abs = os.path.join(self.file.dir, file)
            if not os.path.isfile(in_path_abs):
                print("Warning: File not found:", file)
                continue
            out_filepath = os.path.join(config.MEDIA_DIR, file)
            if os.path.isfile(out_filepath):
                #print("File already present, skipping:", file)
                continue
            copy_file(in_path_abs, config.MEDIA_DIR)

class ImagePage(Page):

    def __init__(self, file):
        super().__init__(file)

        self.img_filename = self.meta['image']
        self.img_filepath_abs = os.path.join(self.file.dir, self.img_filename)

        self.data1 = self.img_filename

    def process(self):
        self.insert_into_db('data1', self.data1)
        self.copy_files()
        self.copy_image()
        make_thumb(self.img_filepath_abs, config.MEDIA_DIR)

    def copy_image(self):
        copy_file(self.img_filepath_abs, config.MEDIA_DIR)


def import_dir(dir):
    # get content
    dir_content = os.listdir(dir)

    # filter pages,
    # create file instances, which in turn create page instances
    pages = []
    for filename in dir_content:
        if filename.endswith(config.PAGE_EXT):
            file = File(filename, dir)
            pages.append(file.page_inst)

    # process
    for page in pages:
        page.process()


if __name__ == '__main__':
    for dir in config.CONTENT_DIRS:
        import_dir(dir)
