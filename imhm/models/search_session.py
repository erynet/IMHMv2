# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys
sys.setdefaultencoding = "utf-8"

from sqlalchemy import Column, Index, ForeignKey, Integer, Boolean, String, DateTime, TIMESTAMP, BLOB
from sqlalchemy.sql import functions

from flask.ext.login import UserMixin

from imhm.tools import Base, SerializerMixin
from imhm.models import Template


class SearchSession(Base, SerializerMixin, Template, UserMixin):
    __tablename__ = "search_session"

    user_idx = Column(Integer, ForeignKey("user.idx", onupdate="CASCADE", ondelete="CASCADE"), nullable=True)
    state = Column(Integer, default=0, nullable=False)
    current_sequence_index = Column(Integer, default=0, nullable=False)
    result = Column(BLOB, nullable=True)
    begin_at = Column(TIMESTAMP, server_default=functions.current_timestamp(), nullable=False)
    end_at = Column(TIMESTAMP, nullable=True)


