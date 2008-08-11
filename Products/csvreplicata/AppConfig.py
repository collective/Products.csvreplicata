from handlers import base
from handlers import reference
from handlers import file

import logging
logger = logging.getLogger('CONFIG')
HANDLERS={'Products.Archetypes.Field.StringField': {'handler_class' : base.CSVString(), 'file' : False},
          'Products.Archetypes.Field.IntegerField': {'handler_class' : base.CSVInteger(), 'file' : False},
          'Products.Archetypes.Field.FloatField': {'handler_class' : base.CSVFloat(), 'file' : False},
          'Products.Archetypes.Field.BooleanField': {'handler_class' : base.CSVBoolean(), 'file' : False},
          'Products.Archetypes.Field.LinesField': {'handler_class' : base.CSVLines(), 'file' : False},
          'Products.Archetypes.Field.TextField': {'handler_class' : base.CSVText(), 'file' : False},
          'Products.Archetypes.Field.DateTimeField': {'handler_class' : base.CSVDateTime(), 'file' : False},
          'Products.Archetypes.Field.ReferenceField': {'handler_class' : reference.CSVReference(), 'file' : False},
          'Products.Archetypes.Field.FileField': {'handler_class' : file.CSVFile(), 'file' : True},
          'plone.app.blob.subtypes.file.ExtensionBlobField': {'handler_class' : file.CSVFile(), 'file' : True},
          }

default_handler = {'handler_class' : base.CSVdefault(), 'file' : False}

def getHandlers():
    """
    """
    # Load custom handlers
    try:
        from handlers.custom.CustomHandlers import *
    except ImportError:
        CUSTOMHANDLERS={}
    all_h=HANDLERS
    for h in CUSTOMHANDLERS.keys():
        all_h[h]=CUSTOMHANDLERS[h]
    return all_h
