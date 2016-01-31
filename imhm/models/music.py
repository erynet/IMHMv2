# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys
sys.setdefaultencoding = "utf-8"

from sqlalchemy import Column, Index, ForeignKey, Integer, Float, Boolean, String, DateTime, TIMESTAMP, BLOB
from sqlalchemy.sql import functions

from imhm.tools import Base, SerializerMixin
from imhm.models import Template


class Music(Base, SerializerMixin, Template):
    __tablename__ = "music"

    title = Column(String(64), nullable=False)
    artist = Column(String(32), nullable=True)
    album_name = Column(String(128), nullable=True)
    length = Column(Integer, nullable=False)
    genre = Column(String(32))
    album_image = Column(BLOB, nullable=True)
    release_date = Column(DateTime, nullable=True)