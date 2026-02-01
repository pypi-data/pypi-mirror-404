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

from typing import List
from functools import lru_cache
import synonyms

_flat_sum_array = lambda x: synonyms.np.sum(x, axis=0)  # 分子

'''
ZH TW
'''
# gobals
_vectors = dict()

@lru_cache(maxsize=12800)
def lookup_word_vector(word):
    '''
    Look up a word's vecor
    With cache, https://gist.github.com/promto-c/04b91026dd66adea9e14346ee79bb3b8
    '''
    try:
        y_ = synonyms.any2unicode(word).strip()
        return _vectors.word_vec(y_)
    except KeyError as error:
        return None


def get_text_vector(text):
    '''
    Get Text vector
    '''
    words = synonyms.jieba.cut(text, cut_all=False)

    terms = set()
    vectors = []
    for w in words:
        # 停用词
        if w in synonyms.STOPWORDS:
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


class EmbeddingsZhTw():

    def __init__(self, w2v_model_path: str):
        '''
        Docstring for __init__

        :param self: Description
        :param w2v_model_path: a 100 dims word2vec binary model
        :type w2v_model_path: str, get model binary file from https://nlp.tmu.edu.tw/word2vec/index.html
        '''
        global _vectors
        _vectors = synonyms.load_w2v(model_file=w2v_model_path)


    def get_wv(self, sentence, ignore=False):
        '''
        get word2vec data by sentence
        sentence is segmented string.
        '''
        global _vectors
        vectors = []
        for y in sentence:
            y_ = synonyms.any2unicode(y).strip()
            if y_ not in synonyms.STOPWORDS:
                synonyms.logging_debug("sentence %s word: %s" %(sentence, y_))
                try:
                    vectors.append(_vectors.word_vec(y_))
                except KeyError as error:
                    if ignore:
                        continue
                    else:
                        synonyms.logging_debug("not exist in w2v model: %s" % y_)
                        # c.append(np.zeros((100,), dtype=float))
                        random_state = np.random.RandomState(seed=(hash(y_) % (2**32 - 1)))
                        vectors.append(random_state.uniform(low=-10.0, high=10.0, size=(100,)))
        return vectors

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