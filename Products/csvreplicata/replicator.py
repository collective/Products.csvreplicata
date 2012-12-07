# -*- coding: utf-8 -*-
#
# File: replicator.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

import logging
from DateTime import DateTime
from time import strptime

from pprint import pprint
import csv
import cStringIO

from Acquisition import aq_inner
import transaction
import re
from exceptions import *
import itertools

from zope.interface import implements
from zope import event
from zope.component import getUtility, getAdapters

from Products.CMFCore.utils import getToolByName
from Products.csvreplicata import config

if config.PLONE25:
    from zope.app.event.objectevent import ObjectCreatedEvent  as ObjectInitializedEvent
    from zope.app.event.objectevent import ObjectModifiedEvent as ObjectEditedEvent
else:
    # plone > 2.5
    from Products.Archetypes.event import ObjectInitializedEvent
    from Products.Archetypes.event import ObjectEditedEvent

from interfaces import Icsvreplicata
from interfaces import ICSVReplicataObjectsSearcher
from interfaces import ICSVReplicataExportImportPlugin
#from config import getHandlers, default_handler

from Products.csvreplicata import getPortalTypes

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.utils import getSiteEncoding


re_flags = re.M|re.S|re.U
logger = logging.getLogger('CSV REPLICATOR')

REMOVE_SPECIALCHARS = re.compile(u"((\x0d\x0a)|(\r\n))", re_flags)
DOUBLELINER = re.compile(u"\n\s*(\n\s*)+", re_flags)
EMPTYLINE  = re.compile(u"^()$", re_flags)


def P(item):
    try:
        return item.getPath()
    except AttributeError:
        return "/".join(
            item.getPhysicalPath())


def get_brain_from_path(catalog, i):
    return catalog.searchResults({
        'path' : {"depth":0,
                  'query':i},
    })[0]


def find_same_level_ancestors(itema, itemb):
    catalog = itema.portal_catalog
    lineagea = itema.getPath().split('/')
    lineageb = itemb.getPath().split('/')
    lasta, lastb = "", ""
    while not "".join(lineageb).startswith(
        "".join(lineagea)
    ):
        lasta = lineagea.pop()
    if lasta:
        lineagea.append(lasta)
    lineageb = lineageb[:len(lineagea)]
    # first child after common ancestor
    bra = get_brain_from_path(catalog, "/".join(lineagea))
    # first child after common ancestor
    brb = get_brain_from_path(catalog, "/".join(lineageb))
    return ((bra, get_position(bra)),
            (brb, get_position(brb)))

def get_container(i):
    catalog = i.portal_catalog
    ppath = i.portal_url.getPortalPath()
    portal = i.portal_url.getPortalObject()
    path = '/'.join(P(i).split('/')[:-1])
    if ppath == path:
        ret = portal
    else:
        ret = get_brain_from_path(catalog, path)
    return ret


def get_contained(i):
    catalog = i.portal_catalog
    path = '/'.join(i.getPath().split('/')[:-1])
    return [a.id for a in catalog.searchResults(
        {'path' : {"depth":1, 'query':path},
         'sort_on': 'getObjPositionInParent',
        })]

def get_position(i):
    return get_contained(i).index(i.id)

def get_reverse_position(i):
    pos = get_position(i)
    return len(get_contained(i)) - pos

def custom_sort(a, b):
    ka = "%s__SEP__%s"% (
        P(get_container(a)), get_reverse_position(a)
    )
    kb = "%s__SEP__%s"% (
        P(get_container(b)), get_reverse_position(b)
    )
    ret = 0
    if ka < kb:
        ret = 1
    if ka > kb:
        ret = -1
    return ret

def fill_empty_fields_and_write_rows(writer, ids, labels=None, rows=None):
    if ids:
        writer.writerow(ids)
    if labels:
        writer.writerow(labels)
    if rows:
        # fill empty field left by non value
        # eg plugin that does not match for a particular object
        for index, row in enumerate(rows[:]):
            if ids:
                if len(row) < len(ids):
                    for i in range(len(ids) - len(row)):
                        rows[index].append(None)
            writer.writerow(rows[index])

class IgnoreLineException(Exception):
    """IngoreLineException."""

class NoneIterator(object):

    def __init__(self, fillvalue=None):
        self.fillvalue = fillvalue

    def next(self): return self.fillvalue


class lazy_izip(object):
    """Rewrite some izip_longest iterator, not present in py2.4.
    This one is eval just in time"""


    def __init__(self, *args, **kwargs):
        self.lists = args
        self.iterables = [itertools.chain(i) for i in self.lists]
        self.count = len(self.lists)
        self.fillvalue = kwargs.get('fillvalue', None)

    def get_next(self, iterable):
        try:
            return iterable.next()
        except:
            if self.count > 1:
                self.count -= 1
                return self.fillvalue
            else:
                raise

    def __iter__(self):
        while True:
            yield [self.get_next(iterable) for iterable in self.iterables]



def strcsv_to_datetime(export_date_str):
    return DateTime(int(export_date_str[0:4]),
                           int(export_date_str[4:6]),
                           int(export_date_str[6:8]),
                           int(export_date_str[8:10]),
                           int(export_date_str[10:12]),
                           int(export_date_str[12:14]))

class Replicator(object):
    """ a folder able to import/export its content as CSV
    """
    implements(Icsvreplicata)

    def __init__(self, context):
        """Initialize adapter."""
        self.context = context
        self.flag = True
        self.site_encoding = getSiteEncoding(context)

    def csvimport(self, csvfile,
                  encoding=None,
                  delimiter=None,
                  stringdelimiter=None,
                  datetimeformat=None,
                  conflict_winner="SERVER",
                  wf_transition=None,
                  zip=None,
                  vocabularyvalue="No",
                  count_created=0,
                  count_modified=0,
                  errors=None,
                  ignore_content_errors=False,
                  plain_format = None,
                  partial_commit_number=0):
        """
        CSV import.

        Calls recursively self._csvimport while self.flag
        """
        if not errors:
            errors = []
        loops = 0
        old_count_created, old_count_modified = 0, 0
        status = {}
        while (False or self.flag):
            loops = loops + 1
            if loops > 1:
                logger.warn('Retry: %s' % loops)
            (count_created, count_modified,
             export_date, errors) = (
                 self._csvimport(
                     csvfile,
                     encoding=encoding,
                     delimiter=delimiter,
                     stringdelimiter=stringdelimiter,
                     datetimeformat=datetimeformat,
                     conflict_winner=conflict_winner,
                     wf_transition=wf_transition,
                     zip=zip,
                     vocabularyvalue=vocabularyvalue,
                     count_created=count_created,
                     count_modified=count_modified,
                     errors=errors,
                     ignore_content_errors=ignore_content_errors,
                     plain_format=plain_format,
                     partial_commit_number=partial_commit_number,
                     loops = loops,
                     status = status,
                 )
             )
            # after 10 loops, we stop trying
            # to resolve broken references
            if loops > 10 and not (
                old_count_modified != count_modified
                or old_count_created != count_created
            ):
                self.flag = False
            old_count_created  = count_created
            old_count_modified = count_modified
        return (count_created, count_modified,
                export_date, errors)

    def _csvimport(self,
                   csvfile,
                   encoding,
                   delimiter,
                   stringdelimiter,
                   datetimeformat,
                   conflict_winner,
                   wf_transition,
                   zip,
                   vocabularyvalue,
                   count_created,
                   count_modified,
                   errors,
                   ignore_content_errors=False,
                   plain_format=None,
                   partial_commit_number=0,
                   loops = 0,
                   status = None):
            if status is None:
                status = {}
            csvfile.seek(0)
            # get portal types
            types = getPortalTypes(self.context)

            # read parameters
            csvtool = getToolByName(
                self.context, "portal_csvreplicatatool")
            if plain_format is None:
                plain_format = csvtool.getPlainFormat()
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
                                quotechar=stringdelimiter)
#                                 ,
#                                 quoting=csv.QUOTE_NONNUMERIC)
            line = 1
            # parse header
            head = reader.next()
            export_folder = head[0]
            export_date_str = str(head[1])
            export_date = None
            if not plain_format:
                export_date = strcsv_to_datetime(export_date_str)

            # parse content
            specific_fields = None
            label_line = False
            needs_another_loop = False
            offset = 0
            if plain_format:
                offset = 2

            if plain_format:
                specific_fields = head[offset+3:]
            #rows = [r for r in reader]
            #for row in rows:
            for idx, row in enumerate(reader):
                #if plain_format and (line ==3):
                #    export_date = strcsv_to_datetime(row[1])
                line = line + 1
                if not label_line:
                    # read type fields
                    if (row[0] == "parent") and not plain_format:
                        specific_fields = row[offset+3:]
                        # next line must not be considered (labels line)
                        label_line = True
                    # read values
                    else:
                        try:
                            # labels
                            if plain_format and (line == 2):
                                raise IgnoreLineException()
                            if plain_format:ignore_content_errors=True
                            (is_new, is_modified, incomplete) = \
                                    self.importObject(
                                        row[offset:],
                                        specific_fields,
                                        types[row[offset+2]],
                                        conflict_winner,
                                        export_date,
                                        wf_transition,
                                        zip,
                                        encoding=encoding,
                                        ignore_content_errors=ignore_content_errors,
                                        plain_format=plain_format,
                                        loops=loops,
                                        status = status,
                                    )
                            if bool(is_new):
                                count_created = count_created + 1
                            elif bool(is_modified):
                                count_modified = count_modified + 1
                            if incomplete:
                                needs_another_loop = True
                            if partial_commit_number:
                                if idx % partial_commit_number == 0:
                                    transaction.commit()
                        except IgnoreLineException, e:
                            pass

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

                        except csvreplicataMissingFileInArchive, e:
                            errors.append("Error in line "+str(line) + ": %s" % (e))

                        except Exception, e:
                             errors.append("Error in line "+str(line) + \
                                           ": %s" % (e))
                            #raise Exception, "Error in csv file line "+str(line) + ": %s \n%s" % (e, row)
                else:
                    label_line = False
            # commit at the end of the loop if we want partial commits
            if partial_commit_number and (bool(needs_another_loop)==True):
                transaction.commit() 
            self.flag = needs_another_loop
            return (count_created, count_modified, export_date, errors)


    def importObject(self,
                     row,
                     specific_fields,
                     type,
                     conflict_winner,
                     export_date,
                     wf_transition,
                     zip,
                     encoding='utf-8',
                     ignore_content_errors=False,
                     plain_format=False,
                     loops = 0,
                     status = None,):
        """
        """
        modified = False
        is_new_object = False
        protected = True
        incomplete = False
        parent_path = row[0]
        id = row[1]
        type_class = row[2]
        if status is None:
            status = {}
        if parent_path == "":
            container = self.context
        else:
            try:
                container = self.context.unrestrictedTraverse(
                    parent_path)
            except:
                raise csvreplicataNonExistentContainer(
                    "Non existent container %s " % parent_path
                )

        # acquisition nightmare, just use base zope ids
        oids = container.objectIds()
        if not id in oids:
            # object does not exist, let's create it
            attool = getToolByName(self.context, 'archetype_tool')
            at = attool.lookupType(type[0], type[1])
            portal_type = at['portal_type']
            container.invokeFactory(portal_type, id=id)
            is_new_object = True
            protected = False

        obj = getattr(container.aq_explicit, id, None)
        opath = '/'.join(obj.getPhysicalPath())
        if not opath in status:
            status[opath] = {}

        if not is_new_object:
            # object exists, so check conflicts
            lastmodified = obj.modified()
            if lastmodified > export_date:
                if conflict_winner == "LOCAL":
                    protected = False
            else:
                protected = False

        # update object
        csvtool = getToolByName(
            self.context, "portal_csvreplicatatool")
        handlers = csvtool.getHandlers()
        # skip parent, id, title
        i = 3 - 1
        for f in specific_fields:
            i += 1
            if f is not None and f != "":
                field, type, h = None, None, None
                try:
                    fstatus = status[opath].get(f, False)
                    fcomplete = fstatus == 'complete'
                    fincomplete = fstatus == 'incomplete'
                    if fcomplete:
                        continue
                    field = obj.Schema().getField(f)
                    if field is None and ignore_content_errors:
                        if not plain_format:
                            logger.error('field %s is None'%f)
                        continue
                    type = field.getType()
                    h = handlers.get(type, handlers['default_handler'])
                    v = None
                    try:
                        v = row[i].decode(encoding)
                    except:
                        v = row[i].encode('utf-8').decode(encoding)
                    handler = h['handler_class']
                    # XXX:on plone25, 'allowDiscussion' is stored in a stringfield, force to be bool.
                    if f == 'allowDiscussion':
                        h = handlers.get('Products.Archetypes.Field.BooleanField')
                    handler = h['handler_class']
                    old_value = handler.get(obj, f, context=self)
                    if isinstance(old_value, basestring):
                        if not isinstance(old_value, unicode) and isinstance(v, unicode):
                            try:
                                old_value = old_value.decode('utf-8')
                            except:
                                pass
                    if old_value != v:
                        if protected and not fincomplete:
                            raise csvreplicataConflictException(
                                "Overlapping content modified "
                                "on the server after "
                                "exportation"
                            )
                        else:
                            if h['file']:
                                handler.set(obj, f, v, context=self, zip=zip, parent_path=parent_path)
                            else:
                                handler.set(obj, f, v, context=self)
                            if fincomplete:
                                logger.warn(
                                    '%s -> %s (%s) import '
                                    'is now complete' % (
                                        opath, f, v))
                            status[opath][f] = 'complete'
                            modified = True
                except Exception, e:
                    incomplete = True
                    status[opath][f] = 'incomplete'
                    if ignore_content_errors:
                        where = 'Path:\t%s\n\tTitle: %s\n' % (
                            '/'.join(obj.getPhysicalPath()),
                            obj.Title(),
                        )
                        what = ''
                        if field: what += '\tfield: %s\n' % field
                        if type:  what += '\ttype: %s\n' % type
                        handler = ''
                        if h:
                            hc = h.get('handler_class', None)
                            hfile = h.get('file', None)
                            if hc:
                                handler += '\thandler: %s\n' % hc.__class__
                            if hfile:
                                handler += '\thandlerfile: %s\n' % hfile

                        logger.warning(
                            'Oops:\n'
                            '%s'
                            '%s'
                            '%s'
                            '\tException: %s\n'
                            '\tMessage: %s\n' % (
                                where,
                                what,
                                handler,
                                e.__class__,
                                e
                            )
                        )
                    else:
                        raise


        # call events
        if is_new_object:
            event.notify(ObjectInitializedEvent(obj))
            obj.unmarkCreationFlag()
            obj.at_post_create_script()
            obj.indexObject()
            try:
                wftool = getToolByName(self.context, 'portal_workflow')
                wftool.doActionFor( obj, wf_transition)
            except Exception, e:
                pass
            is_new_object = obj
        elif modified:
            event.notify(ObjectEditedEvent(obj))
            obj.at_post_edit_script()
            obj.reindexObject()
            modified = obj

        # search plugins and apply them to our objects
        if len(row) > 3:
             plugins = list(getAdapters([self, obj], ICSVReplicataExportImportPlugin))
             for pluginid, plugin in plugins:
                 k = 'csvreplicataplugin_%s' % pluginid
                 pstatus = status[opath].get(k,  False)
                 pcomplete = 'complete' == pstatus
                 pincomplete = 'incomplete' == pstatus
                 if pcomplete:
                     continue
                 try:
                     status[opath][k] = False
                     plugin.set_values(row[3:], specific_fields)
                     if pincomplete:
                         logger.warn(
                             '%s -> %s plugin import '
                             'is now complete' % (
                                 opath, pluginid))

                     status[opath][k] = 'complete'
                 except Exception, e:
                     incomplete = True
                     status[opath][k] = 'incomplete'
                     where = 'Path:\t%s\n\tTitle: %s\n' % (
                         '/'.join(obj.getPhysicalPath()),
                         obj.Title(),
                     )
                     logger.warning(
                         'Plugin Oops:\n'
                         '%s\n'
                         '%s\n'
                         '%s\n' % (e, pluginid, where)
                     )
        return (is_new_object, modified, incomplete)

    def csvexport(self,
                  encoding = None,
                  delimiter = None,
                  stringdelimiter = None,
                  datetimeformat = None,
                  depth = 1,
                  wf_states = None,
                  zip = None,
                  vocabularyvalue = "No",
                  exportable_content_types = None,
                  stream = None,
                  plain_format=None,
                 ):
        """
        """
        if not stream: stream = cStringIO.StringIO()
        # read parameters
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        if encoding is None:
            encoding = csvtool.getEncoding()
        if delimiter is None:
            delimiter = csvtool.getDelimiter()
        if stringdelimiter is None:
            stringdelimiter = csvtool.getStringdelimiter()
        if datetimeformat is None:
            datetimeformat = csvtool.getDateTimeFormat()
            #datetimeformat = "%Y-%m-%d"
        self.datetimeformat = datetimeformat
        self.vocabularyvalue = vocabularyvalue

        if plain_format is None:
            plain_format = csvtool.getPlainFormat()


        # search objects
        #exportable_content_types = csvtool.getReplicableTypesSorted()
        catalog = self.context.portal_catalog
        portal = self.context.portal_url.getPortalObject()

        if exportable_content_types is not None:
            if self.context.Type() in ["Collection", "Smart Folder"]:
                all = self.context.queryCatalog(full_objects=True)
                exportable_objects = []
                for o in all:
                    if o.portal_type in exportable_content_types:
                        exportable_objects.append(o)
            else:
                query = {'portal_type': exportable_content_types}
                if depth == 0:
                    path = {'query':"/".join(self.context.getPhysicalPath()),
                            'level': -1}
                else:
                    path = {'query':"/".join(self.context.getPhysicalPath()),
                            'depth':depth}
                query['path'] = path

                if wf_states is not None:
                    query['review_state'] = wf_states
                search_exportable = list(catalog.searchResults(query))
                search_exportable.sort(custom_sort)
                exportable_objects = [o.getObject()
                                      for o in search_exportable]
        else:
            exportable_objects = []

        # search plugins for objects to add to the export list
        objects_searchers = getAdapters([self, self.context],
                              ICSVReplicataObjectsSearcher)
        # be sure not to export twice the same content.
        objects = []
        for oid, o_s in objects_searchers:
            # we do not need to filter on object meta types as plugins can export everything :)
            # the configurable list of objects is only available for AT based contents.
            noecho = [objects.append(o)
                      for o in o_s.getObjects()
                      if (
                          (not (o in exportable_objects))
                          and (not o in objects)
                      )
                      ]
        exportable_objects.extend(objects)
        csvstr = ''
        if plain_format:
            csvstr = self.export_plain(stream,
                                       delimiter, stringdelimiter, encoding,
                                       exportable_objects, zip=zip)
        else:
            csvstr = self.export_split(stream,
                                       delimiter, stringdelimiter, encoding,
                                       exportable_objects, zip=zip)
        return csvstr

    def export_plain(self,
                     stream,
                     delimiter,
                     stringdelimiter,
                     encoding,
                     exportable_objects,
                     zip=None):
        # export content
        types = []
        fields = ['startpoint', 'replicata_export_date',]
        startpoint = "/".join(self.context.getPhysicalPath()).encode(encoding)
        exportdate = DateTime().strftime(format='%Y%m%d%H%M%S').encode(encoding)
        labelsmapping = {}
        for index, obj in enumerate(exportable_objects):
            # search plugins that can add cells to our objects
            plugins = list(getAdapters([self, obj], ICSVReplicataExportImportPlugin))
            type_info = str(obj.getTypeInfo().id)
            if not type_info in types:
                # get type fields
                currentFieldsAndLabels = self.getTypeFields(type_info)
                for field, label in currentFieldsAndLabels:
                    fieldName = field.encode(encoding)
                    if not fieldName in fields:
                        fields.append(fieldName)
                    # handle utf-8 false-ascii encoded string
                    try:
                        label.encode(encoding)
                    except UnicodeDecodeError:
                        label.decode(encoding).encode(encoding)
                    labelsmapping[fieldName] = label
            # add cells given by plugins, must run once per object as each object
            # even on the same type can have fields like for annotations
            currentpluginfields = []
            for pluginid, plugin in plugins:
                plugin.append_ids(currentpluginfields)
            for pluginFieldName in currentpluginfields:
                if not pluginFieldName in fields:
                    fields.append(pluginFieldName)
                    labelsmapping[pluginFieldName] = pluginFieldName
        labelsmapping['startpoint'] = 'Start point'
        labelsmapping['replicata_export_date'] = 'Export Date'
        # initialize csv
        writer = csv.DictWriter(stream,
                                fields,
                                delimiter=delimiter,
                                quotechar=stringdelimiter,
                                extrasaction='ignore',
                                quoting=csv.QUOTE_NONNUMERIC)

        writer.writerow(dict([(f, f) for f in fields]))
        writer.writerow(labelsmapping)

        # export content

        for index, obj in enumerate(exportable_objects):
            if obj == self.context : continue
            # search plugins that can add cells to our objects
            plugins = list(
                getAdapters(
                    [self, obj], 
                    ICSVReplicataExportImportPlugin))
            type_info = str(obj.getTypeInfo().id)
            # get type fields
            currentFieldsAndLabels = self.getTypeFields(type_info)
            # reset fields row
            currentfields = [s[0].encode(encoding)
                             for s in currentFieldsAndLabels]
            # per object specific fields list
            current_specific_fields = currentfields[3:]
            # add cells given by plugins, must run once per object as each object
            # even on the same type can have fields like for annotations
            currentpluginfields = []
            for pluginid, plugin in plugins:
                plugin.append_ids(currentpluginfields)
            # initiate to blank all valuees currently given by plugins
            plugins_values = [None for i in range(len(currentpluginfields))]
            # fetch the possible objecvalues handled by plugins
            for pluginid, plugin in plugins:
                plugin.fill_values(plugins_values, currentpluginfields)
            values_row = self.getObjectValues(
                obj,
                current_specific_fields,
                zip) + plugins_values
            for i, value in enumerate(values_row[:]):
                if isinstance(value, basestring):
                    # byte but not utf-9 yet
                    if not isinstance(value, unicode):
                        values_row[i] = value.decode('utf-8')
                    # any way in anycase, back to ASCII encoded
                    values_row[i] = values_row[i].encode(encoding)
            cf = currentfields + currentpluginfields
            cf.insert(0, 'replicata_export_date')
            values_row.insert(0, exportdate)
            cf.insert(0, 'startpoint')
            values_row.insert(0, startpoint)
            row = dict([(field, values_row[cf.index(field)]) for field in cf])
            #current = "/".join(self.context.getPhysicalPath())
            #parent_path = "/".join(obj.getParentNode().getPhysicalPath())
            #parent_path = parent_path[len(current)+1:]
            #row["parent"] = parent_path
            writer.writerow(row)

        return stream

    def export_split(self,
                     stream,
                     delimiter,
                     stringdelimiter,
                     encoding,
                     exportable_objects,
                     zip=None):

        # initialize csv
        writer = csv.writer(stream,
                            delimiter=delimiter,
                            quotechar=stringdelimiter,
                            quoting=csv.QUOTE_NONNUMERIC)

        writer.writerow(["/".join\
                         (self.context.getPhysicalPath()).encode(encoding),
                         DateTime().strftime(format='%Y%m%d%H%M%S').\
                         encode(encoding)])

        # export content
        currentrows = []
        currenttype = None
        currentfields = []
        currentpluginfields = []
        currentlabels = []
        currentfieldsIndex = 0
        for index, obj in enumerate(exportable_objects):
            if obj == self.context : continue
            # search plugins that can add cells to our objects
            plugins = list(
                getAdapters([self, obj], 
                            ICSVReplicataExportImportPlugin))
            type_info = str(obj.getTypeInfo().id)
            if not(type_info == currenttype):
                currenttype = type_info
                # do no write to file the fist iteration step
                # goal is to flush to file per object type to minimize
                # RAM memory usage
                if index > 0:
                    fill_empty_fields_and_write_rows(
                        writer,
                        currentfields + currentpluginfields,
                        currentlabels + currentpluginfields,
                        currentrows
                    )
                    # be sure, reset!
                    currentfields, currentlabels, currentrows = [], [], []
                # get type fields
                currentFieldsAndLabels = self.getTypeFields(type_info)
                # reset fields row
                currentfields = [s[0].encode(encoding)
                                 for s in currentFieldsAndLabels]
                # reset labels row
                for s in currentFieldsAndLabels:
                    # handle utf-8 false-ascii encoded string
                    try:
                        currentlabels.append(s[1].encode(encoding))
                    except UnicodeDecodeError:
                        currentlabels.append(s[1].decode(encoding).encode(encoding))
                # per object specific fields list
                current_specific_fields = currentfields[3:]
                # reset current plugin handled fields
                currentpluginfields = []
            # add cells given by plugins, must run once per object as each object
            # even on the same type can have fields like for annotations
            for pluginid, plugin in plugins:
                plugin.append_ids(currentpluginfields)
            # initiate to blank all valuees currently given by plugins
            plugins_values = [None for i in range(len(currentpluginfields))]
            # fetch the possible objecvalues handled by plugins
            for pluginid, plugin in plugins:
                plugin.fill_values(plugins_values, currentpluginfields)
            values_row = self.getObjectValues(obj,
                                              current_specific_fields,
                                              zip) + plugins_values
            for i, value in enumerate(values_row[:]):
                if isinstance(value, basestring):
                    # byte but not utf-9 yet
                    if not isinstance(value, unicode):
                        values_row[i] = value.decode('utf-8')
                    # any way in anycase, back to ASCII encoded
                    values_row[i] = values_row[i].encode(encoding)
            currentrows.append(values_row)
        # last loop turn fields
        if len(currentrows):
            fill_empty_fields_and_write_rows(
                writer,
                currentfields + currentpluginfields,
                currentlabels + currentpluginfields,
                currentrows
            )
        return stream

    def getTypeFields(self, type):
        """
        """
        fields_and_labels = [('parent', 'Parent folder'),
                             ('id'    , 'Identifier'),
                             ('type'  , 'Content type')]
        types = {}
        try:
            attool = getToolByName(self.context, 
                                   'archetype_tool')
            types = getPortalTypes(self.context)
        except Exception, e:
            pass
        at = None
        # if its not an archetypes based object
        # we will rely on present plugins to export its specific fields
        try:
            at = attool.lookupType(types[type][0], types[type][1])
        except KeyError, e:
            return fields_and_labels
        # All right, archetypes, keep on workin'
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        if csvtool.replicabletypes.has_key(type):
            schematas = csvtool.replicabletypes[type]
        else:
            schematas = []
        notExportableFieldClasses = csvtool.getExcludedfieldsclasses()
        notExportableFields = csvtool.getNonExportableFields()
        at_class = at['klass']
        for schemata in schematas:
            fields = at_class.schema.getSchemataFields(schemata)
            #TODO: use getTranslationService to get the i18n translation
            fields_and_labels.extend(
                [(f.getName(), f.widget.label)
                 for f in fields
                 if f.__class__.__name__ not in notExportableFieldClasses
                 and f.getName() not in notExportableFields]
            )
        return fields_and_labels

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
        obj_id, type_info = None, None
        # deal with  specific none zope object
        try:
            type_info = obj.getTypeInfo().id
        except:
            pass
        try:
            obj_id = obj.id
        except:
            pass
        values = [parent_path, obj_id, type_info]
        csvtool = getToolByName(self.context, "portal_csvreplicatatool")
        handlers = csvtool.getHandlers()
        # add specific columns
        for f in specific_fields:
            otype = obj.Schema().getField(f).getType()
            h = handlers.get(otype, handlers['default_handler'])
            # XXX:on plone25, 'allowDiscussion' is stored in a stringfield, force to be bool.
            if f == 'allowDiscussion':
                h = handlers.get(
                    'Products.Archetypes.Field.BooleanField')
            handler = h['handler_class']
            if h['file']:
                v = handler.get(obj, f, context=self, zip=zip, parent_path=parent_path)
            else:
                v = handler.get(obj, f, context=self)
            values.append(v)
        return values


