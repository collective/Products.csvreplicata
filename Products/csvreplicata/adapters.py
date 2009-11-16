#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009, Mathieu PASQUET <mpa@makina-corpus.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the <ORGANIZATION> nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

__docformat__ = 'restructuredtext en'


class CSVReplicataPluginAbstract(object):
    """."""

    def __init__(self, replicator, context):
        self.replicator = replicator
        self.context = context

class CSVReplicataObjectSearcherAbstract(CSVReplicataPluginAbstract):
    """Just to be marked in zcml."""

    def getObjects(self):
        """."""
        raise Exception('Not implemented.')

class CSVReplicataExportPluginAbstract(CSVReplicataPluginAbstract):
    """."""

    def __init__(self, replicator, context):
        CSVReplicataPluginAbstract.__init__(self, replicator, context)
        self.ids = []
        self._datetimeformat = None

    def append_ids(self, row_ids):
        """."""
        row_ids.extend(
            [i 
             for i in self.ids 
             if not i in row_ids]
        )

    def fill_values(self, row, row_ids):
        """."""
        raise Exception('Not implemented.')

    def set_values(self, row, row_ids):
        """."""
        raise Exception('Not implemented.')

# example plugins for searching/exporting comments on plone2.5

# THE ZCML REGISTRATION WILL LOOK LIKE:
"""
  <adapter
      name="comments_searcher"
      factory=".adapters.CommentsObjectsSearcher"
      provides="Products.csvreplicata.interfaces.ICSVReplicataObjectsSearcher"
      for="Products.csvreplicata.interfaces.Icsvreplicata Products.CMFCore.interfaces._tools.IDiscussionTool"
    />    
  <adapter
      name="comments_exporter"
      factory=".adapters.CommentsExporter"
      provides="Products.csvreplicata.interfaces.ICSVReplicataExportPlugin"
      for="Products.csvreplicata.interfaces.Icsvreplicata zope.interface.Interface"
    /> 

    After, mark your portal_discussion with "ICSVReplicable" and export it.
"""


# THE CODE WILL LOOK LIKE

#import logging
#from datetime import datetime
#from DateTime import DateTime
#
#from zope.app.annotation.interfaces import IAnnotations
#from zope.component import getMultiAdapter
#from persistent.dict import PersistentDict
#from persistent.list import PersistentList
#
#from Products.CMFCore.utils import getToolByName
#from Products.csvreplicata.adapters import CSVReplicataObjectSearcherAbstract
#from Products.csvreplicata.adapters import CSVReplicataExportPluginAbstract
#from Products.csvreplicata.adapters import CSVReplicataPluginAbstract 

#def get_dict_csv_mapping(dictionnary,
#                         results = None,
#                         export_key = 'myexportkey',
#                         replicator = None
#                        ):
#    if isinstance(dictionnary, PersistentDict):
#        dictionnary = dict(dictionnary)
#    if not results:
#        results = {}
#    for key in dictionnary:
#        if isinstance(dictionnary[key], dict) or isinstance(dictionnary[key], PersistentDict):
#            get_dict_csv_mapping(dict(dictionnary[key]), results, '%s_%s' % (export_key, key), replicator)
#        else:
#            value = dictionnary[key]
#            #print '-->%s  %s <-> (%s, %s)' % (dict(dictionnary), key, value.__class__, value)
#            if (
#                isinstance(value, list) 
#                or isinstance(value, PersistentList)
#                or isinstance(value, tuple)
#            ):
#                value = ','.join(['%s' % a for a in value])
#            if isinstance(value, DateTime) or isinstance(value, datetime):
#                df = '%d/%m/%Y %H:%M:%S'
#                if replicator:
#                    getattr(replicator, 'datetimeformat', df)
#                value = value.strftime(df)
#            results['%s_%s' % (export_key, key)] = value
#    return results
#
#class CommentsObjectsSearcher(CSVReplicataObjectSearcherAbstract):
#
#    def getObjects(self):
#        logger = logging.getLogger('Products.csvreplicata.adapters.CommentsObjectsSearcher')
#        objs = []
#        c = getToolByName(self.context, 'portal_catalog')
#        bcomments = c.searchResults(**{
#            'meta_type': ['Discussion Item'],
#            'sort_on': 'in_reply_to',
#        })
#        lbcomments = len(bcomments)
#        logger.info('%s comments to export' % lbcomments)
#        SLICE = 1000
#        for i in range((lbcomments / SLICE) + 1):
#            lowerBound = SLICE * i
#            upperBound = SLICE * (i+1)
#            if upperBound > lbcomments:
#                upperBound = lbcomments
#            logger.info('Loading %s to %s comments.' % (lowerBound, upperBound))
#            #lowerBound, upperBound = 0, 3
#            scomments = [b.getObject() 
#                         for b in bcomments[lowerBound : upperBound]]
#            objs.extend(scomments)
#        logger.info('All comments loaded.')
#        return objs
#
#class CommentsExporter(CSVReplicataExportPluginAbstract):
#    """."""
#    def __init__(self, *args, **kwargs):
#        CSVReplicataExportPluginAbstract.__init__(self, *args, **kwargs)
#        self.comment = None
#        self.comment_as_dict = None
#        if self.context.meta_type in ['Discussion Item']:
#            try:
#                self.comment = {}
#                self.comment['creators']          = self.context.listCreators()
#                self.comment['contributors']      = self.context.contributors
#                self.comment['description']       = self.context.description
#                self.comment['effective_date']    = self.context.effective_date
#                self.comment['expiration_date']   = self.context.expiration_date
#                self.comment['id']                = self.context.id
#                self.comment['in_reply_to']       = self.context.in_reply_to
#                self.comment['modification_date'] = self.context.modification_date
#                self.comment['subject']           = self.context.subject
#                self.comment['text']              = self.context.text
#                self.comment['text_format']       = self.context.text_format
#                self.comment['title']             = self.context.title
#                self.comment['cooked_text']       = self.context.cooked_text
#                self.comment['language']          = self.context.language
#                self.comment['path']              = '/'.join(self.context.getPhysicalPath())
#                self.comment['in_reply_to']       = '/'.join(self.context.inReplyTo().getPhysicalPath())
#                self.comment['in_reply_to_chain'] = ['/'.join(obj.getPhysicalPath()) 
#                                                     for obj in self.context.parentsInThread()]
#                 
#                self.comment_as_dict = get_dict_csv_mapping(self.comment, 
#                                                            export_key = 'comment',
#                                                            replicator=self.replicator)
#                ks = self.comment_as_dict.keys()
#                ks.sort()
#                self.ids = ks
#            except:
#                pass
#
#    def fill_values(self, row, row_ids):
#        """."""
#        for id in row_ids:
#            if id in self.ids:
#                index = row_ids.index(id)
#                if index < len(row):
#                    row[index] = self.comment_as_dict[id]
#
#    def set_values(self, row, row_ids):
#        """."""
#        pass 
                 

# vim:set et sts=4 ts=4 tw=80:
