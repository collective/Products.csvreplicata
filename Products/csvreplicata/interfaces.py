# -*- coding: utf-8 -*-

from zope.interface import Interface


class ICSVDefault(Interface):
    """CSV Default.
    
    A CSV Field defaut Interface
    """
    
    def get(obj, field, context=None):
        """A getter."""
    
    def set(obj, field, value, context=None):
        """ A setter."""
    
    def store(field, obj, value):
        """Store field value."""



class IcsvreplicataTool(Interface):
    """Marker interface for .csvreplicataTool.csvreplicataTool
    """


class ICSVReplicable(Interface):
    """Marker interface for replicable folders
    """
    
class Icsvreplicata(Interface):
    """ adapter interface
    """
