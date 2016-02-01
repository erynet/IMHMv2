# -*- coding:utf-8 -*-
__author__ = 'ery'

try:
    import ujson as json
except ImportError:
    import json

# from datetime import datetime
from flask import abort, Blueprint, request, jsonify, session

from imhm.tools import DB
from imhm.utils.async.functions import android_push, do_recognize_session
# from coock.tools import pre_request_logging, after_request_logging
# from coock.tools import check_req_data, admin_only, login_required
# from coock.models import Users, UsersExtend, UserBehaviorLog

management_bp = Blueprint(__name__, "management")
app = management_bp
# db = DB.get_session()
#
#
# @app.teardown_request
# def teardown_request_sqlalchemy_session_remove(exception):
#     try:
#         db.remove()
#     except Exception, e:
#         print("teardown_request_sqlalchemy_session_remove : %s" % str(e))
#
# if not GS.is_production():
#     app.before_request(pre_request_logging)
#     app.after_request(after_request_logging)

# ----- Header -----


@app.route("/_m/ping/", methods=["GET", "POST"])
def management_ping():
    return jsonify({}), 200


@app.route("/_m/gcm/", methods=["GET"])
def test_gcm():
    android_push.apply_async(args=["dummyuuid", u"123456"])
    do_recognize_session.apply_async(args=[1, 2])
    return jsonify({}), 200
