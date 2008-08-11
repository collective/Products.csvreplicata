# -*- coding: utf-8 -*-

from zope.interface import Interface

##code-section HEAD
##/code-section HEAD

class IcsvreplicataTool(Interface):
    """Marker interface for .csvreplicataTool.csvreplicataTool
    """

##code-section FOOT
class ICSVReplicable(Interface):
    """Marker interface for replicable folders
    """
    
class Icsvreplicata(Interface):
    """ adapter interface
    """

##/code-section FOOT