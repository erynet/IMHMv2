# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys
sys.setdefaultencoding = "utf-8"

from sqlalchemy.dialects.mysql import BLOB

from sqlalchemy import Column, Index, ForeignKey, Integer, Boolean, String, DateTime, TIMESTAMP
from sqlalchemy.sql import functions

from flask.ext.login import UserMixin

from imhm.tools import Base, SerializerMixin
from imhm.models import Template


class SearchPacket(Base, SerializerMixin, Template, UserMixin):
    __tablename__ = "search_packet"

    session_idx = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)
    data = Column(BLOB(16777216), nullable=False)
    length = Column(Integer, default=0, nullable=False)

    idx_session_idx_sequence = Index("idx_session_idx_sequence", session_idx, sequence)


