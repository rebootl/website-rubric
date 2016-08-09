#!/usr/bin/python
'''import page from input file'''

import os
import sys
import json
import sqlite3
import hashlib

import config
from rubric_dyn.common import pandoc_pipe, copy_file, make_thumb, \
    url_encode_str, date_norm, get_md5sum

def connect_db():
    return sqlite3.connect(config.DATABASE)

class File:

    def __init__(self, filepath):
        #self.filename = filename
        #self.dir = dir

        #self.filepath_abs = os.path.join(self.dir, self.filename)

        self.filepath = filepath

        self.dir_abs = os.path.dirname(self.filepath)

        self.meta_json, \
        self.body_md = read_content_file(self.filepath)

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

        self.date_norm, \
        self.time_norm, \
        self.datetime_norm = date_norm(self.date_str)

        self.ref = url_encode_str(self.title)

        self.meta_json = self.file.meta_json
        self.body_md = self.file.body_md

        # set some more defaults
        self.body_md5sum = ""
        self.body_html = "THIS IS HTML"
        self.data1 = ""

        if 'id' in self.meta.keys():
            self.id = self.meta['id']
        else:
            self.id = None

    def process(self):
        self.process_body_md()
        #self.insert_into_db('body_md5sum', self.body_md5sum)
        self.write_to_db()
        self.copy_files()

    def process_body_md(self):
        self.body_md5sum = get_md5sum(self.body_md)
        self.body_html = pandoc_pipe( self.body_md, config.PANDOC_OPTS )

    def write_to_db(self):
        # if the page has a meta.id the entry with this id is updated
        # if not, a new entry is written
        if self.id:
            print("Entry has id, updating...")
            # check if entry is present
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('''SELECT ref
                           FROM entries
                           WHERE id = ?''', (self.id,))
            result = cur.fetchone()
            conn.close()

            if result is None:
                print("Warning: No entry with ID {} found. Leaving.".format(self.id))
                sys.exit(1)

            self.db_update_entry()
        else:
            print("Entry has no id, adding new...")

            # check if an entry w/ the same title is already there
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('''SELECT id
                           FROM entries
                           WHERE ref = ?''', (self.ref,))
            result = cur.fetchone()
            conn.close()

            if result is None:
                self.db_new_entry()
            else:
                print("Warning: An entry with the same title is already in the database, ID {}. Skipping.".format(result[0]))
                sys.exit(1)

    def db_new_entry(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute( '''INSERT INTO entries
                         ( ref, type, title, author,
                           date_str, datetime_norm, date_norm, time_norm,
                           body_html, body_md5sum, meta_json, body_md,
                           data1, pub )
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                     ( self.ref, self.type, self.title, self.author,
                       self.date_str, self.datetime_norm, self.date_norm,
                        self.time_norm,
                       self.body_html, self.body_md5sum, self.meta_json,
                        self.body_md,
                       self.data1, 0 ) )
        conn.commit()
        conn.close()

    def db_update_entry(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute( '''UPDATE entries
                        SET ref = ?, type = ?, title = ?, author = ?,
                         date_str = ?, datetime_norm = ?, date_norm = ?,
                         time_norm = ?, body_html = ?, body_md5sum = ?,
                         meta_json = ?, body_md = ?, data1 = ?
                        WHERE id = ?''',
                     ( self.ref, self.type, self.title, self.author,
                       self.date_str, self.datetime_norm, self.date_norm,
                       self.time_norm, self.body_html, self.body_md5sum,
                       self.meta_json, self.body_md, self.data1,
                       self.id ) )
        conn.commit()
        conn.close()

    def copy_files(self):
        for file in self.meta['files']:
            in_path_abs = os.path.join(self.file.dir_abs, file)
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
        #self.insert_into_db('data1', self.data1)
        self.write_to_db()
        self.copy_files()
        self.copy_image()
        make_thumb(self.img_filepath_abs, config.MEDIA_DIR)

    def copy_image(self):
        copy_file(self.img_filepath_abs, config.MEDIA_DIR)


#def import_dir(dir):
#    # get content
#    dir_content = os.listdir(dir)
#
#    # filter pages,
#    # create file instances, which in turn create page instances
#    pages = []
#    for filename in dir_content:
#        if filename.endswith(config.PAGE_EXT):
#            file = File(filename, dir)
#            pages.append(file.page_inst)
#
#    # process
#    for page in pages:
#        page.process()


def import_file(filepath):
    # check file extension and presence
    if not filepath.endswith(config.PAGE_EXT):
        print("Error: Extension must be {} Leaving.".format(config.PAGE_EXT))
        sys.exit(1)
    elif not os.path.isfile(filepath):
        print("Error: File not found... Leaving.")
        sys.exit(1)

    # create instance (should create page instance as well..?)
    file_inst = File(filepath)
    file_inst.page_inst.process()


if __name__ == '__main__':
    # check command line argument
    if len(sys.argv) < 2:
        print("Usage: {} <file path>".format(sys.argv[0]))
        sys.exit(1)
    else:
        filepath = sys.argv[1]

    import_file(filepath)

    #print("YEY", filename)
