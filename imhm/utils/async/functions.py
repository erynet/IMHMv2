# -*- coding:utf-8 -*-
__author__ = 'ery'


from celery import Task, signals

from sqlalchemy import func, or_, and_, text

from imhm.tools import DB, GS, RLock, SPHRT
from imhm.models import *
from imhm.utils.async import capp
from imhm.config import push_message_code


class BaseTask(Task):
    abstract = True
    ignore_result = True
    default_retry_delay = 3


@capp.task(base=BaseTask, name="imhm.utils.async.functions.patrol")
def patrol():
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.android_push")
def android_push(uuids, message):
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
        return False
    return True


@capp.task(base=BaseTask, name="imhm.utils.async.functions.ios_push")
def ios_push(uuids, message):
    return True


@capp.task(base=BaseTask, name="imhm.utils.async.functions.mpush")
def mpush(ids, message=None, code=None):
    if not ids:
        return False
    if (message == None) and (code == None):
        return False

    chunk_size = GS.getd("VAR_CELERY_PUSH_CHUNK_SIZE")

    if not code:
        if code not in push_message_code:
            return False
        msg = push_message_code[code]
    else:
        msg = message

    # determine platform of device
    # assuming all devices are android
    for i in range((ids.__len__() / chunk_size) + 1):
        android_push.apply_async(args=[ids[i * chunk_size: (i + 1) * chunk_size], msg])

    return True


@capp.task(base=BaseTask, name="imhm.utils.async.functions.check_bussiness_license")
def check_bussiness_license(users_idx):
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.withdraw_users")
def withdraw_users():
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.address_added")
def address_added(addr_idx):
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.address_deleted")
def address_deleted(addr_idx):
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.address_rebuild")
def address_rebuild():
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.notify_new_order")
def notify_new_order(orders_idx):
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.sph_rt_rebuild_users")
def sph_rt_rebuild_users():
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.sph_rt_rebuild_address")
def sph_rt_rebuild_address():
    pass


@capp.task(base=BaseTask, name="imhm.utils.async.functions.sph_rt_rebuild_orders")
def sph_rt_rebuild_orders():
    pass
