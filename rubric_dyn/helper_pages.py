'''helper for pages (functions not returning a view)'''
import os
import json
from flask import g

def create_page_nav(curr_type, curr_datetime_norm):
    '''create previous/next navigation for posts (using same type)'''

    q_begin = '''SELECT date_norm, ref
                 FROM entries
                 WHERE date_norm IS NOT 'ERRONEOUS_DATE'
                 AND ( type = ? )
                 AND pub = 1
                 '''

    # get previous page
    # and create new page_nav list
    cur = g.db.execute( q_begin + \
                        '''AND datetime_norm < ?
                           ORDER BY datetime_norm DESC LIMIT 1''',
                           (curr_type, curr_datetime_norm) )
    prev_result = cur.fetchone()

    if curr_type == 'article':
        type_subpath = "/articles"

    if prev_result is not None:
        prev_date = prev_result[0]
        prev_ref = prev_result[1]
        page_nav = { 'prev_href': os.path.join(type_subpath, prev_date, prev_ref) }
    else:
        page_nav = { 'prev_href': None }

    # get next page
    # and fill in page_nav list
    cur = g.db.execute( q_begin + \
                        '''AND datetime_norm > ?
                           ORDER BY datetime_norm ASC LIMIT 1''',
                           (curr_type, curr_datetime_norm) )
    next_result = cur.fetchone()

    if next_result is not None:
        next_date = next_result[0]
        next_ref = next_result[1]
        page_nav['next_href'] = os.path.join(type_subpath, next_date, next_ref)
    else:
        page_nav['next_href'] = None

    return page_nav

# (--> will be DEPRECATED, since tags will be csv)
def extract_tags(meta_json):
    '''extract tags from json'''
    meta = json.loads(meta_json)
    if 'tags' in meta.keys():
        return meta['tags']
    else:
        return None
