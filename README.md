This is basically the underlaying system I use to manage my little personal website.

The website is live at: <http://cem.revamp-it.ch>  
(Static version due to server limitations.)

It's basically a self written "micro-cms" based on python-flask (the micro-framework) and I named it __rubric-dyn__.

Please feel free to exlore this and use for reference. But please don't use this to simply create a copy of my website.

Note that currently this is not licensed and as such should be considered copyright protected.  
Though I may release it under GPL...

Thanks :)

## Setup notes

### Prerequisites

- python (v3)
- python-flask
- sqlite3
- pandoc (markdown conversion)
- python-pillow (for image-processing)

### DB

Create new db:

 $ sqlite3 website.db < schema.sql

### Config

Copy `config-example.py` to `config.py` and adapt settings.

### Build-in flask Development Server

run `server.py`

starts server on port 5000

interface login via: http://<host>:5000/interface/

### Apache Setup

acc. to flask doku.: <link>
