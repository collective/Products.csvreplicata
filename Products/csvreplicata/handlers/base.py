# -*- coding: utf-8 -*-
#
# File: base.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from zope import interface
from Products.csvreplicata.interfaces import ICSVDefault

from DateTime import DateTime

from datetime import datetime

from time import strptime

from Products.CMFCore.utils import getToolByName

from Products.csvreplicata.exceptions import *

import logging
logger = logging.getLogger('HANDLER')


def get_padded_year(v, format):
    yformat = format.replace('%Y', '_YEARBEGIN_%Y_YEAREND_')
    datestr = v.strftime(yformat)
    year = datestr.split('_YEARBEGIN_')[1].split('_YEAREND_')[0]
    year = (4 - len(year))*'0'+year
    ret = (datestr.split('_YEARBEGIN_')[0] +
           year +
           datestr.split('_YEAREND_')[1]
          )
    return ret

class CSVdefault(object):
    """
    """
    interface.implements(ICSVDefault)


    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).getRaw(obj)
        if v is None:
            return ''
        else:
            return str(v)

    def set(self, obj, field, value, context=None):
        if value == '':
            value = None
        self.store(field, obj, value)

    def store(self, field, obj, value):
        old_value = obj.Schema().getField(field).get(obj)
        if type(old_value) is tuple and type(value) is list:
            value = tuple(value)
        if obj.Schema().getField(field).writeable(obj):
            obj.Schema().getField(field).set(obj, value)
        else:
            raise csvreplicataPermissionException, \
            "Insufficient privileges to modify this object and/or field"

class CSVString(CSVdefault):
    """
    """
    # special case for bizarious collage vocabs.
    collage_vocab = 'Products.Collage.content._portlet.PortletVocabulary'

    def getLenVocab(self, vocab):
        """
        Some vocabularies like the old Products.Collage.content._portlet.PortletVocabulary
        do not have __len__. So just bypass the check
        """
        lenvocab = 0
        try:
            lenvocab = len(vocab)
        except AttributeError, e:
            lenvocab = 1
        return lenvocab


    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).getRaw(obj)

        vocab = obj.Schema().getField(field).vocabulary


        if context.vocabularyvalue == "Yes" and self.getLenVocab(vocab):
            if hasattr(vocab, 'getValue'):
                v = vocab.getValue(v)
            # some thirdparty modules have list instead of nice vocabs.
            elif isinstance(vocab, list):
                if v in vocab:
                    return v
            elif '%s'%vocab.__class__ == self.collage_vocab:
                if v in vocab.getDisplayList(obj):
                    return vocab.getDisplayList(obj).getValue(v)
            elif hasattr(obj, vocab):
                v = getattr(obj, vocab)().getValue(v)
        if v is None:
            v = ''
        return v

    def set(self, obj, field, value, context=None):
        v = obj.Schema().getField(field).getRaw(obj)

        vocab = obj.Schema().getField(field).vocabulary

        lenvocab = 1
        if context.vocabularyvalue == "Yes" and self.getLenVocab(vocab):
            if isinstance(vocab, list):
                if value in vocab:
                    value = value
                else:
                    value = ''
            elif vocab.getKey(value) is not None:
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
        try:
            self.store(field, obj, value)
        except Exception, e:
            if field == 'subject':
                obj.setSubject(value)
            else:
                raise


class CSVText(CSVdefault):
    """
    """

    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).getRaw(obj)
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
            format = csvtool.getDateTimeFormat()
            #format = '%d/%m/%Y'
        else:
            format = context.datetimeformat

        v = obj.Schema().getField(field).get(obj)
        ret = ''
        if isinstance(v, DateTime):
            if 'Y' in format and v.year() < 1000:
                ret = get_padded_year(v, format)
            else:
                ret = v.strftime(format)
        return ret

    def set(self, obj, field, value, context=None):
        if context is None:
            csvtool = getToolByName(obj, "portal_csvreplicatatool")
            format = csvtool.getDateTimeFormat()
            #format = '%d/%m/%Y'
        else:
            format = context.datetimeformat

        if value == '':
            value = None
        else:
            try:
                t = strptime(value, format)
                dt = datetime(t[0], t[1], t[2], t[3], t[4], t[5])
                value = DateTime(dt)
                self.store(field, obj, value)
            except DateTime.DateTimeError, e:
                raise csvreplicataException, v + " is not a valid date/time"

