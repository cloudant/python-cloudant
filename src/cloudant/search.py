#!/usr/bin/env python
# Copyright (c) 2016 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
API module for composing and executing Cloudant Search indexes.
"""
from ._common_util import codify
from cloudant.error import CloudantException


class SearchIndex(dict):
    """
    Encapsulates a search index as a dictionary based object, exposing the
    search index function as an attribute and supporting query/data access
    through the search endpoint.  A Search object is instantiated with a
    reference to a DesignDocument and is typically used as part of the
    :class:`~cloudant.design_document.DesignDocument`
    search index management API.
    """
    def __init__(
            self,
            ddoc,
            search_index_name,
            search_index=None,
            **kwargs
    ):
        super(SearchIndex, self).__init__()
        self._design_doc = ddoc
        self._search_index_name = search_index_name
        self['index'] = codify(search_index)
        if kwargs:
            super(SearchIndex, self).update(kwargs)

    @property
    def url(self):
        """
        Constructs and returns the Cloudant Search URL.

        :returns: Search URL
        """
        if not self._search_index_name:
            return '/'.join([
                self._design_doc.document_url,
                '_search',
                self._search_index_name
            ])
        else:
            msg = 'Search index name is None or was not provided.'
            raise CloudantException(msg)

