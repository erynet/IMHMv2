# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys
sys.setdefaultencoding = "utf-8"

from sqlalchemy import Column, Index, ForeignKey, Integer, Boolean, String, DateTime, TIMESTAMP
from sqlalchemy.sql import functions

from flask.ext.login import UserMixin

from imhm.tools import Base, SerializerMixin
from imhm.models import Template


class User(Base, SerializerMixin, Template, UserMixin):
    __tablename__ = "user"

    username = Column(String(64), unique=True, nullable=False)
    password = Column(String(64), nullable=False)
    uuid = Column(String(128), nullable=True)

