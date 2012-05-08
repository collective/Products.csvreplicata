# -*- coding: utf-8 -*-
#
# File: browser.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from zipfile import ZipFile
from cStringIO import StringIO
import os
import tempfile
import shutil


from zope.interface.interfaces import IInterface
from zope.interface.declarations import implements
from ZPublisher.Iterators import IStreamIterator

from Products.csvreplicata.interfaces import Icsvreplicata
from Products.csvreplicata import config

import logging
logger = logging.getLogger('CSV MANAGER')

class ReplicationManager(BrowserView):
    """ allow to manage CSV replication
    """

    def __init__(self, context, request):
        """Initialize browserview"""
        self.context = context
        self.request = request


    def kssClassesView(self):
        """
        Yet another plone25 wrapper.
        """
        if not config.PLONE25:
            return self.context.restrictedTraverse(
                '@@kss_field_decorator_view'
            )

    def getKssClasses(self):
        """
        Yet another plone25 wrapper.
        """
        try:
            kssClassesView = self.context.restrictedTraverse('@@kss_field_decorator_view')
            return kssClassesView.getKssClassesInlineEditable
        except Exception, e:
            if not config.PLONE25:
                raise

    def doImport(self):
        """
        """
        fileorigin = self.request.get("fileorigin")
        if fileorigin=="SERVER":
            csvtool = getToolByName(self.context, "portal_csvreplicatatool")
            import_dir_path = csvtool.getServerfilepath()
            file = open(os.path.join(import_dir_path, self.request.get("serverfile")))
        else:
            file = self.request.get("csvfile")

        replicator = Icsvreplicata(self.context)
        datetimeformat = self.request.get("datetimeformat")
        vocabularyvalue = self.request.get("vocabularyvalue")
        encoding = self.request.get("encoding")
        delimiter = self.request.get("delimiter")
        stringdelimiter = self.request.get("stringdelimiter")
        conflict_winner = self.request.get("conflictrule")
        wf_transition = self.request.get("wf_transition")
        partial_commit_number = 0
        try:
            partial_commit_number = int(self.request.get("partial_commit_number"))
        except:
            pass
        if wf_transition=="None":
            wf_transition = None
        plain_format = False
        if self.request.get('is_plain_format', '') == 'on':
            plain_format = True
        importfiles = self.request.get("importfiles")
        if importfiles=="Yes":
            zip = ZipFile(file)
            csvfile=StringIO()
            csvfile.write(zip.read("export.csv"))
            csvfile.seek(0)
        else:
            zip = None
            csvfile = file

        (count_created,
         count_modified,
         export_date,
         errors) = replicator.csvimport(
             csvfile,
             encoding = encoding,
             delimiter = delimiter,
             stringdelimiter = stringdelimiter,
             datetimeformat = datetimeformat,
             conflict_winner = conflict_winner,
             wf_transition = wf_transition,
             zip = zip,
             vocabularyvalue = vocabularyvalue,
             plain_format = plain_format,
             partial_commit_number=partial_commit_number,
         )
        if len(errors)==0:
            self.writeMessageOnPage(["All lines imported, %d object(s) created, %d object(s) modified." % (count_created, count_modified)])
            self.writeMessageOnPage(["This CSV file has been produced on "+str(export_date)+". To avoid inconsistencies, do not import this file anymore. It is preferable to export a new one."])
        else:
            self.writeMessageOnPage(["%d object(s) created, %d object(s) modified." % (count_created, count_modified)])
            self.writeMessageOnPage(errors, error = True)

        self.request.RESPONSE.redirect(self.context.absolute_url()+'/@@csvreplicata')

    def doExport(self):
        """
        """
        replicator = Icsvreplicata(self.context)
        encoding = self.request.get('encoding')
        depth = int(self.request.get('depth','1'))
        datetimeformat = self.request.get("datetimeformat")
        vocabularyvalue = self.request.get("vocabularyvalue")
        delimiter = self.request.get("delimiter")
        stringdelimiter = self.request.get("stringdelimiter")
        wf_states = self.request.get("wf_states", 'Any')
        selected_exportable_content_types = self.request.get("exportable_content_types")

        # handling of selected types
        exportable_content_types = selected_exportable_content_types

        if 'Any' in wf_states:
            wf_states = None
        exportfiles = self.request.get("exportfiles")

        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        tmp = csvtool.getTempPath()
        delete_on_exit = False
        delete_grand_parent = False
        if not tmp:
            delete_grand_parent = True
            tmp = tempfile.mkdtemp()

        tmppath = tempfile.mkdtemp(dir=tmp)

        zippath = os.path.join(tmppath, 'export.zip')
        if exportfiles=="Yes":
            # initialize zipfile
            zip = ZipFile(zippath, "w", 8)
        else:
            zip = None

        plain_format = False
        if self.request.get('is_plain_format', '') == 'on':
            plain_format = True

        csvpath = os.path.join(tmppath, 'export.csv')
        csvstream = open(csvpath, 'w')
        csv = replicator.csvexport(
            encoding = encoding,
            delimiter = delimiter,
            stringdelimiter = stringdelimiter,
            depth = depth,
            datetimeformat = datetimeformat,
            wf_states = wf_states,
            zip = zip,
            vocabularyvalue = vocabularyvalue,
            exportable_content_types = exportable_content_types,
            stream = csvstream,
            plain_format = plain_format
        )
        csvstream.flush()
        csvstream.close()
        streamed = EphemeralStreamIterator(
            csvpath,
            delete_parent=True,
            delete_grand_parent=delete_grand_parent)
        if exportfiles=="Yes":
            self.request.response.setHeader('Content-type','application/zip')
            self.request.response.setHeader('Content-Disposition', "attachment; filename=export.zip")
            zip.write(csvpath, "export.csv")
            zip.close()
            streamed.file.close()
            streamed = EphemeralStreamIterator(
                zippath,
                delete_parent=True,
                delete_grand_parent=delete_grand_parent)
        else:
            if not encoding:
                encoding = 'UTF-8'
            self.request.response.setHeader('Content-type','text/csv;charset='+encoding)
            self.request.response.setHeader('Content-Disposition', "attachment; filename=export.csv")

        self.request.response.setHeader('Content-Length', str(len(streamed)))
        return streamed

    def writeMessageOnPage(self, messages, ifMsgEmpty = '', error = False):
        """adds portal message
        """
        plone_tools = getToolByName(self, 'plone_utils')
        if plone_tools is not None:
            #portal message type
            if error:
                msgType = 'error'
            else:
                msgType = 'info'

            #if empty
            if (len(messages)==0):
               messages = [ifMsgEmpty]

            #display it
            for msg in messages:
                if len(msg)==0:
                    mess = ifMsgEmpty
                else:
                    mess = msg
                if len(mess)>0:
                    plone_tools.addPortalMessage(mess, msgType, self.request)

    def getAllWorkflowStates(self):
        """
        """
        plone_wf = getToolByName(self.context, 'portal_workflow')
        states = []
        for wf in plone_wf.getChildNodes():
            for s in wf.states.getChildNodes():
                if not(s.id in states):
                    states.append(s.id)
        return states

    def getAllWorkflowTransitions(self):
        """
        """
        plone_wf = getToolByName(self.context, 'portal_workflow')
        transitions = []
        for wf in plone_wf.getChildNodes():
            for t in wf.transitions.getChildNodes():
                if not(t.id in transitions):
                    transitions.append(t.id)
        return transitions

    def getServerImportableFiles(self):
        """
        """
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        import_dir_path = csvtool.getServerfilepath()
        if import_dir_path is not None and import_dir_path!='':
            return os.listdir(import_dir_path)
        return []


# badly stolen ideas from dexterity
# see https://svn.plone.org/svn/plone/plone.dexterity/trunk/plone/dexterity/filerepresentation.py

class FileStreamIterator(object):
    """Simple stream iterator to allow efficient data streaming.
    """

    # Stupid workaround for the fact that on Zope < 2.12, we don't have
    # a real interface
    if IInterface.providedBy(IStreamIterator):
        implements(IStreamIterator)
    else:
        __implements__ = (IStreamIterator,)

    def __init__(self, path, size=None, chunk=1<<16):
        """Consume data (a str) into a temporary file and prepare streaming.

        size is the length of the data. If not given, the length of the data
        string is used.

        chunk is the chunk size for the iterator
        """
        self.path = path
        self.file = open(path)
        self.file.seek(0)
        self.size = os.stat(path).st_size
        self.chunk = chunk

    def __iter__(self):
        return self

    def next(self):
        data = self.file.read(self.chunk)
        if not data:
            self.file.close()
            raise StopIteration
        return data

    def __len__(self):
        return self.size


class EphemeralStreamIterator(FileStreamIterator):
    """File and maybe its parent directory is deleted when readed"""

    def __init__(self, path, size=None, chunk=1<<16, delete_parent = False, delete_grand_parent=False):
        FileStreamIterator.__init__(self, path, size, chunk)
        self.delete_parent = delete_parent
        self.delete_grand_parent = delete_grand_parent

    def next(self):
        try:
            return FileStreamIterator.next(self)
        except:
            os.unlink(self.path)
            if self.delete_parent:
                shutil.rmtree(os.path.dirname(self.path))
            if self.delete_grand_parent:
                shutil.rmtree(os.path.dirname(os.path.dirname(self.path)))
            raise



