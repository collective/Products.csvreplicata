# -*- coding: utf-8 -*-
#
# File: csvreplicataTool.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# Generator: ArchGenXML Version 2.0
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from ZODB.PersistentMapping import PersistentMapping
from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from zope.interface import implements
import interfaces

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from Products.csvreplicata.config import *


from Products.CMFCore.utils import UniqueObject


##code-section module-header #fill in your manual code here
from Products.CMFCore.utils import getToolByName
import logging
logger = logging.getLogger('csvreplicataTool')
logger.info('csvreplicataTool')

from Products.csvreplicata import getPortalTypes

##/code-section module-header

schema = Schema(
    (
        StringField(
            name='encoding',
            default="UTF-8",
            widget=StringField._properties['widget'](
                label='Encoding',
                label_msgid='csvreplicata_label_encoding',
                i18n_domain='csvreplicata',
            ),
        ),
        StringField(
            name='delimiter',
            default=";",
            widget=StringField._properties['widget'](
                label='Delimiter',
                label_msgid='csvreplicata_label_delimiter',
                i18n_domain='csvreplicata',
            ),
        ),
        StringField(
            name='stringdelimiter',
            default='"',
            widget=StringField._properties['widget'](
                label='Stringdelimiter',
                label_msgid='csvreplicata_label_stringdelimiter',
                i18n_domain='csvreplicata',
            ),
        ),
        StringField(
            name='serverfilepath',
            default="",
            widget=StringField._properties['widget'](
                label='Server import folder',
                label_msgid='csvreplicata_label_serverfilepath',
                i18n_domain='csvreplicata',
            ),
        ),
        LinesField(
            name='excludedfields',
            default=['id', 
                     'locallyAllowedTypes', 
                     'constrainTypesMode',
                     'immediatelyAddableTypes'],
            widget=LinesField._properties['widget'](
                label='Excludedfields',
                label_msgid='csvreplicata_label_excludedfields',
                i18n_domain='csvreplicata',
            ),
        ),
        BooleanField(
            'plainFormat',
            default=False,
            widget=BooleanWidget(
                label='Plain format',
                label_msgid='csvreplicata_plain_format',
                i18n_domain='csvreplicata',
            ),
        ),
        StringField(
            name='DateTimeFormat',
            default='%d/%m/%Y %H:%M:%S',
            widget=StringField._properties['widget'](
                label='Excludedfieldsclasses',
                label_msgid='csvreplicata_label_DateTimeFormat',
                i18n_domain='csvreplicata',
            ),
        ),
        StringField(
            name='tempPath',
            default='',
            widget=StringField._properties['widget'](
                label='Temporary path',
                label_msgid='csvreplicata_label_tempPath',
                i18n_domain='csvreplicata',
            ),
        ),
        LinesField(
            name='excludedfieldsclasses',
            widget=LinesField._properties['widget'](
                label='Excludedfieldsclasses',
                label_msgid='csvreplicata_label_excludedfieldsclasses',
                i18n_domain='csvreplicata',
            ),
        ),
        IntegerField(
            name='partialCommitNumber',
            default='',
            widget=IntegerWidget(
                label='Partial Commit number',
                label_msgid='csvreplicata_label_patial_commit_number',
                i18n_domain='csvreplicata',
            ),
        ),
    ),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

csvreplicataTool_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
##/code-section after-schema

class csvreplicataTool(UniqueObject, BaseContent, BrowserDefaultMixin):
    """
    """
    security = ClassSecurityInfo()
    implements(interfaces.IcsvreplicataTool)

    meta_type = 'csvreplicataTool'
    _at_rename_after_creation = True

    schema = csvreplicataTool_schema

    handlers = PersistentMapping

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header




    # tool-constructors have no id argument, the id is fixed
    def __init__(self, id=None):
        BaseContent.__init__(self,'portal_csvreplicatatool')
        self.setTitle('')

        ##code-section constructor-footer #fill in your manual code here
        self.setTitle('CSV Replicator tool')
        self.replicabletypes = PersistentMapping()
        self.handlers = {}
        ##/code-section constructor-footer

    @property
    def dreplicabletypes(self):
        return dict(self.replicabletypes)


    def manage_afterAdd(self, item, container):
        """ initialize handlers with appconfig HANDLERS values"""
        self.handlers = HANDLERS

    # tool should not appear in portal_catalog
    def at_post_edit_script(self):
        self.unindexObject()

        ##code-section post-edit-method-footer #fill in your manual code here
        ##/code-section post-edit-method-footer


    # Methods

    # Manually created methods

    def setCSVsettings(self, REQUEST):
        """
        """
        self.setEncoding(REQUEST.get('encoding'));
        self.setDelimiter(REQUEST.get('delimiter'));
        self.setServerfilepath(REQUEST.get('serverfilepath'));
        self.setDateTimeFormat(REQUEST.get('datetimeformat'));
        self.setTempPath(REQUEST.get('tempPath'))
        self.setPlainFormat(REQUEST.get('is_plain_format', '') == 'on')
        partial_commit_number = REQUEST.get('partial_commit_number', '')
        if partial_commit_number:
            partial_commit_number = int(partial_commit_number)
        self.setPartialCommitNumber(partial_commit_number)
        # Redirection of the page now that the treatment is done
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/csv_settings')

    def setCSVHandledTypes(self, REQUEST):
        """
        """
        types_tool = getToolByName(self, 'archetype_tool')

        # Get of the various replicabletypes current and new)
        newreplicabletypes = REQUEST.get('csvhandledtypes')
        if (not type(newreplicabletypes) is list):
            newreplicabletypes = [newreplicabletypes]
        currentreplicablestypes = self.replicabletypes

        # Addition of the new replicable types, by default a new empty list
        # and creation of a temp variable to hold the new csv handled types
        newreplicabletypestempdict = {}
        for t in newreplicabletypes :
            newreplicabletypestempdict[t] = []
            if (not currentreplicablestypes.has_key(t)):
                    currentreplicablestypes[t] = ['default', ]

        # removal of the types that are not anymore replicables
        for k, v in currentreplicablestypes.items():
            if (not newreplicabletypestempdict.has_key(k)):
                del currentreplicablestypes[k]

        # save of the new values
        self.replicabletypes.update(currentreplicablestypes)

        # Redirection of the page now that the treatment is done
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/csv_settings')

    def setExcludedFields(self, REQUEST):
        """
        """
        self.setExcludedfieldsclasses(
            REQUEST.get('excludedfieldsclasses').split('\n'));
        self.setExcludedfields(REQUEST.get('excludedfields').split('\n'));

        # Redirection of the page now that the treatment is done
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/csv_settings')

    def getPortalTypeNames(self):
        """
        """
        l = getPortalTypes(self).keys()
        l.sort()
        return [(k, k) for k in l]

    def getReplicableTypesSorted(self):
        """
        """
        l = self.replicabletypes.keys()
        l.sort()
        return l

    def getTypeSchematas(self, type):
        """
        """
        attool = getToolByName(self, 'archetype_tool')
        pt = getPortalTypes(self)
        if pt.has_key(type):
            (package, name) = pt[type]
            t = attool.lookupType(package, name)
            return  t['klass'].schema.getSchemataNames()
        else:
            return []

    def setCSVHandledTypesSchematas(self, REQUEST):
        """
        """
        currentreplicablestypes = self.replicabletypes

        i = 0
        for ptn in self.getReplicableTypesSorted():
            i += 1
            if (type(ptn) is tuple):
                t = ptn[0]
            else:
                t = ptn

            r = REQUEST.get('csvhandledschematas-'+str(i))
            if r:
                if (not type(r) is list):
                    r = [r]
                currentreplicablestypes[t] = r
            else :
                if currentreplicablestypes.has_key(t):
                    del currentreplicablestypes[t]

        self.replicabletypes.update(currentreplicablestypes)

        # Redirection of the page now that the treatment is done
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/csv_settings')

    def clearReplicableTypes(self):
        """
        """
        self.replicabletypes.clear()

    def printReplicableTypes(self):
        """
        """
        return self.replicabletypes

    def getHandlers(self):
        """
        """
        if not getattr(self, 'handlers', None):
            setattr(self, 'handlers', {})
        # migrate persistent mapping with possible new values
        for h in HANDLERS:
            if not h in self.handlers:
                self.handlers[h] = HANDLERS[h]
        return self.handlers

    def setHandler(self, key, value):
        """
        """
        self.handlers[key] = value

    def delHandler(self, key):
        """
        """
        del(self.handlers[key])

    def getNonExportableFields(self):
        return (self.getExcludedfields() 
                + ('tableContents',))

    def fullactivation(self):
        types = getPortalTypes(self)
        self.replicabletypes.update(
            dict(
                [(t, self.getTypeSchematas(t)) 
                 for t in types])
        )



registerType(csvreplicataTool, PROJECTNAME)
# end of class csvreplicataTool

##code-section module-footer #fill in your manual code here
##/code-section module-footer



