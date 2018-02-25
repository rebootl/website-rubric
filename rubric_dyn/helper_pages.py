'''helper for pages (functions not returning a view)'''
import os
import json
import sqlite3

from flask import g
from flask import current_app

from rubric_dyn.common import gen_href
from rubric_dyn.db_read import get_next_entryref, get_prev_entryref, \
    db_load_category

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

def gen_timeline_date_sets(pages_rows):
    '''generate timeline entries'''
    # create list (--> use list sqlite.Row instead ???)
    pages = []
    for page_row in pages_rows:
        page = dict(page_row)

        # limit page length
        #  more than three paragraphs
        if page['body_html'].count('</p>') > 3:
            body_html_cut = "</p>".join(page['body_html'].split("</p>", 3)[:3])
            page['body_html'] = body_html_cut
            page['cut'] = True
        # more than one image
        if page['body_html'].count('</figure>') > 1:
            body_html_cut = page['body_html'].split('</figure>')[0] + '</figure>'
            # (debug-print)
            #print(body_html_cut)
            page['body_html'] = body_html_cut
            page['cut'] = True
        #if ...

        pages.append(page)

    date_sets = []
    last_date = ""
    for page in pages_rows:
        curr_date = page['date_norm']
        if curr_date != last_date:
            date_set = { 'date': curr_date,
                         'pages': [] }
            date_sets.append(date_set)
            last_date = curr_date

    # add the changes to the sets
    for date_set in date_sets:
        for page in pages:
            if page['date_norm'] == date_set['date']:
                date_set['pages'].append(page)

    return date_sets

def create_page_nav(cat_id, date_norm, time_norm):

    row_next = get_next_entryref(cat_id, date_norm, time_norm)
    row_prev = get_prev_entryref(cat_id, date_norm, time_norm)

    cat_row = db_load_category(cat_id)

    if row_next == None:
        page_nav = { 'next': None }
    else:
        page_nav = { 'next': { 'cat_ref': cat_row['ref'],
                               'date_norm': row_next['date_norm'],
                               'ref': row_next['ref'] } }

    if row_prev == None:
        page_nav['prev'] = None
    else:
        page_nav['prev'] = { 'cat_ref': cat_row['ref'],
                             'date_norm': row_prev['date_norm'],
                             'ref': row_prev['ref'] }

    page_nav['index_ref'] = cat_row['ref']

    return page_nav
