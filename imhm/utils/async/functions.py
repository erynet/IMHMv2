# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
import os

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, "../../../"))

from celery import Task, signals

from sqlalchemy import func, or_, and_, text

from imhm.tools import DB
from imhm.models import *
from imhm.utils.async import capp
from imhm.config import push_message_code


class BaseTask(Task):
    abstract = True
    ignore_result = True
    default_retry_delay = 3


@capp.task(base=BaseTask, name="imhm.utils.async.functions.android_push")
def android_push(uuids, message):
    print str(uuids)
    if not uuids:
        return False

    from gcm import GCM

    g = GCM("AIzaSyAheYj04o3dgHhG8MrN5NGQKY4HT8NhzKc")

    try:
        if isinstance(uuids, list):
            g.json_request(registration_ids=uuids, data=message)
        elif isinstance(uuids, str):
            g.plaintext_request(registration_id=uuids, data=message)
    except Exception, e:
        print str(e)
        return False
    return True


@capp.task(base=BaseTask, name="imhm.utils.async.functions.do_recognize_session")
def do_recognize_session(session_idx):
    print str("QWeR")
    pass

