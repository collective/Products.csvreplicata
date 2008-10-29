# -*- coding: utf-8 -*-
#
# File: reference.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from Products.csvreplicata.exceptions import *
from base import CSVdefault

import logging
logger = logging.getLogger('HANDLER')
 
        
class CSVReference(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj, aslist=True)
        if v is None:
            return ''
        else:
            current = "/".join(obj.getPhysicalPath())+"/"
            l = []
            for o in v:
                path = "/".join(o.getPhysicalPath())
                if path.startswith(current):
                    l.append(path[len(current):])
                else:
                    l.append(path)
            return '\n'.join(l)
    
    def set(self, obj, field, value, context=None):
        if value == '':
            ref = []
        else:
            value = value.split('\n')
            ref = []
            for path in value:
                try:
                    target = obj.unrestrictedTraverse(path)
                    ref.append(target)
                except Exception:
                    raise csvreplicataBrokenReferenceException, path + \
                    " cannot be found"
                
        self.store(field, obj, ref)
        