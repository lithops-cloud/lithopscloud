import sys
import requests
import yaml
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_code_engine_sdk.ibm_cloud_code_engine_v1 import IbmCloudCodeEngineV1
from lithopscloud.modules.utils import CACHE, free_dialog, retry_on_except, color_msg, Color, NEW_INSTANCE, inquire_user
from lithopscloud.modules.config_builder import ConfigBuilder, spinner
from typing import Any, Dict

CE_REGIONS = []


class CodeEngine(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self, api_key=None) -> Dict[str, Any]:

        print(color_msg("\n\nConfiguring IBM Code Engine:\n", color=Color.YELLOW))
        init_ce_region_list()

        ce_instances = self.get_ce_instances()

        chosen_project = inquire_user('Please pick one of your Code Engine projects',
                                      color_ce_instances_with_regions(ce_instances),
                                      create_new_instance=NEW_INSTANCE + ' project')

        if NEW_INSTANCE in chosen_project:
            chosen_project = self.create_new_project()

        project_namespace = self.get_project_namespace(chosen_project)

        self.base_config['code_engine']['namespace'] = project_namespace
        self.base_config['code_engine']['region'] = chosen_project['region']
        self.base_config['lithops']['backend'] = 'code_engine'

        print(color_msg("\n------IBM Code Engine was configured successfully------\n", color=Color.LIGHTGREEN))

        return self.base_config

    def get_project_namespace(self, project_instance):
        """returns the the namespace of a previously chosen project (identified by its guid)
        :param project_instance: a dict containing the name, region and guid of a project"""

        @spinner
        @retry_on_except(retries=10, sleep_duration=7, error_msg="IBM Cloud Code Engine is currently unavailable. "
                                                                "Your request could not be processed. "
                                                                "Please wait a few minutes and try again.  ")
        def _get_kubeconfig_response():
            return ce_client.get_kubeconfig(x_delegated_refresh_token=delegated_refresh_token, id=project_instance['guid'])

        ce_client = IbmCloudCodeEngineV1(authenticator=IAMAuthenticator(apikey=self.base_config['ibm']['iam_api_key'], url=ConfigBuilder.compute_iam_endpoint))
        ce_client.set_service_url(f"https://api.{project_instance['region']}.codeengine.cloud.ibm.com/api/v1")

        iam_token_url = 'https://iam.cloud.ibm.com/identity/token'
        if ConfigBuilder.compute_iam_endpoint:
            iam_token_url = ConfigBuilder.compute_iam_endpoint + '/identity/token'
            
        iam_response = requests.post(iam_token_url,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     data={
                                         'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                                         'apikey': self.base_config['ibm']['iam_api_key'],
                                         'response_type': 'delegated_refresh_token',
                                         'receiver_client_ids': 'ce',
                                         'delegated_refresh_token_expiry': '3600'
                                     })

        delegated_refresh_token = iam_response.json()['delegated_refresh_token']

        kubeconfig_response = _get_kubeconfig_response()
        kubeconfig_string = kubeconfig_response.get_result().content.decode("utf-8")

        dict_struct = yaml.safe_load(kubeconfig_string)
        cluster_namespace = dict_struct['contexts'][0]['context']['namespace']
        return cluster_namespace

    def get_ce_instances(self, verbose=True):
        """return available code engine instances, along with their corresponding region and group user id."""

        if verbose:
            print("Obtaining all existing Code Engine projects...\n")
        ce_instances = []

        res_group_objects = self.get_resources()

        for resource in res_group_objects:
            if 'codeengine' in resource['id']:
                if 'parameters' in resource:  # to accommodate older projects
                    project_name = resource['parameters']['name']
                else:
                    project_name = resource['name']

                ce_instances.append({"name": project_name, 'region': resource['region_id'], 'guid': resource['guid']})

        return ce_instances

    def create_new_project(self):
        """Creates a new project. requires a paid account.
        :returns the new project's name and namespace.  """

        region = inquire_user('Please choose a region you would like to create your project in',
                              CE_REGIONS, handle_strings=True)

        name = free_dialog("Please name your new Code Engine project")['answer']

        try:
            response = self.resource_controller_service.create_resource_instance(
                name=name,
                target=region,
                resource_group=CACHE['resource_group_id'],
                resource_plan_id='814fb158-af9c-4d3c-a06b-c7da42392845'
            ).get_result()
        except Exception as e:
            print(color_msg(f"Couldn't create new code engine project.\n{e} ", color=Color.RED))
            sys.exit(1)  # used sys.exit instead of exception to cancel traceback that will hide the error message

        project_guid = response['guid']
        print(color_msg(f"A new Code Engine project named '{name}' was created.",color=Color.LIGHTGREEN))

        return {"name": name, 'region': region, 'guid': project_guid}


@retry_on_except(retries=3, sleep_duration=7)
def init_ce_region_list():
    """initializes a list of the available regions in which a user can create a code engine project"""
    response = requests.get(
        'https://globalcatalog.cloud.ibm.com/api/v1/814fb158-af9c-4d3c-a06b-c7da42392845/%2A').json()
    for resource in response['resources']:
        CE_REGIONS.append(resource['geo_tags'][0])


def color_ce_instances_with_regions(ce_instances):
    """colors each ce_instance name and affix its region to it"""
    for instance in ce_instances:
        instance['name'] = instance['name'] + ' ' + color_msg(instance['region'], color=Color.YELLOW)
    return ce_instances
