from cStringIO import StringIO
from Products.CMFCore.utils import getToolByName

def removeConfiglets(self, out):
    configTool = getToolByName(self, 'portal_controlpanel', None)
    if configTool:
        out.write('Removing configlet %s\n' % 'CSV_replicata')
        configTool.unregisterConfiglet('CSV_replicata')

def uninstall(self):
    out = StringIO()
    removeConfiglets(self,out)
