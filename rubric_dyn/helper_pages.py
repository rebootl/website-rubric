'''helper for pages (functions not returning a view)'''
import os
import json
import sqlite3

from flask import g

def gen_page_nav(curr_id, rows, prefix, date_path=False):
    '''get previous and next entry from list of db entries
and generate page_nav'''
    cnt = 0
    for row in rows:
        if row['id'] == curr_id:
            break
        cnt += 1

    prev_row_num = cnt-1
    if prev_row_num < 0:
        page_nav = { 'prev_href': None }
    elif date_path:
        page_nav = { 'prev_href': os.path.join( prefix,
            rows[prev_row_num]['date_norm'],
            rows[prev_row_num]['ref'] ) }
    else:
        page_nav = { 'prev_href': os.path.join( prefix,
            rows[prev_row_num]['ref'] ) }

    next_row_num = cnt+1
    if next_row_num > len(rows)-1:
        page_nav['next_href'] = None
    elif date_path:
        page_nav['next_href'] = os.path.join( prefix,
            rows[next_row_num]['date_norm'],
            rows[next_row_num]['ref'] )
    else:
        page_nav['next_href'] = os.path.join( prefix,
            rows[next_row_num]['ref'] )

    return page_nav

def create_page_nav(curr_id, curr_type, index="/"):
    '''create previous/next navigation for posts (using same type)'''

    # get all items as list
    # get the current index
    # get the next and preview out of list
    # --> evtl. this could all be done by a sqlite query,
    #     but how ? the query would become very complicated...

    # another variant would be (better for larger dataset)
    # select all with the same datetime
    # if there are order by another criteria
    # and get the next/previous
    # else get the next/previous by datetime

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref, date_norm
                           FROM entries
                           WHERE date_norm IS NOT 'NOT_SET'
                           AND ( type = ? )
                           AND pub = 1
                           ORDER BY date_norm ASC, time_norm ASC''',
                           (curr_type,) )
    rows = cur.fetchall()


    if curr_type == 'article':
        prefix = "/articles"
        index = "/#articles"
    else:
        prefix = '/'

    page_nav = gen_page_nav(curr_id, rows, prefix, True)

    page_nav['index'] = index

    return page_nav

def create_page_nav_image(curr_id, curr_gallery_id, curr_gallery_ref):
    '''create previous/next navigation for images'''

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref
                           FROM images
                           WHERE gallery_id = ?
                           ORDER BY datetime_norm ASC''',
                           (curr_gallery_id,) )
    rows = cur.fetchall()

    page_nav = gen_page_nav(curr_id, rows, '/')

    page_nav['index'] = os.path.join("/galleries", curr_gallery_ref)

    return page_nav

def create_page_nav_gallery(curr_id):
    '''create previous/next navigation for galleries'''

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref
                           FROM galleries
                           ORDER BY date_norm ASC''' )
    rows = cur.fetchall()

    page_nav = gen_page_nav(curr_id, rows, '/galleries')

    page_nav['index'] = '/#galleries'

    return page_nav

# (--> will be DEPRECATED, since tags will be csv)
def extract_tags(meta_json):
    '''extract tags from json'''
    meta = json.loads(meta_json)
    if 'tags' in meta.keys():
        return meta['tags']
    else:
        return None
