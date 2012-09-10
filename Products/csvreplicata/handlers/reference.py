# -*- coding: utf-8 -*-
#
# File: reference.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
# GNU General Public License (GPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.org>"""
__docformat__ = 'plaintext'

from Products.csvreplicata import exceptions as exs
from Acquisition import aq_base
from base import CSVdefault
import os

import logging
logger = logging.getLogger('HANDLER')

from Products.CMFCore.utils import getToolByName

def get_path(context, path):
    p = getToolByName(context, 'portal_url')
    portal = p.getPortalObject()
    ppath = '/'.join(portal.getPhysicalPath())
    cpath = '/'.join(context.getPhysicalPath())
    qpath = path
    if not qpath.startswith(ppath+'/'):
        if qpath.startswith('/'):
            c = ppath
            qpath = qpath.strip('/')
        else:
            c = cpath
        qpath = os.path.join(c, qpath)
    target = None
    catalog = getToolByName(context, 'portal_catalog')
    res = catalog.search({'path':{'query': qpath,'depth':0}})
    if len(res):
        target = res[0].getObject()
    #try restrictedtraverse
    if not target:
        try:
            target = context.unrestrictedTraverse(qpath)
            # be sure not to have grabbed something
            # with acquisition not the the right place
        except Exception, e:
            pass
        orepr = repr(target).lower()
        if target is not None:
            if (('fspagetemplate' in orepr)
                or ('computedattribute' in orepr)
               ):
                target = None
    # if we have not found anything,
    # and if the path is absolute
    # try to find on a path relative to the new
    # plone site
    if target:
        targetpath = '/'.join(target.getPhysicalPath())
        if not targetpath.startswith(ppath+'/'):
            target = None 
    if (path.startswith('/') 
        and not target
        and not path.startswith(ppath+'/') 
        and path.count('/') > 1):
        parts = path.split('/')
        rparts = parts[2:]
        innerp = '/'+'/'.join(rparts)
        target = get_path(context, innerp) 
    return target

class CSVReference(CSVdefault):
    """
    """

    def get(self, obj, field, context=None):
        """
        """
        v = obj.Schema().getField(field).get(obj, aslist=True)
        if v is None:
            return ''
        else:
            current = "/".join(obj.getPhysicalPath())+"/"
            l = []
            for o in v:
                path = "/".join(o.getPhysicalPath())
                if path.startswith(current):
                    l.append(path[len(current):])
                else:
                    l.append(path)
            return '\n'.join(l)

    def set(self, obj, field, value, context=None):
        if value == '':
            ref = []
        else:
            value = value.split('\n')
            ref = []
            for path in value:
                if isinstance(path, unicode):
                    try:
                        path = path.encode('utf-8', 'ignore')
                    except Exception, e:
                        pass
                try:
                    target = get_path(obj, path)
                    if not target:
                        raise Exception('%s not found' % path)
                    ref.append(target)
                except Exception, e:
                    raise exs.csvreplicataBrokenReferenceException(
                        path + " cannot be found"
                    )
        self.store(field, obj, ref)




