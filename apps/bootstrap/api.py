from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.contrib.auth.models import User, Group

from permissions.models import Role
from history.models import History
from django_gpg.runtime import gpg
from documents.models import DocumentType, DocumentTypeFilename, Document
from folders.models import Folder
from taggit.models import Tag
from tags.models import TagProperties
from metadata.models import MetadataType, MetadataSet
from sources.models import WebForm, StagingFolder
from document_indexing.models import Index, IndexTemplateNode
from dynamic_search.models import RecentSearch
# TODO: clear the job queues

bootstrap_options = {}


def nuke_database():
    # Delete all document types
    for obj in DocumentType.objects.all():
        obj.delete()

    # Delete all documents one by one to trigger the document file delete method
    # Should also get rid of document metadata
    for obj in Document.objects.all():
        obj.delete()

    # Delete all metadata types
    for obj in MetadataType.objects.all():
        obj.delete()

    # Delete all metadata sets
    for obj in MetadataSet.objects.all():
        obj.delete()

    # Delete all indexes types, should also delete index nodes
    for obj in Index.objects.all():
        obj.delete()

    # Delete all webforms sources
    for obj in WebForm.objects.all():
        obj.delete()

    # Delete all staging folder sources
    for obj in StagingFolder.objects.all():
        obj.delete()

    # Delete all user groups
    for obj in Group.objects.all():
        obj.delete()

    # Delete all users except superadmins and staff
    for obj in User.objects.all():
        if not obj.is_superuser and not obj.is_staff:
            obj.delete()

    # Delete all user roles
    for obj in Role.objects.all():
        obj.delete()

    # Delete all the remaining history events
    for obj in History.objects.all():
        obj.delete()

    # Delete all tags
    for obj in Tag.objects.all():
        obj.delete()

    # Delete any remaining tag property
    for obj in TagProperties.objects.all():
        obj.delete()

    # Delete all foders
    for obj in Folder.objects.all():
        obj.delete()

    # Delete all recent searches
    for obj in RecentSearch.objects.all():
        obj.delete()

    # Clear the entire key ring (public and private keys)
    gpg.delete_all_keys()


class BootstrapBase(object):
    name = None
    label = ''
    description = ''

    def __unicode__(self):
        return unicode(self.label)


class BootstrapSimple(BootstrapBase):
    name = 'simple'
    label = _(u'Simple')
    description = _(u'A simple setup providing an uploaded date metadata and index plus an alphabetic index based on document filenames.')

    def execute(self):
        # Create metadata types
        upload_date = MetadataType.objects.create(name='upload_date', title=ugettext(u'Upload date'), default='current_date()')

        # Create a segmented date index
        index = Index.objects.create(name='date_tree', title=ugettext(u'Segmented date index'), enabled=True)
        template_root = index.template_root

        # Create index template
        node1 = IndexTemplateNode.objects.create(parent=template_root, index=index, expression='metadata.upload_date[0:4]', enabled=True, link_documents=False)
        node2 = IndexTemplateNode.objects.create(parent=node1, index=index, expression='metadata.upload_date[5:7]', enabled=True, link_documents=False)
        node3 = IndexTemplateNode.objects.create(parent=node2, index=index, expression='metadata.upload_date[8:10]', enabled=True, link_documents=True)


class BootstrapPermit(BootstrapBase):
    name = 'permits'
    label = _(u'Permits')
    description = _(u'A setup for handling permits and related documents.')

    def execute(self):
        # Create document types
        form = DocumentType.objects.create(name=ugettext(u'Form'))
        DocumentTypeFilename.objects.create(document_type=form, filename=ugettext(u'Building construction form'))
        DocumentTypeFilename.objects.create(document_type=form, filename=ugettext(u'Building usage form'))

        blueprint = DocumentType.objects.create(name=ugettext(u'Blueprint'))
        DocumentTypeFilename.objects.create(document_type=blueprint, filename=ugettext(u'Floorplan'))
        DocumentTypeFilename.objects.create(document_type=blueprint, filename=ugettext(u'Plot plan'))

        # Create metadata types
        date = MetadataType.objects.create(name='date', title=ugettext(u'Date'), default='current_date()')
        client = MetadataType.objects.create(name='client', title=ugettext(u'Client'))
        permit = MetadataType.objects.create(name='permit', title=ugettext(u'Permit number'))
        project = MetadataType.objects.create(name='project', title=ugettext(u'Project'))
        user = MetadataType.objects.create(name='user', title=ugettext(u'User'), lookup='sorted([user.get_full_name() or user for user in User.objects.all() if user.is_active])')

        # Create a segmented date index
        index = Index.objects.create(name='main_index', title=ugettext(u'Permit index'), enabled=True)

        # Create index template
        per_permit = IndexTemplateNode.objects.create(parent=index.template_root, index=index, expression='\'%s\'' % ugettext(u'Per permit'), enabled=True, link_documents=False)
        per_permit_child = IndexTemplateNode.objects.create(parent=per_permit, index=index, expression='metadata.permit', enabled=True, link_documents=True)

        per_project = IndexTemplateNode.objects.create(parent=index.template_root, index=index, expression='\'%s\'' % ugettext(u'Per project'), enabled=True, link_documents=False)
        per_project_child = IndexTemplateNode.objects.create(parent=per_project, index=index, expression='metadata.project', enabled=True, link_documents=False)
        per_permit = IndexTemplateNode.objects.create(parent=per_project_child, index=index, expression='\'%s\'' % ugettext(u'Per permit'), enabled=True, link_documents=False)
        per_permit_child = IndexTemplateNode.objects.create(parent=per_permit, index=index, expression='metadata.permit', enabled=True, link_documents=True)

        per_date = IndexTemplateNode.objects.create(parent=index.template_root, index=index, expression='\'%s\'' % ugettext(u'Per date'), enabled=True, link_documents=False)
        per_date_child = IndexTemplateNode.objects.create(parent=per_date, index=index, expression='metadata.date', enabled=True, link_documents=True)

        per_user = IndexTemplateNode.objects.create(parent=index.template_root, index=index, expression='\'%s\'' % ugettext(u'Per user'), enabled=True, link_documents=False)
        per_user_child = IndexTemplateNode.objects.create(parent=per_user, index=index, expression='metadata.user', enabled=True, link_documents=True)

        per_client = IndexTemplateNode.objects.create(parent=index.template_root, index=index, expression='\'%s\'' % ugettext(u'Per client'), enabled=True, link_documents=False)
        per_client_child = IndexTemplateNode.objects.create(parent=per_client, index=index, expression='metadata.client', enabled=True, link_documents=True)


for bootstrap in [BootstrapSimple(), BootstrapPermit()]:
    bootstrap_options[bootstrap.name] = bootstrap
