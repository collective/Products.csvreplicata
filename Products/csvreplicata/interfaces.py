# -*- coding: utf-8 -*-

from zope.interface import Interface, Attribute

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


class ICSVFile(Interface):
    """CSV File.

    A CSV File defaut Interface
    """

    def get(obj, field, context=None, zip=None):
        """A getter."""

    def set(obj, field, value, context=None, zip=None):
        """ A setter."""


class IcsvreplicataTool(Interface):
    """Marker interface for .csvreplicataTool.csvreplicataTool
    """


class ICSVReplicable(Interface):
    """Marker interface for replicable folders
    """

class Icsvreplicata(Interface):
    """ adapter interface
    """

class  ICSVReplicataObjectsSearcher(Interface):
    """You have some others infos in adapters.py. """
    prefix = Attribute('preifx to use as title')

    """Search for aditionnal objects 
    to export which are not catalogued in
    the main catalog"""

    def getObjects():
        """ Get a list of objects to export"""

class  ICSVReplicataExportImportPlugin(Interface):
    """You have some others infos in adapters.py"""

    """Export aditionnal fields/values pairs  
    which are not handled via archetypes handlers"""

    """Be sure to prefix your titles and not have conflicting titles 
    (Otherwise normally, first win)"""

    """ PLEASE INIT THIS IN THE __init__ OF YOUR PLUGIN, you may have better to inherit the mixin class in .adapters to init thems """
    ids = Attribute('ordonned list of csv ids')
    prefix = Attribute('prefix to use as title in csv, it must begin with "ReplicataPlugin_"')

    def append_ids(row_ids):
        """Add the plugins ids to a list of ids tuple."""

    def fill_values(row, row_ids):
        """
        Fill contextual value in a row matching the given fields
        row: a row (list of cells) 
        As list arguments are references in python, the plugin will just
        need to  modiffy it and the caller will get the list updated as well.
        No need to return it.
        row_ids: The current list of fields matching the row.
        For example:
            a.csv has rows with a,b,c,d
            c and d are columns given by MySuperPlugin
        An appropriate call can call will be:
            current_row = [1, 2, None, None]
            MySuperPluginInstance.fill_values(
                    current_row, ['a', 'b', 'c', 'd']
            )

        You will note that the row has been initialized with empty values
        for the plugin handled columns. Indeed, the plugin is not supposed
        to handle values initialization, it just fill/update them.
        """

    def set_values(row, row_ids):
        """Set contextual value in a row matching the previous ids order.."""

# BBB: compatibility
ICSVReplicataExportPlugin = ICSVReplicataExportImportPlugin
