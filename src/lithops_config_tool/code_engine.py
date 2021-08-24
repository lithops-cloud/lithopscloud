import requests
import yaml
from ibm_code_engine_sdk.ibm_cloud_code_engine_v1 import IbmCloudCodeEngineV1

from util_func import get_option_from_list, get_iam_api_key, get_resource_instances, \
    update_config_file, get_authenticator

CE_REGIONS = ['eu-de', 'eu-gb', 'us-south', 'ca-tor', 'jp-osa', 'jp-tok']


def config_ce():
    print("\n\n Configuring Code Engine:")

    ce_instances = get_ce_instances()
    chosen_project = get_option_from_list('Please pick one your Code Engine projects :',
                                          list(ce_instances.keys()))['answer']
    guid = ce_instances[chosen_project]['guid']
    region = ce_instances[chosen_project]['region']

    project_namespace = get_project_namespace(region, guid)

    runtime_image = input("Please provide a runtime image suitable"
                                " for your current lithops version.\nFor more information please refer to: "
                                "https://github.com/lithops-cloud/lithops/tree/master/runtime/code_engine ")

    update_config_file(f"""code_engine:
                          namespace: {project_namespace}
                          region: {ce_instances[chosen_project]['region']}
                          runtime: {runtime_image}""")

    print("\n------IBM Code Engine was configured successfully------\n")


def get_project_namespace(region, guid):
    """returns the the namespace of a previously chosen project (identified by its guid)"""
    ce_client = IbmCloudCodeEngineV1(authenticator=get_authenticator())
    ce_client.set_service_url(f'https://api.{region}.codeengine.cloud.ibm.com/api/v1')

    iam_response = requests.post('https://iam.cloud.ibm.com/identity/token',
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                 data={
                                     'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                                     'apikey': get_iam_api_key(),
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


def get_ce_instances():
    """return available code engine instances, along with their corresponding region and group user id."""
    ce_instances = {}
    for resource in get_resource_instances()['resources']:
        if 'codeengine' in resource['id']:
            ce_instances[resource['parameters']['name']] = {'region': resource['region_id'],
                                                            'guid': resource['guid']}

    return ce_instances


def verify_code_engine():
    pass