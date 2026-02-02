from dataflows import Flow, PackageWrapper, add_metadata, DataStreamProcessor, DataStream
from datapackage_pipelines_ckanext import helpers as ckanext_helpers
from datapackage import Package
from os import path
import logging
import json
import uuid
from os import rename
from collections import defaultdict


class DatasetsPackageDataStreamProcessor(DataStreamProcessor):

    def __init__(self, resources, datapackage, source_stats):
        config = ckanext_helpers.get_plugin_configuration('upload_via_email')
        self.data_path = config['data_path']
        self.resources = resources
        self.datapackage = datapackage
        self.source_stats = source_stats

    def process_messages(self, resource):
        stats = defaultdict(int)
        output_resources = []
        messages_datasets = []
        for i, row in enumerate(resource):
            dataset_name = str(uuid.uuid4())
            org_id = row['organization_id']
            dataset_resources = []
            for part_id in row['part_ids']:
                with open(path.join(self.data_path, 'attachments', row['id'], 'part{}.json'.format(part_id))) as f:
                    part = json.load(f)
                part_body_filename = path.join(self.data_path, 'attachments', row['id'], 'part{}.body'.format(part_id))
                if part.get('filename'):
                    if path.exists(part_body_filename):
                        output_filename = path.join(self.data_path, 'attachments', row['id'], part['filename'])
                        rename(part_body_filename, output_filename)
                        dataset_resources.append({'name': '{}-{}'.format(dataset_name, part_id),
                                                  'dataset-name': dataset_name,
                                                  'dataset-resource-name': part['filename'],
                                                  "dpp:streamedFrom": output_filename,
                                                  "data": []})
                    else:
                        logging.error('missing filename: {}'.format(part_body_filename))
            if len(dataset_resources) > 0:
                messages_datasets.append({'message_id': row['id'], 'dataset_name': dataset_name})
                output_resources.append({'name': dataset_name,
                                         "data": [],
                                         'dataset-properties': {'name': dataset_name,
                                                                'owner_org': org_id,
                                                                'title': row['subject']}})
                output_resources += dataset_resources
                stats['get_datasets: messages with valid resources'] += 1
            else:
                stats['get_datasets: messages without valid resources'] += 1
            self.source_stats.update(**stats)
        return messages_datasets, output_resources

    def _process(self):
        for resource, descriptor in zip(self.resources, self.datapackage['resources']):
            if descriptor['name'] == 'messages':
                messages_datasets, output_resources = self.process_messages(resource)
            else:
                raise Exception('unexpected resource: {}'.format(descriptor['name']))
        dp = Package({'name': '_',
                      'resources': output_resources})
        dp.add_resource({'name': 'messages-datasets',
                         'path': 'messages-datasets.csv',
                         'dpp:streaming': True,
                         'schema': {'fields': [{'name': 'message_id', 'type': 'string'},
                                               {'name': 'dataset_name', 'type': 'string'}]}})
        return DataStream(dp, ((row for row in r) for r in [messages_datasets]), {})


def flow(parameters, datapackage, resources, source_stats):
    return Flow(DatasetsPackageDataStreamProcessor(resources, datapackage, source_stats))
