import sys
import requests
import yaml
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_code_engine_sdk.ibm_cloud_code_engine_v1 import IbmCloudCodeEngineV1
from lithopscloud.modules.utils import CACHE, free_dialog

from lithopscloud.modules.config_builder import ConfigBuilder
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list_alt

CE_REGIONS = []


class CodeEngine(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self, api_key=None) -> Dict[str, Any]:

        print("\n\n Configuring Code Engine:")
        init_ce_region_list()

        ce_instances = self.get_ce_instances()
        chosen_project = get_option_from_list_alt('Please pick one your Code Engine projects :',
                                                  list(ce_instances.keys()), instance_to_create='project')['answer']

        if chosen_project == 'Create a new project':
            region, project_namespace = self.create_new_project()
        else:
            project_guid = ce_instances[chosen_project]['guid']
            region = ce_instances[chosen_project]['region']

            project_namespace = self.get_project_namespace(region, project_guid)

        self.base_config['code_engine']['namespace'] = project_namespace
        self.base_config['code_engine']['region'] = region
        self.base_config['lithops']['backend'] = 'code_engine'

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

        res_group_objects = self.get_resources()

        for resource in res_group_objects:
            if 'codeengine' in resource['id']:
                if 'parameters' in resource:  # to accommodate older projects
                    project_name = resource['parameters']['name']
                else:
                    project_name = resource['name']
                ce_instances[project_name] = {'region': resource['region_id'],
                                              'guid': resource['guid']}

        return ce_instances

    def create_new_project(self):
        """Creates a new project. requires a paid account.

        :returns the new project's name and namespace.  """

        region = get_option_from_list_alt('Please choose a region you would like to create your project in :',
                                          CE_REGIONS)['answer']

        name = free_dialog("Please name your new Code Engine project")['answer']

        try:
            response = self.resource_controller_service.create_resource_instance(
                name=name,
                target=region,
                resource_group=CACHE['resource_group_id'],
                resource_plan_id='814fb158-af9c-4d3c-a06b-c7da42392845'
            ).get_result()
        except Exception as e:
            print(f"Couldn't create new code engine project.\n{e} ")
            sys.exit()  # used sys.exit instead of exception to cancel traceback that will hide the error message

        project_guid = response['guid']
        project_namespace = self.get_project_namespace(region, project_guid)

        return region, project_namespace


def init_ce_region_list():
    """initializes a list of the available regions in which a user can create a bucket"""
    response = requests.get(
        'https://globalcatalog.cloud.ibm.com/api/v1/814fb158-af9c-4d3c-a06b-c7da42392845/%2A').json()
    for resource in response['resources']:
        CE_REGIONS.append(resource['geo_tags'][0])
