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

# see ./exportimport_plugins.py and ./meta.zcml to know how to implenent plugins

class CSVReplicataPluginAbstract(object):
    """."""

    def __init__(self, replicator, context):
        self.replicator = replicator
        self.context = context
        if not getattr(self, 'prefix', False):
            self.prefix = 'ReplicataPlugin_%s_%s_' % (
                self.__module__.replace('.', '_'),
                self.__class__.__name__
            )

class CSVReplicataObjectSearcherAbstract(CSVReplicataPluginAbstract):
    """Just to be marked in zcml."""

    def getObjects(self):
        """."""
        raise Exception('Not implemented.')

class CSVReplicataExportImportPluginAbstract(CSVReplicataPluginAbstract):
    """."""

    def __init__(self, replicator, context):
        CSVReplicataPluginAbstract.__init__(self, replicator, context)
        self.ids = []
        self._datetimeformat = None

    def compute_id(self, id):
         return '%s%s' % (self.prefix, id)

    def computedid_to_id(self, cid):
        if cid.startswith(self.prefix):
            return cid.replace(self.prefix, '', 1)

    def append_ids(self, row_ids):
        """."""
        row_ids.extend(
            ['%s%s' % (self.prefix, i)
             for i in self.ids
             if not i in row_ids]
        )

    def fill_values(self, row, row_ids):
        """."""
        raise Exception('Not implemented.')

    def set_values(self, row, row_ids):
        """."""
        for id in row_ids:
            cid = self.computedid_to_id(id)
            if (bool(cid) and (cid in self.ids)):
                self.set_value(cid, row[row_ids.index(id)], row, row_ids)

    def set_value(self, id, value):
        """."""
        raise Exception('Not implemented.', prefix='')

# BBB: COMPATIBILITY
CSVReplicataExportPluginAbstract = CSVReplicataExportImportPluginAbstract


# vim:set et sts=4 ts=4 tw=80:
