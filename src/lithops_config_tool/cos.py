import sys

import ibm_boto3
from ibm_botocore.client import Config
from ibm_botocore.exceptions import ClientError

BUCKET_REGIONS = ['eu-de', 'eu-gb', 'us-south', 'us-east', 'ca-tor', 'au-syd', 'jp-osa', 'jp-tok']


def config_cos():
    def _init_boto3_client(region):
        return ibm_boto3.client(service_name='s3',
                                ibm_api_key_id=get_iam_api_key(),
                                ibm_auth_endpoint="https://iam.ng.bluemix.net/oidc/token",
                                config=Config(signature_version='oauth'),
                                endpoint_url=f'https://s3.{region}.cloud-object-storage.appdomain.cloud')

    s3_client = _init_boto3_client(BUCKET_REGIONS[0])  # initiate using a randomly chosen region

    selected_storage_name = get_option_from_list('Please choose a COS instance:', get_cos_instances())['answer']

    ibm_service_instance_id = get_service_instance_id(selected_storage_name)
    client_response = s3_client.list_buckets(IBMServiceInstanceId=ibm_service_instance_id)

    # prompt user to choose a bucket from buckets available within chosen cos instance
    bucket_names = [bucket["Name"] for bucket in client_response['Buckets']]
    chosen_bucket = get_option_from_list('Please choose a bucket:', bucket_names, 'bucket')['answer']

    if 'Create' not in chosen_bucket:
        print('Searching for bucket in all available regions...')
        bucket_location = ''
        for index, region in enumerate(BUCKET_REGIONS):
            try:
                if index:  # skip re-initiating client in the current region (index 0)
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
            raise Exception("Couldn't locate the bucket's region. Cannot proceed.")

    else:  # user would like to create a new bucket
        bucket_location = get_option_from_list('Please choose a region you would like your bucket to be located in :',
                                               BUCKET_REGIONS)['answer']
        # changing location of the client to create a bucket in requested region.
        s3_client = _init_boto3_client(bucket_location)

        chosen_bucket = create_bucket(s3_client, ibm_service_instance_id)

    update_config_file(f"""ibm_cos:
                          storage_bucket: {chosen_bucket}
                          region: {bucket_location}""")

    print("\n------IBM Cloud Object Storage was configured successfully------")


def create_bucket(s3_client, ibm_service_instance_id):
    """Creates a bucket and returns its name"""

    bucket_created = False
    while not bucket_created:
        try:
            chosen_bucket = free_dialog("Please choose a name for your new bucket")['answer']
            s3_client.create_bucket(Bucket=f'{chosen_bucket}', IBMServiceInstanceId=ibm_service_instance_id)
            bucket_created = True
        except TypeError:  # allow user to exit config tool using ctrl+c
            print('Terminating config tool, as requested.')
            sys.exit(0)
        except Exception as invalid_bucket_name:
            print("Invalid Bucket Name:", invalid_bucket_name)

    return chosen_bucket


def get_cos_instances():
    """return available cos instances by name"""
    storage_instances = []
    for resource in get_resource_instances()['resources']:
        if 'cloud-object-storage' in resource['id']:
            storage_instances.append(resource['name'])
    return storage_instances


def get_service_instance_id(storage_name):
    """returns CRN of selected storage instance"""
    for resource in get_resource_instances()['resources']:
        if storage_name in resource['name']:
            return resource['id']
