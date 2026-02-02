import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.datapackage_pipelines.interfaces import IDatapackagePipelines
import os


class Upload_Via_EmailPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(IDatapackagePipelines)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'upload_via_email')

    def register_pipelines(self):
        return 'ckanext-upload_via_email', os.path.join(os.path.dirname(__file__), 'pipelines')

    def get_pipelines_config(self):
        return {'gmail_token': toolkit.config.get('ckanext.upload_via_email.gmail_token'),
                'allowed_senders_resource_id': toolkit.config.get('ckanext.upload_via_email.allowed_senders_resource_id'),
                'default_sender_to_address': toolkit.config.get('ckanext.upload_via_email.default_sender_to_address'),
                'default_sender_organization_id': toolkit.config.get('ckanext.upload_via_email.default_sender_organization_id'),
                'success_message': toolkit.config.get('ckanext.upload_via_email.success_message'),
                'success_message_from_email': toolkit.config.get('ckanext.upload_via_email.success_message_from_email'),
                'success_message_subject': toolkit.config.get('ckanext.upload_via_email.success_message_subject'),}
