# -*- coding: utf-8 -*-
#
# File: base.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from DateTime import DateTime
from time import strptime

from Products.CMFCore.utils import getToolByName

from Products.csvreplicata.exceptions import *

import logging
logger = logging.getLogger('HANDLER')

class CSVdefault(object):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).getRaw(obj)
        if v is None:
            return ''
        else:
            return str(v)
    
    def set(self, obj, field, value, context=None):
        if value=='':
            value = None
        self.store(field, obj, value)
        
    def store(self, field, obj, value):
        old_value = obj.Schema().getField(field).get(obj)
        if type(old_value) is tuple and type(value) is list:
            value = tuple(value)
        if obj.Schema().getField(field).writeable(obj):
            obj.Schema().getField(field).set(obj, value)
        else:
            raise csvreplicataPermissionException, "Insufficient privileges to modify this object and/or field"
        
class CSVString(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).getRaw(obj)
        
        vocab = obj.Schema().getField(field).vocabulary
        if context.vocabularyvalue == "Yes" and len(vocab)>0 :
            v = vocab.getValue(v)
            
        if v is None:
            v = ''
        
        return v
    
    def set(self, obj, field, value, context=None):
        v = obj.Schema().getField(field).getRaw(obj)
        
        vocab = obj.Schema().getField(field).vocabulary
        
        if context.vocabularyvalue == "Yes" and len(vocab)>0 :
            if vocab.getKey(value) is not None:
                value = vocab.getKey(value)
            else:
                value = ''
        self.store(field, obj, value)
        
class CSVInteger(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj)
        if v is None:
            return ''
        else:
            return str(v)
    
    def set(self, obj, field, value, context=None):
        if value=='':
            value = None
        elif value is not None:
            value = int(value)
        self.store(field, obj, value)

class CSVFloat(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj)
        if v is None:
            return ''
        else:
            return str(v)
    
    def set(self, obj, field, value, context=None):
        if value=='':
            value = None
        elif value is not None:
            value = float(value)
        self.store(field, obj, value)

class CSVBoolean(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj)
        if v is None:
            return ''
        else:
            return str(v)
    
    def set(self, obj, field, value, context=None):
        if value=='':
            value = None
        elif value is not None:
            if value=="True":
                value=True
            elif value=="False":
                value=False
            else:
                raise csvreplicataException, field+" must be True or False"
        self.store(field, obj, value)
        
class CSVLines(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj)
        if v is None:
            return ''
        else:
            return '\n'.join(v)
    
    def set(self, obj, field, value, context=None):
        if value=='':
            value = []
        else:
            value = value.split('\n')
        self.store(field, obj, value)
        
class CSVText(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj, mimetype="text/plain")
        return v
    
    def set(self, obj, field, value, context=None):
        self.store(field, obj, value)
        
class CSVDateTime(CSVdefault):
    """
    """
    def get(self, obj, field, context=None):
        """
        """
        if context is None:
            csvtool = getToolByName(obj, "portal_csvreplicatatool")
            #format = csvtool.getDateTimeFormat()
            format = '%d/%m/%Y'
        else:
            format = context.datetimeformat
            
        v = obj.Schema().getField(field).get(obj)
        if isinstance(v, DateTime):
            return v.strftime(format)
        else:
            return ''
    
    def set(self, obj, field, value, context=None):
        if context is None:
            csvtool = getToolByName(obj, "portal_csvreplicatatool")
            #format = csvtool.getDateTimeFormat()
            format = '%d/%m/%Y'
        else:
            format = context.datetimeformat
            
        if value=='':
            value = None
        else:
            try:
                dt = strptime(value, format)
                value = DateTime(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5])
                self.store(field, obj, value)
            except DateTime.DateTimeError, e:
                raise csvreplicataException, v+" is not a valid date/time"