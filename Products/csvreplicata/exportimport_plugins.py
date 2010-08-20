import logging
from Products.csvreplicata import adapters
from DateTime.DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.csvreplicata.adapters import CSVReplicataObjectSearcherAbstract

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
        i = -1
        for i, cid in enumerate(row_ids):
            id = self.computedid_to_id(cid)
            if id == 'wf_chain':
                break
        if len(chains)>0:
           chain = chains[0]
           st = wf_tool.getStatusOf(chain.id, self.context)
           row[i+1] = st['review_state']
           row[i+0] = chain.id

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


#
# TO EXPORT COMMENTS.
# - Mark your plone site ICSVReplicable
# - As always, configure the tool as you wish in the back office
# - Goto http://yoursiterootURL/@@csvreplicata
# - export as you want, you can even uncheck all types in the object list,
#   comments will be exported anyway
#


class CommentsObjectsSearcher(adapters.CSVReplicataObjectSearcherAbstract):

    def getObjects(self):
        logger = logging.getLogger('Products.csvreplicata.adapters.CommentsObjectsSearcher')
        objs = []
        c = getToolByName(self.context, 'portal_catalog')
        bcomments = c.searchResults(**{
            'meta_type': ['Discussion Item'],
            'sort_on': 'in_reply_to',
        })
        lbcomments = len(bcomments)
        logger.info('%s comments to export' % lbcomments)
        SLICE = 1000
        for i in range((lbcomments / SLICE) + 1):
            lowerBound = SLICE * i
            upperBound = SLICE * (i+1)
            if upperBound > lbcomments:
                upperBound = lbcomments
            logger.info('Loading %s to %s comments.' % (lowerBound, upperBound))
            #lowerBound, upperBound = 0, 3
            scomments = [b.getObject()
                         for b in bcomments[lowerBound : upperBound]]
            objs.extend(scomments)
        logger.info('All comments loaded.')
        return objs

class CommentsExportImporter(adapters.CSVReplicataExportImportPluginAbstract):
    """."""
    prefix = 'CommentExporter_'
    def __init__(self, *args, **kwargs):
        logger = logging.getLogger('Products.csvreplicata.adapters.CommentsImporter')
        adapters.CSVReplicataExportImportPluginAbstract.__init__(self, *args, **kwargs)
        self.comment = None
        self.comment_as_dict = None
        if self.context.meta_type in ['Discussion Item']:
            try:
                self.comment = {}
                self.comment['creators']          = self.context.listCreators()
                self.comment['contributors']      = self.context.contributors
                self.comment['description']       = self.context.description
                self.comment['effective_date']    = self.context.effective_date
                self.comment['expiration_date']   = self.context.expiration_date
                self.comment['id']                = self.context.id
                self.comment['in_reply_to']       = self.context.in_reply_to
                self.comment['modification_date'] = self.context.modification_date
                self.comment['subject']           = self.context.subject
                self.comment['text']              = self.context.text
                self.comment['text_format']       = self.context.text_format
                self.comment['title']             = self.context.title
                self.comment['cooked_text']       = self.context.cooked_text
                self.comment['language']          = self.context.language
                self.comment['path']              = '/'.join(self.context.getPhysicalPath())
                self.comment['in_reply_to']       = '/'.join(self.context.inReplyTo().getPhysicalPath())
                self.comment['in_reply_to_chain'] = ['/'.join(obj.getPhysicalPath())
                                                     for obj in self.context.parentsInThread()]
                ks = self.comment.keys()
                ks.sort()
                self.ids = ks
            except Exception, e:
                logger.info('Error while setting comment info')

    def fill_values(self, row, row_ids):
        """."""
        for i, cid in enumerate(row_ids):
            id = self.computedid_to_id(cid)
            if id in self.ids:
                row[i] = self.comment[id]

    def set_values(self, row, row_ids):
        """."""
        logger = logging.getLogger('Products.csvreplicata.adapters.CommentsImporter')
        if not getattr(self, 'csvlog', True):
            self.csvlog = True
            logger.info('Import comments not implemented')

