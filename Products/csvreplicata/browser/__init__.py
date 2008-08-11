#
from Products.csvreplicata.interfaces import ICSVReplicable

class isCSVReplicable(object):
    
    def __call__(self):
        return ICSVReplicable.providedBy(self.context)