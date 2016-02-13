from flask import Blueprint

media_static = Blueprint('media_static', __name__, static_folder='media')
