# -*- coding: utf-8 -*-
#
# File: setuphandlers.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# Generator: ArchGenXML Version 2.0
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'


import logging
logger = logging.getLogger('csvreplicata: setuphandlers')
from Products.csvreplicata.config import PROJECTNAME
from Products.csvreplicata.config import DEPENDENCIES
import os
from Products.CMFCore.utils import getToolByName
import transaction
##code-section HEAD

import ConfigParser
from Products.csvreplicata.interfaces import ICSVReplicable, Icsvreplicata
from zope.interface import alsoProvides, noLongerProvides, directlyProvides

##/code-section HEAD

def isNotcsvreplicataProfile(context):
    return context.readDataFile("csvreplicata_marker.txt") is None

def setupHideToolsFromNavigation(context):
    """hide tools"""
    if isNotcsvreplicataProfile(context): return
    # uncatalog tools
    shortContext = context._profile_path.split(os.path.sep)[-3]
    if shortContext != 'csvreplicata': # avoid infinite recursions
        return
    site = context.getSite()
    toolnames = ['portal_csvreplicatatool']
    portalProperties = getToolByName(site, 'portal_properties')
    navtreeProperties = getattr(portalProperties, 'navtree_properties')
    if navtreeProperties.hasProperty('idsNotToList'):
        for toolname in toolnames:
            try:
                site[toolname].unindexObject()
            except:
                pass
            current = list(navtreeProperties.getProperty('idsNotToList') or [])
            if toolname not in current:
                current.append(toolname)
                kwargs = {'idsNotToList': current}
                navtreeProperties.manage_changeProperties(**kwargs)

def fixTools(context):
    """do post-processing on auto-installed tool instances"""
    if isNotcsvreplicataProfile(context): return
    site = context.getSite()

    tool_ids=['portal_csvreplicatatool']
    for tool_id in tool_ids:
        tool=site[tool_id]
        tool.initializeArchetype()



def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""
    if isNotcsvreplicataProfile(context): return
    shortContext = context._profile_path.split(os.path.sep)[-3]
    if shortContext != 'csvreplicata': # avoid infinite recursions
        return
    wft = getToolByName(context.getSite(), 'portal_workflow')
    wft.updateRoleMappings()

def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code
    if isNotcsvreplicataProfile(context): return
    shortContext = context._profile_path.split(os.path.sep)[-3]
    if shortContext != 'csvreplicata': # avoid infinite recursions
        return
    site = context.getSite()


def importcsvStep(context):
    """This step give you a way to import content in your website with
    csvreplicata.

    How it works:
       read replicata.cfg file to load configuration

       read replicata.csv and call csvreplicata with the config.

    Config:
        [replicable_types]
        #List schemata for each types you want to import
        #Folder : default, categorization, dates, ownership, settings
        #News Item : default

        Document: default

        [settings]
        #list here every csv settings that will be given to replicator.importcsv
        encoding:utf-8
        delimiter:,
        stringdelimiter:"
        datetimeformat:%d/%m/%Y
        wf_transition = publish
        conflict_winner:SERVER

    """
    if not 'openDataFile' in dir(context):
        return

    replicatacfg = context.openDataFile('replicata.cfg')
    replicatacsv = context.openDataFile('replicata.csv')
    replicatazip = context.openDataFile('replicata.zip')
    if replicatazip is None and replicatacsv is None:
        return
    site = context.getSite()
    wftool = getToolByName(site, 'portal_workflow')

    csvreplicatatool = getToolByName(site, 'portal_csvreplicatatool')
    # save existents user settings
    old_replicabletypes_settings = csvreplicatatool.replicabletypes

    #get import settings
    Config = ConfigParser.ConfigParser()
    #defaults system of configparser just sucks, so set values
    Config.add_section("replicable_types")
    Config.add_section("settings")
    Config.set("settings", "encoding","utf-8")
    Config.set("settings", "delimiter",";")
    Config.set("settings", "stringdelimiter",'"')
    Config.set("settings", "datetimeformat","%d/%m/%Y %H:%M:%S")
    Config.set("settings", "wf_transition", "publish")
    Config.set("settings", "conflict_winner","SERVER")
    Config.set("settings", "global_path","")
    Config.set("settings", "ignore_content_errors","false")
    Config.set("settings", "plain_format","true")
    if replicatacfg is not None:
        Config.read(replicatacfg.name)
    options = Config.items('replicable_types', raw=True)
    replicable_types = {}
    for option in options:
        replicable_types[option[0].title()] = option[1].split(',')
    if replicable_types:
        csvreplicatatool.replicabletypes = replicable_types
    else:
        csvreplicatatool.replicabletypes = old_replicabletypes_settings



    #build kwargs of csvimport method.
    kwargs = {}

    wf_transition = Config.get('settings', 'wf_transition')
    kwargs['wf_transition'] = wf_transition

    datetimeformat = Config.get('settings', 'datetimeformat')
    kwargs['datetimeformat'] = datetimeformat

    delimiter = Config.get('settings', 'delimiter')
    kwargs['delimiter'] = delimiter

    stringdelimiter = Config.get('settings', 'stringdelimiter')
    kwargs['stringdelimiter'] = stringdelimiter

    encoding = Config.get('settings', 'encoding')
    kwargs['encoding'] = encoding

    conflict_winner = Config.get('settings', 'conflict_winner')
    kwargs['conflict_winner'] = conflict_winner

    wf_transition = Config.get('settings', 'wf_transition')
    kwargs['wf_transition'] = wf_transition

    signore_content_errors = Config.get('settings', 'ignore_content_errors')
    ignore_content_errors = False
    if signore_content_errors:
        if signore_content_errors == 'true':
            ignore_content_errors = True
    kwargs['ignore_content_errors'] = ignore_content_errors

    plain_format = Config.get('settings', 'plain_format')

    kwargs['plain_format'] = False
    if plain_format == 'true':
        kwargs['plain_format'] = True

    if replicatazip:
        from zipfile import ZipFile
        kwargs['zip'] = ZipFile(replicatazip.name)

    #retrive context:
    global_path = Config.get('settings', 'global_path')
    try:
        folder = site.restrictedTraverse(global_path)
    except KeyError:
        logger.error('can t find global path')
        folder = site
    # now import
    alsoProvides(folder, ICSVReplicable)
    replicator = Icsvreplicata(folder)
    replicator.csvimport(replicatacsv, **kwargs)

    # restore replicabletypes user settings
    csvreplicatatool.replicabletypes = old_replicabletypes_settings

##code-section FOOT
##/code-section FOOT
