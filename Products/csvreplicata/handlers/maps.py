# -*- coding: utf-8 -*-
import logging
from base import CSVdefault
logger = logging.getLogger('csvreplicata.CSVMap')
class CSVMap(CSVdefault):
    """
    """
    def set(self, obj, field, value, context=None):
        val = None
        if not value:
            value = None
        if isinstance(value, basestring):
            # desired input value is something like "(1.0, 2.0)"
            if value.startswith('(') and value.endswith(')'):
                val = eval(value)
        self.store(field, obj, val) 

