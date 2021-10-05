import json
import sys
from typing import Any, Dict
import ibm_boto3
import requests
from ibm_botocore.client import Config
from ibm_botocore.exceptions import ClientError
from lithopscloud.modules.config_builder import ConfigBuilder
from lithopscloud.modules.utils import free_dialog, CACHE, color_msg, Color, NEW_INSTANCE, retry_on_except
from lithopscloud.modules.utils import inquire_user

BUCKET_REGIONS = []


class CosConfig(ConfigBuilder):

    def run(self) -> Dict[str, Any]:
        def _init_boto3_client(region):
            return ibm_boto3.client(service_name='s3',
                                    ibm_api_key_id=self.base_config['ibm']['iam_api_key'],
                                    ibm_auth_endpoint="https://iam.ng.bluemix.net/oidc/token",
                                    config=Config(signature_version='oauth'),
                                    endpoint_url=f'https://s3.{region}.cloud-object-storage.appdomain.cloud')

        print(color_msg("\n\nConfiguring IBM cloud object storage:\n", color=Color.YELLOW))

        init_cos_region_list()
        s3_client = _init_boto3_client(BUCKET_REGIONS[0])  # initiate using a randomly chosen region

        print("Obtaining existing COS instances...")

        resource_instances = self.get_resources()

        selected_storage_name = inquire_user('Please choose a COS instance',
                                             get_cos_instances(resource_instances),
                                             create_new_instance=NEW_INSTANCE + ' COS instance')

        if NEW_INSTANCE in selected_storage_name:
            ibm_service_instance_id = self.create_cos_instance()

        else:
            ibm_service_instance_id = selected_storage_name['id']

        client_response = s3_client.list_buckets(IBMServiceInstanceId=ibm_service_instance_id)
        # prompt user to choose a bucket from buckets available within chosen cos instance
        default_bucket = self.base_config['ibm_cos']['storage_bucket'] if self.base_config.get('ibm_cos') else None
        chosen_bucket = inquire_user('Please choose a bucket',  client_response['Buckets'],
                                     create_new_instance=NEW_INSTANCE + ' bucket',
                                     choice_key='Name',
                                     default=default_bucket)

        if NEW_INSTANCE not in chosen_bucket:
            chosen_bucket = chosen_bucket['Name']
            print('Searching for bucket in all available regions...')
            bucket_location = ''
            for index, region in enumerate(BUCKET_REGIONS):
                try:
                    # skip re-initiating client in the current region (index 0)
                    if index:
                        s3_client = _init_boto3_client(region)
                        print(f"Searching for bucket in {region}...")
                    s3_client.get_bucket_location(Bucket=chosen_bucket)
                    bucket_location = region
                    print(f"bucket found in {region}...")
                    break
                except ClientError as ex:
                    if ex.response['Error']['Code'] == 'NoSuchBucket':
                        pass
                    else:
                        raise

            if not bucket_location:
                raise Exception(
                    "Couldn't locate the bucket's region. Cannot proceed.")

        else:  # user would like to create a new bucket
            bucket_location = \
                inquire_user('Please choose a region you would like your bucket to be located in',
                             BUCKET_REGIONS, handle_strings=True)
            # changing location of the client to create a bucket in requested region.
            s3_client = _init_boto3_client(bucket_location)

            chosen_bucket = create_bucket(s3_client, ibm_service_instance_id)

        self.base_config['ibm_cos'] = {'storage_bucket': chosen_bucket, 'region': bucket_location}
        self.base_config['lithops']['storage'] = 'ibm_cos'

        print(color_msg("\nIBM Cloud Object Storage was configured successfully", color=Color.LIGHTGREEN))
        return self.base_config

    def create_cos_instance(self):
        """creates a cloud object storage instance, under a specified resource group and returns its user chosen name"""
        plan_type = {'standard': '744bfc56-d12c-4866-88d5-dac9139e0e5d', 'lite': '2fdf0c08-2d32-4f46-84b5-32e0c92fffd8'}
        cos_instance_created = False

        while not cos_instance_created:

            plan = inquire_user('Please choose a pricing tier',
                                ['lite (restricted to one per account)', 'standard (requires a paid account)']
                                , handle_strings=True)
            plan = plan_type[plan.split(' ')[0]]
            cos_name = free_dialog("Please name your COS instance")['answer']

            try:
                response = self.resource_controller_service.create_resource_instance(
                    name=cos_name,
                    target=f"crn:v1:bluemix:public:globalcatalog::::deployment:{plan}%3Aglobal",
                    resource_group=CACHE['resource_group_id'],
                    resource_plan_id=plan
                ).get_result()
                cos_instance_created = True

            except Exception as e:
                print(color_msg(f"Couldn't create new cloud object storage instance.\n{e} ", color=Color.RED))

        print(color_msg(f"A new COS instance named '{cos_name}' was created", color=Color.LIGHTGREEN))
        return response['id']


def create_bucket(s3_client, ibm_service_instance_id):
    """Creates a bucket and returns its name"""

    bucket_created = False
    while not bucket_created:
        try:
            chosen_bucket = free_dialog("Please choose a name for your new bucket")['answer']
            s3_client.create_bucket(Bucket=f'{chosen_bucket}', IBMServiceInstanceId=ibm_service_instance_id)
            bucket_created = True
        except TypeError:  # allow user to exit config tool using ctrl+c
            print(color_msg('Terminating config tool, as requested.', color=Color.RED))
            sys.exit(0)
        except Exception as invalid_bucket_name:
            print(color_msg(f"Invalid Bucket Name: {invalid_bucket_name}", color=Color.RED))

    return chosen_bucket


def get_cos_instances(resource_instances):
    """return available cos instances by name and id"""
    storage_instances = []
    for resource in resource_instances:
        if 'cloud-object-storage' in resource['id']:
            # storage_instances.append(resource['name'])
            storage_instances.append({"name": resource['name'], "id": resource['id']})

    return storage_instances


@retry_on_except(retries=3, sleep_duration=7)
def init_cos_region_list():
    """initializes a list of the available regions in which a user can create a bucket"""
    response = requests.get(f'https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints').json()
    for region in response['service-endpoints']['regional']:
        BUCKET_REGIONS.append(region)
