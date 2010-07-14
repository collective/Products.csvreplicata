from Products.csvreplicata import adapters
from Products.CMFCore.utils import getToolByName

class WorkflowExportImporter(adapters.CSVReplicataExportImportPluginAbstract):

    def __init__(self, replicator, context):
        adapters.CSVReplicataPluginAbstract.__init__(self, replicator, context)
        self.ids = ['wf_state']
        self._datetimeformat = None

    def append_ids(self, row_ids):
        """."""
        row_ids.extend(
            ['%s%s' % (self.prefix, i)
             for i in self.ids 
             if not i in row_ids]
        )

    def fill_values(self, row, row_ids):
        """."""
        wf_tool = getToolByName(self.context, 'portal_workflow')
        chain = wf_tool.getWorkflowsFor(self.context)
        if len(chain)>0:
           st = wf_tool.getStatusOf(chain[0].id, self.context)
           row[0] = st['review_state']

    def set_values(self, row, row_ids):
        """."""
        raise Exception('Not implemented.', prefix='')
