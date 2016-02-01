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


# @app.route("/search/push/<int:idx>/", methods=["POST"])
# def search_push(idx):
#     is_ok, d, _ = check_req_data(request, essential_list=["b64stream"])
#     if not is_ok:
#         raise abort(400)
#
#     ss = db.query(SearchSession).filter_by(idx=idx).first()
#     if not ss:
#         raise abort(404)
#
#     try:
#         with db.begin_nested():
#             sp = SearchPacket(session_idx=idx, sequence=ss.current_sequence_index, data=d["b64stream"])
#             ss.current_sequence_index += 1
#             db.add(sp)
#     except Exception, e:
#         print str(e)
#         raise abort(500)
#     db.commit()
#
#     import cPickle
#     if isinstance(ss.result, str):
#         return jsonify({"state": ss.state, "current_session_idx": ss.idx, "found_songs_idx": cPickle.loads(ss.result)}), 200
#     else:
#         return jsonify({"state": ss.state, "current_session_idx": ss.idx, "found_songs_idx": None}), 200


@app.route("/search/push_raw/", methods=["POST"])
def search_push_raw():
    is_ok, d, _ = check_req_data(request, essential_list=["username", "sequence", "b64stream"])
    if not is_ok:
        raise abort(400)

    user = db.query(User).filter_by(username=d["username"]).first()
    if not user:
        raise abort(404)

    if d["sequence"] == 0:
        try:
            with db.begin_nested():
                ss = SearchSession(user_idx=user.idx)
                db.add(ss)
        except Exception, e:
            print str(e)
            raise abort(500)
    else:
        ss = db.query(SearchSession).\
            filter_by(user_idx=user.idx, state=0).order_by(SearchSession.begin_at.desc()).first()

    try:
        with db.begin_nested():
            sp = SearchPacket(session_idx=ss.idx, sequence=d["sequence"],
                              data=d["b64stream"], length=d["b64stream"].__len__())
            db.add(sp)
    except Exception, e:
        print str(e)
        raise abort(500)
    db.commit()

    if sp.sequence % 3 == 2:
        from subprocess import Popen
        p = Popen(["/imhm/penv/bin/python", "/imhm/imhm/imhm/tools/recognizer.py", str(ss.idx), "0"])

    return jsonify({"current_session_idx": ss.idx}), 200


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

    from subprocess import Popen
    p = Popen(["/imhm/penv/bin/python", "/imhm/imhm/imhm/tools/recognizer.py", str(ss.idx), "1"])
    p.wait()

    return jsonify({"current_session_idx": ss.idx}), 200


@app.route("/search/download/<int:idx>/", methods=["GET"])
def search_download(idx):
    ss = db.query(SearchSession).filter_by(idx=idx).first()
    if not ss:
        raise abort(404)

    sps = db.query(SearchPacket).filter_by(session_idx=ss.idx).order_by(SearchPacket.sequence.asc()).all()
    if not sps:
        raise abort(401)

    import base64
    with StrCat() as s:
        print s
        for sp in sps:
            s.append(base64.b64decode(sp.data))
        res = make_response(str(s))
    res.headers["Content-Disposition"] = "attachment; filename=SearchSession-{0}.pcm".format(ss.idx)
    return res, 200

