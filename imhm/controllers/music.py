# -*- coding:utf-8 -*-
__author__ = 'ery'

try:
    import ujson as json
except ImportError:
    import json

from datetime import datetime, timedelta
from flask import abort, Blueprint, request, jsonify, session, make_response

from sqlalchemy import func, or_, and_, text

from imhm.tools import DB
from imhm.tools import pre_request_logging, after_request_logging
from imhm.tools import check_req_data, parse_session, admin_only, login_required
from imhm.tools import StrCat
from imhm.config import f401
from imhm.models import *

# from imhm.utils.async.functions import mpush, check_bussiness_license

music_bp = Blueprint(__name__, "music")
app = music_bp
db = DB.get_session()


@app.teardown_request
def teardown_request_sqlalchemy_session_remove(exception):
    try:
        db.remove()
        # print("teardown_request_sqlalchemy_session_remove : success")
    except Exception, e:
        # print("teardown_request_sqlalchemy_session_remove : %s" % str(e))
        pass


app.before_request(pre_request_logging)
app.after_request(after_request_logging)


# ----- Header -----


@app.route("/music/info/<int:idx>/", methods=["GET"])
def music_info(idx):
    m = db.query(Music).filter_by(idx=idx).first()
    if not m:
        raise abort(404)

    return jsonify(
            {"title": m.title, "artist": m.artist, "album_name": m.album_name, "length": m.length, "genre": m.genre,
             "release_date": m.release_date, "image_size": m.album_image.__len__()}), 200


@app.route("/music/image/<int:idx>/", methods=["GET"])
def music_image_download(idx):
    m = db.query(Music).filter_by(idx=idx).first()
    if not m:
        raise abort(404)

    import base64
    img = base64.b64decode(m.album_image)
    res = make_response(img)
    fname = m.title + "-" + m.artist + ".jpg"
    res.headers["Content-Type"] = "image/jpeg"
    res.headers["Content-Length"] = img.__len__()
    # res.headers["Content-Disposition"] = "attachment; filename={0}".format(fname)
    return res, 200
