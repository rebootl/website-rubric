#!/usr/bin/python
'''Pandoc filter to insert path prefix for images.'''

from pandocfilters import toJSONFilter, Para, Image

import os

#PATH_HASH = "PATH_178164f81917b8e87073295a635588de"
PREFIX = "/media"

def repl_path(key, value, format, meta):
    if key == 'Image':
        alt, [ src, tit ] = value

        # only change source if it's a filename only
        dirname = os.path.dirname(src)
        if dirname == '':
            src = os.path.join(PREFIX, src)

        return Image( alt, [ src, tit ] )

if __name__ == "__main__":
    toJSONFilter(repl_path)
