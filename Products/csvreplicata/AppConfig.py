from handlers import base
from handlers import reference
from handlers import file
from handlers import maps

import logging
logger = logging.getLogger('CONFIG')

# settings default archetypes widgets fields
HANDLERS = {
    'default_handler': { 'handler_class' : base.CSVdefault(), 'file' : False },
    'Products.Archetypes.Field.StringField': {'handler_class' : base.CSVString(), 'file' : False},
    'Products.Archetypes.Field.IntegerField': {'handler_class' : base.CSVInteger(), 'file' : False},
    'Products.Archetypes.Field.FloatField': {'handler_class' : base.CSVFloat(), 'file' : False},
    'Products.Archetypes.Field.BooleanField': {'handler_class' : base.CSVBoolean(), 'file' : False},
    'Products.Archetypes.Field.LinesField': {'handler_class' : base.CSVLines(), 'file' : False},
    'Products.Archetypes.Field.TextField': {'handler_class' : base.CSVText(), 'file' : False},
    'Products.Archetypes.Field.DateTimeField': {'handler_class' : base.CSVDateTime(), 'file' : False},
    'Products.Archetypes.Field.ReferenceField': {'handler_class' : reference.CSVReference(), 'file' : False},
    'Products.Archetypes.Field.FileField': {'handler_class' : file.CSVFile(), 'file' : True},
    'Products.Archetypes.Field.ImageField': {'handler_class' : file.CSVFile(), 'file' : True},
    'plone.app.blob.subtypes.image.ExtensionBlobField': { 'handler_class' : file.CSVFile(), 'file' : True },
    'plone.app.blob.subtypes.file.ExtensionBlobField': {'handler_class' : file.CSVFile(), 'file' : True},
    'plone.app.blob.subtypes.blob.ExtensionBlobField': {'handler_class' : file.CSVFile(), 'file' : True},
    'Products.AttachmentField.AttachmentField.AttachmentField': {'handler_class' : file.CSVFile(), 'file' : True},
    'Products.Maps.field.LocationField': {'handler_class' : maps.CSVMap(), 'file' : False},
    'Products.ATBackRef.BackReferenceField':  {'handler_class' : reference.CSVReference(), 'file' : False},
}

