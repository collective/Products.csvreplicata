from Products.csvreplicata import adapters
from DateTime.DateTime import DateTime
from Products.CMFCore.utils import getToolByName

class WorkflowExportImporter(adapters.CSVReplicataExportImportPluginAbstract):

    def __init__(self, replicator, context):
        adapters.CSVReplicataPluginAbstract.__init__(self, replicator, context)
        self.ids = ['wf_chain', 'wf_state',]
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
        chains = wf_tool.getWorkflowsFor(self.context)
        if len(chains)>0:
           chain = chains[0]
           st = wf_tool.getStatusOf(chain.id, self.context)
           row[1] = st['review_state']
           row[0] = chain.id

    def set_value(self, id, value, row, row_ids):
        """."""
        if id == 'wf_chain':
            state = row[row_ids.index(self.compute_id('wf_state'))]
            wf_tool = getToolByName(self.context, 'portal_workflow')
            wchain = wf_tool.get(value, None)
            if wchain:
                chains = wf_tool.getWorkflowsFor(self.context)
                if len(chains)>0:
                    st = wf_tool.getStatusOf(chains[0].id, self.context)
                    rst = st['review_state']
                    if rst != state and (wchain in chains):
                        wf_tool.setStatusOf(
                            wchain.id,
                            self.context,
                            {'action': None, 
                            'review_state': state,
                            'comments': 'State setted by csvreplicata', 
                            'actor': 'admin', 
                            'time': DateTime(),
                            }
                        )
                        wchain.updateRoleMappingsFor(self.context)
                        self.context.reindexObject()
