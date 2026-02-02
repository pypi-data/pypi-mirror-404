from datapackage_pipelines.wrapper import ingest, spew
from datapackage_pipelines_ckan.processors.add_ckan_resource import AddCkanResource
from datapackage_pipelines_ckanext import helpers as ckanext_helpers
from functools import lru_cache
from os import environ


@lru_cache()
def get_config(key):
    return ckanext_helpers.get_plugin_configuration('upload_via_email').get(key)


class AddCkanAllowedSendersResource(AddCkanResource):

    def get_parameters(self, parameters):
        parameters['resource-id'] = get_config('allowed_senders_resource_id')
        super(AddCkanAllowedSendersResource, self).get_parameters(parameters)

    def update_ckan_resource(self, resource):
        super(AddCkanAllowedSendersResource, self).update_ckan_resource(resource)
        resource.update(http_headers={'Authorization': environ['CKAN_API_KEY']},
                        name='allowed-senders', path='allowed-senders.csv')

    def __call__(self, *args, **kwargs):
        parameters, datapackage, res_iter = ingest()
        self.get_parameters(parameters)
        if self.resource_id:
            resource_show_url = self.get_resource_show_url()
            resource = self.get_ckan_resource(resource_show_url)
            self.update_ckan_resource(resource)
            datapackage['resources'].append(resource)
        spew(datapackage, res_iter)

if __name__ == '__main__':
    AddCkanAllowedSendersResource()()
