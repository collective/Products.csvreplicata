# -*- coding: utf-8 -*-
#
# File: file.py
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
 
        
class CSVFile(CSVdefault):
    """
    """
    
    def get(self, obj, field, context=None, zip=None):
        """
        """
        f = obj.Schema().getField(field).get(obj)
        if f is None:
            return ''
        else:
            filename = f.filename
            if zip is not None:
                if obj.Schema().getField(field).getType()=="plone.app.blob.subtypes.file.ExtensionBlobField":
                    f=f.data
                zip.writestr(filename, f)
            return filename
    
    def set(self, obj, field, value, zip=None):
        if value=='':
            raise csvreplicataException, "No filename for %s" % (field)
        elif zip is None:
            raise csvreplicataException, "No zip file provided"
        else:
            if obj.Schema().getField(field).writeable(obj):
                obj.Schema().getField(field).set(obj, zip.read(value))
                obj.Schema().getField(field).get(obj).setFilename(value)
            else:
                raise csvreplicataPermissionException, "Insufficient privileges to modify this object and/or field"
        
        