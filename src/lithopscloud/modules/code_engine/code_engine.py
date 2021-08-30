import requests
import yaml
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_code_engine_sdk.ibm_cloud_code_engine_v1 import IbmCloudCodeEngineV1
from lithopscloud.modules.code_engine import CACHE

from lithopscloud.modules.config_builder import ConfigBuilder
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list_alt

CE_REGIONS = ['eu-de', 'eu-gb', 'us-south', 'ca-tor', 'jp-osa', 'jp-tok']


class CodeEngine(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self, api_key=None) -> Dict[str, Any]:

        print("\n\n Configuring Code Engine:")

        ce_instances = self.get_ce_instances()
        chosen_project = get_option_from_list_alt('Please pick one your Code Engine projects :',
                                                  list(ce_instances.keys()))['answer']

        guid = ce_instances[chosen_project]['guid']
        CACHE['guid'] = guid

        region = ce_instances[chosen_project]['region']

        project_namespace = self.get_project_namespace(region, guid)

        self.base_config['code_engine']['namespace'] = project_namespace
        self.base_config['code_engine']['region'] = ce_instances[chosen_project]['region']

        print("\n------IBM Code Engine was configured successfully------\n")

        return self.base_config

    def get_project_namespace(self, region, guid):
        """returns the the namespace of a previously chosen project (identified by its guid)"""
        ce_client = IbmCloudCodeEngineV1(authenticator=IAMAuthenticator(apikey=self.base_config['ibm']['iam_api_key']))
        ce_client.set_service_url(f'https://api.{region}.codeengine.cloud.ibm.com/api/v1')

        iam_response = requests.post('https://iam.cloud.ibm.com/identity/token',
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     data={
                                         'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                                         'apikey': self.base_config['ibm']['iam_api_key'],
                                         'response_type': 'delegated_refresh_token',
                                         'receiver_client_ids': 'ce',
                                         'delegated_refresh_token_expiry': '3600'
                                     })

        delegated_refresh_token = iam_response.json()['delegated_refresh_token']

        kubeconfig_response = ce_client.get_kubeconfig(
            x_delegated_refresh_token=delegated_refresh_token,
            id=guid,
        )
        kubeconfig_string = kubeconfig_response.get_result().content.decode("utf-8")

        dict_struct = yaml.safe_load(kubeconfig_string)
        cluster_namespace = dict_struct['contexts'][0]['context']['namespace']
        return cluster_namespace

    def get_ce_instances(self):
        """return available code engine instances, along with their corresponding region and group user id."""
        ce_instances = {}

        resource_group_id = self.get_resource_group_id()
        res_group_objects = \
            self.resource_service_client.list_resource_groups(resource_group_id=resource_group_id).get_result()[
                'resources']
        for resource in res_group_objects:
            if 'codeengine' in resource['id']:
                ce_instances[resource['parameters']['name']] = {'region': resource['region_id'],
                                                                'guid': resource['guid']}

        return ce_instances

    def get_resource_group_id(self):
        """returns resource group id of a resource group the user will be prompt to pick"""

        available_resource_groups = {}
        resource_group_list = self.resource_service_client.service_client.list_resource_groups()
        for resource in resource_group_list.result['resources']:
            available_resource_groups[resource['name']] = [resource['id']]

        chosen_resource_group = \
            get_option_from_list_alt('Please choose the resource group your resource instances belong to :',
                                     list(available_resource_groups.keys()))['answer']
        resource_group_id = available_resource_groups[chosen_resource_group]

        return resource_group_id
