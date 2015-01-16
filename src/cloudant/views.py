#!/usr/bin/env python
"""
_views_

Utilities for handling design docs and the resulting views

"""


from .document import CloudantDocument


class Code(str):
    """
    _Code_

    """
    def __init__(self, s):
        super(Code, self).__init__(s)


class View(dict):
    """
    Dictionary based object representing a view

    """
    def __init__(self, view_name):
        super(View, self).__init__()
        self.view_name = view_name
        self.map = None
        self.reduce = None

    def to_json(self):
        result = {self.view_name: {}}
        if self.map:
            result[self.view_name]['map'] = self.map
        if self.reduce:
            result[self.view_name]['reduce'] = self.reduce
        return result

class DesignDocument(CloudantDocument):

    def fetch(self):
        super(DesignDocument, self).fetch()
        print "Fetched design doc"
        for view in self['views']:
            print view

