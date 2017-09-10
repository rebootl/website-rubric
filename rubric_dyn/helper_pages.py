'''helper for pages (functions not returning a view)'''
import os
import json
import sqlite3

from flask import g
from flask import current_app

from rubric_dyn.common import gen_href

def gen_changelog(change_rows):
    '''generate changelog output ordered by dates'''
    # prepare list of changes ordered by dates
    #
    # structure:
    #
    # dates = [ { 'date': "2016-08-01",
    #             'changes': [ { change1_data } ] },
    #           { 'date': "2016-07-30",
    #             'changes': [ { change2_data } ] } ]
    #

    # create list from changelog data
    # and insert additional informations per item
    changes = []
    for change_row in change_rows:
        change = {}
        for i, v in enumerate(change_row):
            change.update( { change_row.keys()[i]: v } )

        cur = g.db.execute('''SELECT ref, type, title, date_norm,
                               pub
                              FROM entries
                              WHERE id = ?''', (change_row['entry_id'],))
        entry = cur.fetchone()
        if entry['pub'] != 1:
            continue

        change['entry'] = entry
        # update entry for specific types
        # e.g. adding body_html for latest
        if entry['type'] == 'latest':
            cur = g.db.execute('''SELECT ref, type, title, date_norm,
                                   body_html, pub
                                  FROM entries
                                  WHERE id = ?''', (change_row['entry_id'],))
            entry = cur.fetchone()
            change['entry'] = entry
        # set href
        change['entry_href'] = gen_href(entry)
        # set timezone name
        # --> not using atm. just write "localtime" or so
        #change['tzname'] = get_tzname( change_row['date_norm'],
        #                               change_row['time_norm'] )

        changes.append(change)

    # first create the date sets
    date_sets = []
    last_date = ""
    for change in changes:
        curr_date = change['date_norm']
        if curr_date != last_date:
            date_set = { 'date': curr_date,
                         'changes': [] }
            date_sets.append(date_set)
            last_date = curr_date

    # add the changes to the sets
    for date_set in date_sets:
        for change in changes:
            if change['date_norm'] == date_set['date']:
                date_set['changes'].append(change)

    # debug output
    #date_repr = ""
    #for date_set in date_sets:
    #    date_repr += date_set['date'] + "\n"
    #    for change in date_set['changes']:
    #        date_repr += " " + change['entry']['title'] + "\n"
    #return '<pre>' + date_repr + '</pre>'

    return date_sets

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


    if curr_type in current_app.config['PAGE_TYPES_PREFIXES'].keys():
        prefix = os.path.join(
            '/',
            current_app.config['PAGE_TYPES_PREFIXES'][curr_type]
        )
    else:
        prefix = '/'

    page_nav = gen_page_nav(curr_id, rows, prefix, True)

    page_nav['index'] = prefix

    return page_nav

# (--> DEPRECATED, since tags are csv)
#def extract_tags(meta_json):
#    '''extract tags from json'''
#    meta = json.loads(meta_json)
#    if 'tags' in meta.keys():
#        return meta['tags']
#    else:
#        return None
