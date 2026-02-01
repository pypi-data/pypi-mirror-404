#!/usr/bin/env python
# -*- coding: utf-8 -*-
#===============================================================================
#
# Copyright (c) 2025 Chatopera Inc. <www.chatopera.com> All Rights Reserved
#
#
# File: /c/Users/Administrator/chatopera/embeddings-zh/embeddings_zh/__init__.py
# Author: Hai Liang Wang
# Date: 2025-05-30:10:07:37
#
#===============================================================================

"""
Embeddings Interfaces

https://python.langchain.com/api_reference/core/embeddings/langchain_core.embeddings.embeddings.Embeddings.html#langchain_core.embeddings.embeddings.Embeddings
"""
__copyright__ = "Copyright (c) Chatopera Inc. 2025. All Rights Reserved"
__author__ = "Hai Liang Wang"
__date__ = "2025-05-30:10:07:37"

import sys

if sys.version_info[0] < 3:
    raise RuntimeError("Must be using Python 3")
else:
    unicode = str

from .zh_CN import EmbeddingsZh
from .zh_TW import EmbeddingsZhTw