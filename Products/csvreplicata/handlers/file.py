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

from Products.CMFPlone.utils import normalizeString
from Products.csvreplicata.exceptions import *
from Products.csvreplicata.interfaces import ICSVFile

from base import CSVdefault

logger = logging.getLogger('csvreplicata.HANDLER')

def get_zip_filename(filename):
    zip_filename = None
    if '.' in filename:
        filenamepref, filenamesuf = (
            ''.join(filename.split('.')[:-1]),
            ''.join(filename.split('.')[-1])
        )
        ufilename = ''
        try:
            ufilename = unicode(filenamepref)
        except:
            ufilename = unicode(filenamepref.decode('utf-8'))
        zip_filename = '%s%s%s' % (
                ufilename,
                '.', filenamesuf)
    else:
        ufilename = ''
        try:
            ufilename = unicode(filename)
        except:
            ufilename = unicode(filename.decode('utf-8'))
        zip_filename = normalizeString(
            ufilename,
            encoding='utf-8') 
    return zip_filename
        

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
            # zip module encode filename with latin1 format !
            # we provide a normalize string to avoid encoding zipe filenames problems
            filename = f.filename
            zip_filename = ''
            if not filename:
                # fallback to id
                try:
                    filename = f.getId()
                except:
                    logger.error('Cant find filename for: %s' % '/'.getPhysicalPath())
            if filename:
                zip_filename = get_zip_filename(filename)
            if zip is not None and zip_filename:
                #logger.error(obj.Schema().getField(field).getType())
                if obj.Schema().getField(field).getType() in \
                ("plone.app.blob.subtypes.file.ExtensionBlobField",
                 "Products.Archetypes.Field.FileField",
                 'Products.AttachmentField.AttachmentField.AttachmentField',
                 "plone.app.blob.subtypes.image.ExtensionBlobField",
                 "plone.app.blob.subtypes.file.ExtensionBlobField",
                 "plone.app.blob.subtypes.blob.ExtensionBlobField",
                 "Products.Archetypes.Field.ImageField"):

                    fdata = str(f.data)

                full_path = os.path.join(parent_path, zip_filename)
                zip.writestr(full_path, fdata)
            return zip_filename

    def set(self, obj, field, value, context=None, zip=None, parent_path = ''):
        if value == '':
            raise csvreplicataException, "No filename for %s" % (field)
        elif zip is None:
            raise csvreplicataException, "No zip file provided"
        else:
            if obj.Schema().getField(field).writeable(obj):
                try:
                    # filename in zip is different from value
                    # filename == normalizeString(value,encoding='utf-8')
                    zip_filename = get_zip_filename(value)
                    filestream = zip.read(os.path.join(parent_path, zip_filename))
                except KeyError, e:
                    raise csvreplicataMissingFileInArchive, "%s not found in zip file" % (zip_filename)

                obj.Schema().getField(field).set(obj, filestream)
                obj.Schema().getField(field).get(obj).setFilename(value.encode('utf-8'))
            else:
                raise csvreplicataPermissionException, \
                "Insufficient privileges to modify this object and/or field"

