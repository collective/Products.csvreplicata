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
        if wf_transition=="None":
            wf_transition = None
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
             vocabularyvalue = vocabularyvalue)
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

        if exportfiles=="Yes":
            # initialize zipfile
            sIO = StringIO()
            zip = ZipFile(sIO,"w",8)
        else:
            zip = None

        csv = replicator.csvexport(
            encoding = encoding, 
            delimiter = delimiter,
            stringdelimiter = stringdelimiter, 
            depth = depth, 
            datetimeformat = datetimeformat, 
            wf_states = wf_states, 
            zip = zip, 
            vocabularyvalue = vocabularyvalue, 
            exportable_content_types = exportable_content_types
        )

        if exportfiles=="Yes":
            self.request.response.setHeader('Content-type','application/zip')
            self.request.response.setHeader('Content-Disposition', "attachment; filename=export.zip")

            zip.writestr("export.csv",csv)
            zip.close()
            return sIO.getvalue()
        else:
            if not encoding:
                encoding = 'UTF-8'
            self.request.response.setHeader('Content-type','text/csv;charset='+encoding)
            self.request.response.setHeader('Content-Disposition', "attachment; filename=export.csv")
            return csv


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
