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

import os
import sys

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(curdir)

if sys.version_info[0] < 3:
    raise RuntimeError("Must be using Python 3")
else:
    unicode = str

from typing import Any, List
from functools import lru_cache
import synonyms

_flat_sum_array = lambda x: synonyms.np.sum(x, axis=0)  # 分子


'''
ZH CN
'''
@lru_cache(maxsize=12800)
def lookup_word_vector(word):
    '''
    Look up a word's vecor
    With cache, https://gist.github.com/promto-c/04b91026dd66adea9e14346ee79bb3b8
    '''
    try:
        return synonyms.v(word)
    except KeyError as error:
        return None


def get_text_vector(text):
    '''
    Get Text vector
    '''
    words, tags = synonyms.seg(text) # 词性，https://gist.github.com/luw2007/6016931

    terms = set()
    vectors = []
    for (w, t) in zip(words, tags):
        # 停用词
        if w in synonyms.STOPWORDS:
            continue

        # 过滤数词，量词
        if t.startswith("m") or \
            t.startswith("q"):
            continue

        # 去重
        if w in terms:
            continue

        terms.add(w)
        vector = lookup_word_vector(w)
        if vector is not None:
            vectors.append(vector)

    if len(vectors) == 0:
        raise RuntimeError("Invalid vector length, none vector found.")

    v = _flat_sum_array(vectors)
    return v

class EmbeddingsZh():

    def __init__(self, **kwargs: Any):
        pass

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeddings with Chatopera [Synonyms](https://github.com/chatopera/Synonyms) for chatbot, RAG.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        ret = []

        texts = list(map(lambda x: x.replace("\n", " "), texts))

        for text in texts:
            try:
                v = get_text_vector(text)
                ret.append(v)
            except RuntimeError as error:
                ret.append(None)

        return ret


    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using Chatopera [Synonyms](https://github.com/chatopera/Synonyms) for chatbot, RAG.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]