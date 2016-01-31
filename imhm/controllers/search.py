# -*- coding:utf-8 -*-
__author__ = 'ery'

try:
    import ujson as json
except ImportError:
    import json

from datetime import datetime, timedelta
from flask import abort, Blueprint, request, jsonify, session

from sqlalchemy import func, or_, and_, text

from imhm.tools import DB
from imhm.tools import pre_request_logging, after_request_logging
from imhm.tools import check_req_data, parse_session, admin_only, login_required
from imhm.config import f401
from imhm.models import *

# from imhm.utils.async.functions import mpush, check_bussiness_license

search_bp = Blueprint(__name__, "search")
app = search_bp
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


@app.route("/search/begin/", methods=["GET"])
def search_begin():
    try:
        with db.begin_nested():
            ss = SearchSession()
            db.add(ss)
    except Exception, e:
        print str(e)
        raise abort(500)
    db.commit()

    return jsonify({"idx": ss.idx}), 200


@app.route("/search/end/<int:idx>/", methods=["GET"])
def search_end(idx):
    ss = db.query(SearchSession).filter_by(idx=idx).first()
    if not ss:
        raise abort(404)

    try:
        with db.begin_nested():
            ss.end_at = datetime.now()
    except Exception, e:
        print str(e)
        raise abort(500)
    db.commit()

    import cPickle
    if isinstance(ss.result, str):
        return jsonify({"state": ss.state, "found_songs_idx": cPickle.loads(ss.result)}), 200
    else:
        return jsonify({"state": ss.state, "found_songs_idx": None}), 200


@app.route("/search/push/<int:idx>/", methods=["POST"])
def search_push(idx):
    is_ok, d, _ = check_req_data(request, essential_list=["b64stream"])
    if not is_ok:
        raise abort(400)

    ss = db.query(SearchSession).filter_by(idx=idx).first()
    if not ss:
        raise abort(404)

    try:
        with db.begin_nested():
            sp = SearchPacket(session_idx=idx, sequence=ss.current_sequence_index, data=d["b64stream"])
            ss.current_sequence_index += 1
            db.add(sp)
    except Exception, e:
        print str(e)
        raise abort(500)
    db.commit()

    import cPickle
    if isinstance(ss.result, str):
        return jsonify({"state": ss.state, "found_songs_idx": cPickle.loads(ss.result)}), 200
    else:
        return jsonify({"state": ss.state, "found_songs_idx": None}), 200


@app.route("/search/result/<int:idx>/", methods=["GET"])
def search_get_result(idx):
    return jsonify({"state": 2, "found_songs_idx": [1, 2, 3]}), 200
