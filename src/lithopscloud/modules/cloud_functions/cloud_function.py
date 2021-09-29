import http.client
import json
import sys
from typing import Dict, Any
import requests
from lithopscloud.modules.config_builder import ConfigBuilder, spinner
from lithopscloud.modules.utils import get_option_from_list_alt, free_dialog, color_msg, Color, NEW_INSTANCE

CF_REGIONS = ['eu-de', 'eu-gb', 'us-south', 'us-east', 'au-syd', 'jp-tok']


class CloudFunction(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self, api_key=None) -> Dict[str, Any]:

        is_cf_based_namespace = False  # set to true if namespace is cloud foundry based
        print(color_msg("\n\nConfiguring IBM cloud functions:\n", color=Color.YELLOW))

        choices = CF_REGIONS[:]

        choices.insert(0, "Search across all regions " + color_msg("*Extended runtime duration*",color=Color.RED))
        selected_region = get_option_from_list_alt("Choose a region where your preferred namespace can be found,"
                                                   " or created in", choices)['answer']

        if 'Search across all regions' in selected_region:
            selected_region = ''  # mark region as not yet selected.

        existing_namespaces = self.get_cloud_function_namespaces(selected_region)

        msg = 'Please pick one of your cloud function namespaces'
        msg = f'{msg} in the {selected_region} region' if selected_region else msg
        chosen_namespace = get_option_from_list_alt(msg,
                                                    list(existing_namespaces.keys()),
                                                    instance_to_create='namespace',
                                                    default=self.base_config['ibm_cf']['namespace'])['answer']

        if NEW_INSTANCE in chosen_namespace:
            if not selected_region:
                selected_region = get_option_from_list_alt('Please choose the region you would like '
                                                           'to create a namespace in', CF_REGIONS)['answer']
            namespace_id, chosen_namespace = self.create_cloud_function_namespaces(selected_region)
            del self.base_config['ibm_cf']['api_key']

        else:  # user would like to use an already existing namespace
            selected_region = existing_namespaces[chosen_namespace]['region']

            if existing_namespaces[chosen_namespace]['type'] == 'CF_based':
                print(color_msg("Consider creating an IAM enabled namespace to leverage IAM access control.",color=Color.RED))
                cf_api_key = input("Please provide your cloud foundry api_key from: "
                                   "https://cloud.ibm.com/functions/namespace-settings ")

                self.base_config['ibm_cf']['api_key'] = cf_api_key
                del self.base_config['ibm_cf']['namespace_id']
                is_cf_based_namespace = True

            else:  # API_based namespace
                namespace_id = existing_namespaces[chosen_namespace]['id']
                del self.base_config['ibm_cf']['api_key']

        if not is_cf_based_namespace:  # namespace is either newly created or is an available API based namespace

            self.base_config['ibm_cf']['namespace_id'] = namespace_id

        self.base_config['ibm_cf']['endpoint'] = f'https://{selected_region}.functions.cloud.ibm.com'
        self.base_config['ibm_cf']['namespace'] = chosen_namespace

        print(color_msg("\n------IBM Cloud Function was configured successfully------\n", color=Color.LIGHTGREEN))
        return self.base_config

    def get_cloud_function_namespaces_metadata(self, region, offset=0):
        """returns meta data on namespaces of ibm cloud functions within a specified region
        :param offset - offset from the beginning of the list of results attained from the GET request,
                        which may contain up to 200 namespaces per http response"""

        iam_token = self.get_oauth_token()
        conn = http.client.HTTPSConnection(f"{region}.functions.cloud.ibm.com")
        conn.request("GET", f"/api/v1/namespaces?limit=200&offset={offset}", headers={'Authorization': iam_token})
        res = conn.getresponse()
        metadata = res.read().decode("utf-8")
        json_struct = json.loads(metadata)  # turn string to a dictionary

        return json_struct

    @spinner
    def get_cloud_function_namespaces(self, selected_region):
        """returns the names of the namespaces within a given region."""
        msg = f"Obtaining Cloud Function namespaces in {selected_region}" if selected_region \
            else "Obtaining all existing Cloud Function namespaces"
        print(msg + '...\n')

        namespaces = {}

        for region in [selected_region] if selected_region else CF_REGIONS:
            collecting_namespaces = True
            max_limit = 200
            offset = 0

            #  request for namespaces is limited to 200 at a time, thus the request is fulfilled in increments of 200s.
            while collecting_namespaces:
                namespace_metadata = self.get_cloud_function_namespaces_metadata(region, offset)
                if namespace_metadata['total_count'] == max_limit:
                    offset += max_limit
                else:
                    collecting_namespaces = False

                for name_space in namespace_metadata['namespaces']:
                    if 'name' in name_space:  # API based namespace
                        namespaces[name_space['name']] = {'type': 'API_based', 'id': name_space['id'],
                                                          'region': name_space['location']}
                    else:  # cloud foundry based namespace
                        namespaces[name_space['id']] = {'type': 'CF_based', 'region': name_space['location']}

        return namespaces

    def create_cloud_function_namespaces(self, region):
        """creates a name space in a given region, under a specified resource group and returns the namespace id"""

        @spinner
        def request_new_namespace():
            print("Creating a new namespace...")
            return requests.post(f'https://{region}.functions.cloud.ibm.com/api/v1/namespaces',
                                 headers=headers, json=data).json()

        iam_token = self.get_oauth_token()
        resource_group_id = self.select_resource_group()
        headers = {'Authorization': iam_token, 'accept': 'application/json'}

        namespace_created = False
        while not namespace_created:
            try:
                chosen_namespace = free_dialog("Please name your IBM cloud function namespace")['answer']
                data = {"name": chosen_namespace, "resource_group_id": resource_group_id,
                        "resource_plan_id": "functions-base-plan"}
                response = request_new_namespace()

                if 'id' not in response.keys():
                    print("Chosen name for the namespace isn't valid. Server message:\n", response['message'])
                else:
                    namespace_created = True

            except TypeError:  # allow user to exit config tool using ctrl+c
                print('Terminating config tool, as requested.')
                sys.exit(0)

        return response['id'], chosen_namespace
