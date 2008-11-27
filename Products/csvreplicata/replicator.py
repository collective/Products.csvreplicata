# -*- coding: utf-8 -*-
#
# File: replicator.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from zope.interface import implements
from zope import event
from zope.component import getUtility



import csv, cStringIO

from DateTime import DateTime
from time import strptime

from Products.CMFCore.utils import getToolByName

from Products.Archetypes.event import ObjectInitializedEvent
from Products.Archetypes.event import ObjectEditedEvent

from interfaces import Icsvreplicata
#from config import getHandlers, default_handler

from exceptions import *
from Products.csvreplicata import getPortalTypes

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.utils import getSiteEncoding

import logging
logger = logging.getLogger('CSV REPLICATOR')

    

class Replicator(object):
    """ a folder able to import/export its content as CSV 
    """
    implements(Icsvreplicata)

    def __init__(self, context):
        """Initialize adapter."""
        self.context = context
        self.flag = True
        self.site_encoding = getSiteEncoding(context)

    def csvimport(self, csvfile, encoding=None, delimiter=None,
                  stringdelimiter=None, datetimeformat=None,
                  conflict_winner="SERVER", wf_transition=None, zip=None,
                  vocabularyvalue="No", count_created=0, count_modified=0,
                  errors=[]):
        """
        CSV import.
        
        Calls recursively self._csvimport while self.flag
        """
        while self.flag :
            
            count_created, count_modified, export_date, errors = \
                    self._csvimport(csvfile, encoding, delimiter,
                                    stringdelimiter, datetimeformat,
                                    conflict_winner, wf_transition, zip,
                                    vocabularyvalue, count_created,
                                    count_modified, errors)

        return (count_created, count_modified, export_date, errors)

    def _csvimport(self, csvfile, encoding, delimiter, stringdelimiter,
                   datetimeformat, conflict_winner, wf_transition, zip,
                   vocabularyvalue, count_created, count_modified, errors):
        
            csvfile.seek(0)
        
            # get portal types
            types = getPortalTypes(self.context)
            
            # read parameters
            csvtool = getToolByName(self.context, "portal_csvreplicatatool")
            if encoding is None:
                encoding = csvtool.getEncoding()
            if delimiter is None:
                delimiter = csvtool.getDelimiter()
            if stringdelimiter is None:
                stringdelimiter = csvtool.getStringdelimiter()
            if datetimeformat is None:
                #datetimeformat = csvtool.getDateTimeFormat()
                datetimeformat = "%Y-%m-%d"
            self.datetimeformat = datetimeformat
            self.vocabularyvalue = vocabularyvalue
                
                
            # read csv
            reader = csv.reader(csvfile, delimiter=delimiter,
                                quotechar=stringdelimiter,
                                quoting=csv.QUOTE_NONNUMERIC)
            line = 1
            # parse header
            head = reader.next()
            export_folder = head[0]
            export_date_str = str(head[1])
            export_date = DateTime(int(export_date_str[0:4]),
                                   int(export_date_str[4:6]),
                                   int(export_date_str[6:8]),
                                   int(export_date_str[8:10]),
                                   int(export_date_str[10:12]),
                                   int(export_date_str[12:14]))
            
            # parse content
            specific_fields = None
            label_line = False
            needs_another_loop = False
            for row in reader:
                line = line + 1
                if not label_line:
                    # read type fields
                    if row[0] == "parent":
                        specific_fields = row[3:]
                        # next line must not be considered (labels line)
                        label_line = True
                    # read values
                    else:
                        try:
                            (is_new, is_modified) = \
                                            self.importObject(row,
                                                              specific_fields,
                                                              types[row[2]],
                                                              conflict_winner,
                                                              export_date,
                                                              wf_transition,
                                                              zip)
                            if is_new:
                                count_created = count_created + 1
                            elif is_modified:
                                count_modified = count_modified + 1
    
                        except csvreplicataConflictException, e:
                            #errors.append("Conflict on line " + \
                                          #str(line)+": %s" % (e))
                            
                            # here content is modified during a second
                            # (or more) parsing "
                            pass
                            
                        except csvreplicataBrokenReferenceException, e:
                            needs_another_loop = True

                        except csvreplicataNonExistentContainer, e:
                            needs_another_loop = True
                            pass
    
                        except Exception, e:
                            errors.append("Error in line "+str(line) + \
                                          ": %s" % (e))
                            
                else:
                    label_line = False
                    
            self.flag = needs_another_loop
            
            return (count_created, count_modified, export_date, errors)
        


    def importObject(self, row, specific_fields, type, conflict_winner,
                     export_date, wf_transition, zip):
        """
        """
        modified = False
        is_new_object = False
        protected = True
        parent_path = row[0]
        id = row[1]
        type_class = row[2]
        if parent_path == "":
            container = self.context
        else:
            try:
                container = self.context.unrestrictedTraverse(parent_path)
            except:
                raise csvreplicataNonExistentContainer, \
                "Non existent container %s " % parent_path
            
            
        obj = getattr(container, id, None)
        if obj is None:
            # object does not exist, let's create it
            attool = getToolByName(self.context, 'archetype_tool')
            at = attool.lookupType(type[0], type[1])
            portal_type = at['portal_type']
            container.invokeFactory(portal_type, id=id)
            obj = getattr(container, id)
            is_new_object = True
            protected = False
        else:
            # object exists, so check conflicts
            lastmodified = obj.modified()
            if lastmodified > export_date:
                if conflict_winner == "LOCAL":
                    protected = False
            else:
                protected = False
                
        # update object
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        handlers = csvtool.getHandlers()
        i = 3
        for f in specific_fields:
            if f is not None and f != "":
                type = obj.Schema().getField(f).getType()
                h = handlers.get(type, handlers['default_handler'])
                handler = h['handler_class']
                old_value = handler.get(obj, f, context=self)
                if old_value != row[i]:
                    if protected:
                        raise csvreplicataConflictException, \
                        "Overlapping content modified on" \
                        " the server after exportation"
                    else:
                        modified = True
                        if h['file']:
                            handler.set(obj, f, row[i], context=self, zip=zip)
                        else:
                            handler.set(obj, f, row[i], context=self)
            i = i+1
        
        # call events
        if is_new_object:
            event.notify(ObjectInitializedEvent(obj))
            obj.at_post_create_script()
            obj.indexObject()
            try:
                wftool = getToolByName(self.context, 'portal_workflow')
                wftool.doActionFor( obj, wf_transition)
            except Exception:
               pass     
        elif modified:
            event.notify(ObjectEditedEvent(obj))
            obj.at_post_edit_script()
            obj.reindexObject()
    
        return (is_new_object, modified)
    
    def csvexport(self, encoding=None, delimiter=None, stringdelimiter=None,
                  datetimeformat=None, depth=1, wf_states=None, zip=None,
                  vocabularyvalue="No", exportable_content_types=None):
        """
        """
        # read parameters
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        if encoding is None:
            encoding = csvtool.getEncoding()
        if delimiter is None:
            delimiter = csvtool.getDelimiter()
        if stringdelimiter is None:
            stringdelimiter = csvtool.getStringdelimiter()
        if datetimeformat is None:
            #datetimeformat = csvtool.getDateTimeFormat()
            datetimeformat = "%Y-%m-%d"
        self.datetimeformat = datetimeformat
        self.vocabularyvalue = vocabularyvalue

        
        # initialize csv
        stream = cStringIO.StringIO()
        writer = csv.writer(stream, delimiter=delimiter,
                            quotechar=stringdelimiter,
                            quoting=csv.QUOTE_NONNUMERIC)
        
        writer.writerow(["/".join\
                         (self.context.getPhysicalPath()).encode(encoding),
                         DateTime().strftime(format='%Y%m%d%H%M%S').\
                         encode(encoding)])
        
        # search objects
        #exportable_content_types = csvtool.getReplicableTypesSorted()
        if exportable_content_types is not None:
            if self.context.Type() == "Smart Folder":
                all = self.context.queryCatalog(full_objects=True)
                exportable_objects = []
                for o in all:
                    if o.Type() in exportable_content_types:
                        exportable_objects.append(o)
            else:
                query = {'portal_type': exportable_content_types}
                if depth == 0:
                    path = {'query':"/".join(self.context.getPhysicalPath())}
                else:
                    path = {'query':"/".join(self.context.getPhysicalPath()),
                            'depth':depth}
                query['path'] = path
                
                if wf_states is not None:
                    query['review_state'] = wf_states
                    
                search_exportable = self.context.portal_catalog.searchResults(
                    query)
                exportable_objects = [o.getObject() for o in search_exportable]
        else:
            exportable_objects = []
        
        # export content
        currenttype = None
        currentfields = []
        for obj in exportable_objects:
            type_info = str(obj.getTypeInfo().id)
            if not(type_info == currenttype):
                currenttype = type_info
                # get type fields
                currentfields = self.getTypeFields(type_info)
                # write ids
                writer.writerow([s[0].encode(encoding) for s in currentfields])
                # writes labels
                writer.writerow([s[1].encode(encoding) for s in currentfields])
                # store type specific fields list
                current_specific_fields = [f[0] for f in currentfields[3:]]
                
            values = self.getObjectValues(obj, current_specific_fields, zip)
            i = 0
            for value in values:
                if type(value) is not type(u''):
                    values[i] = value.decode(self.site_encoding)
                i += 1
            
            # write values
            writer.writerow([s.encode(encoding) for s in values])
        
        return stream.getvalue()

    def getTypeFields(self, type):
        """
        """
        types = getPortalTypes(self.context)
        attool = getToolByName(self.context, 'archetype_tool')
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        if csvtool.replicabletypes.has_key(type):
            schematas = csvtool.replicabletypes[type]
        else:
            schematas = []
        notExportableFieldClasses = csvtool.getExcludedfieldsclasses()
        notExportableFields = csvtool.getExcludedfields()
        at = attool.lookupType(types[type][0], types[type][1])
        at_class = at['klass']
        types = [('parent', 'Parent folder'), ('id', 'Identifier'),
                ('type','Content type')] 
        for schemata in schematas:
            fields = at_class.schema.getSchemataFields(schemata)
            #TODO: use getTranslationService to get the i18n translation
            types.extend([(f.getName(), f.widget.label) 
                          for f in fields 
                          if f.__class__.__name__ not in \
                          notExportableFieldClasses 
                          and f.getName() not in notExportableFields])
        return types
    
    def getObjectValues(self, obj, specific_fields, zip):
        """
        """
        # compute parent path
        current = "/".join(self.context.getPhysicalPath())
        parent_path = "/".join(obj.getParentNode().getPhysicalPath())
        if parent_path == current:
            parent_path = ""
        elif parent_path.startswith(current+"/"):
            parent_path = parent_path[len(current)+1:]
            
        # add the 3 standard first columns
        values = [parent_path, obj.id, obj.getTypeInfo().id]
        
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        handlers = csvtool.getHandlers()
        # add specific columns
        for f in specific_fields:
            type = obj.Schema().getField(f).getType()
            h = handlers.get(type, handlers['default_handler'])
            handler = h['handler_class']
            if h['file']:
                v = handler.get(obj, f, context=self, zip=zip)
            else:
                v = handler.get(obj, f, context=self)
            values.append(v)
        return values



    
