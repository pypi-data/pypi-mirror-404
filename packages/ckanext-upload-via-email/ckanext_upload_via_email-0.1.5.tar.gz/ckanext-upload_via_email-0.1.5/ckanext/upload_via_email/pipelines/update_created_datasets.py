from dataflows import Flow, PackageWrapper
from datapackage import Package
from datapackage_pipelines_ckanext import helpers as ckanext_helpers
import shutil
from os import path
import json
from oauth2client.client import OAuth2Credentials
from googleapiclient.discovery import build
from httplib2 import Http
from email.mime.text import MIMEText
from os import environ
import base64
from collections import defaultdict, deque
from utils import temp_loglevel
import logging
import re


def send_success_message(data_path, message_id, dataset_name, config, service, stats, override_to=None):
    with open(path.join(data_path, 'attachments', message_id, 'message.json')) as f:
        source_message = json.load(f)
    dataset_url = '{}/dataset/{}'.format(environ['CKAN_URL'], dataset_name)
    message = MIMEText(config['success_message'].format(dataset_url=dataset_url))
    source_message_from_headers = [header for header in source_message['payload']['headers'] if header['name'] == 'From']
    logging.info(f'source message from headers: {source_message_from_headers}')
    from_email = [header['value'] for header in source_message['payload']['headers'] if header['name'] == 'From'][0]
    if override_to:
        message['to'] = override_to
    else:
        try:
            message['to'] = re.findall('<(.*)>', from_email)[0]
        except Exception:
            message['to'] = from_email
    logging.info(f'sending success message to: {message["to"]}')
    message['from'] = config['success_message_from_email']
    message['subject'] = config['success_message_subject']
    message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode('utf-8')}
    with temp_loglevel():
        service.users().messages().send(userId='me', body=message).execute()
    stats['update_created_datasets: sent emails'] += 1
    return dataset_url, from_email


def flow(parameters, datapackage, resources, source_stats):
    config = ckanext_helpers.get_plugin_configuration('upload_via_email')
    data_path = config['data_path']
    credentials = OAuth2Credentials.from_json(config['gmail_token'])
    assert credentials and not credentials.invalid
    service = build('gmail', 'v1', http=credentials.authorize(Http()), cache_discovery=False)

    def get_ckan_log(datasets_messages, ckan_log_resource):
        last_created_datasets = deque(maxlen=10)
        stats = defaultdict(int)
        ckan_log_path = path.join(data_path, 'ckan_log', 'datapackage.json')
        if path.exists(ckan_log_path):
            yield from Package(ckan_log_path).get_resource('ckan-log').iter(keyed=True)
        successful_message_ids = set()
        for row in ckan_log_resource:
            if not row['dataset_name'] or row['dataset_name'] == '_':
                continue
            message_id = datasets_messages.get(row['dataset_name'])
            row['message_id'] = message_id
            if not row['error'] and message_id not in successful_message_ids:
                successful_message_ids.add(message_id)
                try:
                    dataset_url, from_email = send_success_message(data_path, message_id, row['dataset_name'], config, service, stats)
                except Exception:
                    if not config.get('success_message_default_to_email'):
                        raise
                    else:
                        logging.exception(f"failed to send to from email, trying default sender: {config['success_message_default_to_email']}")
                        dataset_url, from_email = send_success_message(data_path, message_id, row['dataset_name'],
                                                                       config, service, stats, config['success_message_default_to_email'])
                last_created_datasets.append(dataset_url)
            yield row
        shutil.rmtree(path.join(data_path, 'attachments'), ignore_errors=True)
        source_stats.update(**stats)
        source_stats['last created datasets'] = list(last_created_datasets)

    def update_created_datasets(package: PackageWrapper):
        for descriptor in datapackage['resources']:
            if descriptor.get('dpp:streaming'):
                resource = next(resources)
                if descriptor['name'] == 'messages-datasets':
                    datasets_messages = {row['dataset_name']: row['message_id'] for row in resource}
                elif descriptor['name'] == 'ckan-log':
                    ckan_log_resource = resource
                    ckan_log_descriptor = descriptor
        for resource in resources:
            for row in resource:
                pass
        ckan_log_descriptor['schema']['fields'] += [{'name': 'message_id', 'type': 'string'},
                                                    {'name': 'from_email', 'type': 'string'}]
        yield Package({'name': '_', 'resources': [ckan_log_descriptor]})
        yield get_ckan_log(datasets_messages, ckan_log_resource)


    return Flow(update_created_datasets)
