# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys
sys.setdefaultencoding = "utf-8"

from sqlalchemy import Column, Index, ForeignKey, Integer, Float, Boolean, String, DateTime, TIMESTAMP
from sqlalchemy.sql import functions

from imhm.tools import Base, SerializerMixin
from imhm.models import Template


class SearchHistory(Base, SerializerMixin, Template):
    __tablename__ = "search_history"

    title = Column(String, ForeignKey("user.idx", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    music_idx = Column(Integer, ForeignKey("music.idx", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    search_date = Column(TIMESTAMP, server_default=functions.current_timestamp(), nullable=False)