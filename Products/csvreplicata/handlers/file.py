# -*- coding: utf-8 -*-
#
# File: file.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'


import os
import logging

from zope import interface

from Products.csvreplicata.exceptions import *
from Products.csvreplicata.interfaces import ICSVFile

from base import CSVdefault

logger = logging.getLogger('csvreplicata.HANDLER')

class CSVFile(CSVdefault):
    """
    """
    interface.implements(ICSVFile)

    def get(self, obj, field, context=None, zip=None, parent_path=''):
        """
        """
        f = obj.Schema().getField(field).get(obj)
        if not f :
            return ''
        else:
            filename = f.filename
            if zip is not None:
                #logger.error(obj.Schema().getField(field).getType())
                if obj.Schema().getField(field).getType() in \
                ("plone.app.blob.subtypes.file.ExtensionBlobField",
                 "Products.Archetypes.Field.FileField",
                 'Products.AttachmentField.AttachmentField.AttachmentField',
                 "Products.Archetypes.Field.ImageField"):

                    f = str(f.data)
                zip.writestr(os.path.join(parent_path, filename), f)
            return filename

    def set(self, obj, field, value, context=None, zip=None, parent_path = ''):
        if value == '':
            raise csvreplicataException, "No filename for %s" % (field)
        elif zip is None:
            raise csvreplicataException, "No zip file provided"
        else:
            if obj.Schema().getField(field).writeable(obj):
                try:
                    file = zip.read(os.path.join(parent_path, value))
                except KeyError, e:
                    raise csvreplicataMissingFileInArchive, "%s not found in zip file" % (value)
                obj.Schema().getField(field).set(obj, file)
                obj.Schema().getField(field).get(obj).setFilename(value)
            else:
                raise csvreplicataPermissionException, \
                "Insufficient privileges to modify this object and/or field"

