#
from Products.csvreplicata.interfaces import ICSVReplicable
from Products.csvreplicata import config
from Products.Five import BrowserView

class isCSVReplicable(object):

    def __call__(self):
        return ICSVReplicable.providedBy(self.context)

class isCSVRPlone25(BrowserView):

    def __call__(self):
        return config.PLONE25

class p25wrapper_is_locked_for_current_user(BrowserView):
    """."""

    def __call__(self, *args, **kwargs):
        """."""
        if config.PLONE25:
            return False
        else:
            return self.context.restrictedTraverse(
                '@@plone_lock_info'
            ).is_locked_for_current_user() 
