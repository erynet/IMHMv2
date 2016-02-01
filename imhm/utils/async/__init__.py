# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
import os

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, "../../../"))


from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from flask import current_app

# from imhm.tools import GS
from imhm.config import celery_configs

capp = Celery(current_app, include=["functions"])
capp.config_from_object(celery_configs["development"])