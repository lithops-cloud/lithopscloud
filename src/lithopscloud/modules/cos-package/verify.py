from enum import Enum
import ibm_boto3
import ibm_botocore
from ibm_botocore.credentials import DefaultTokenManager
from ibm_botocore.exceptions import ClientError, CredentialRetrievalError
from ibm_botocore.client import Config

from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.utils import ARG_STATUS, color_msg, Color, inquire_user, NEW_INSTANCE, get_confirmation
from lithopscloud.modules.cos import init_cos_region_list, BUCKET_REGIONS, get_cos_instances, CosConfig

KEY_TYPE = Enum('TYPE', 'API HMAC')  # available types of identification for the ibm_cf service
PUBLIC_ENDPOINT_TEMPLATE = 'https://s3.{}.cloud-object-storage.appdomain.cloud'


def verify(base_config):
    """ this function outputs error messages based on lacking or invalid values in regard the cos-package segment of the
        lithops config file.
       :param dict base_config: contents of provided config file.  """

    cos_config = base_config['ibm_cos']
    iam_api_key = base_config['ibm']['iam_api_key']
    output = {'ibm_cos': {}}
    init_cos_region_list()

    def _pick_viable_key():
        """:returns the all possible credentials. keys are verified and flagged if invalid. """

        chosen_key, chosen_key_type, api_key, access_key, secret_key = ('',) * 5

        if iam_api_key and iam_api_key != ARG_STATUS.INVALID:
            chosen_key = iam_api_key
            chosen_key_type = KEY_TYPE.API
            output['ibm'] = {'iam_api_key': iam_api_key}

        if 'api_key' in cos_config:
            api_key = cos_config['api_key']
            try:
                test_apikey_and_bucket(api_key, KEY_TYPE.API)
                if not chosen_key:
                    chosen_key = api_key
                    chosen_key_type = KEY_TYPE.API
                    output['ibm_cos']['api_key'] = api_key
            except CredentialRetrievalError:
                api_key = ARG_STATUS.INVALID
                print(color_msg("Invalid COS ApiKey", Color.RED))

        if {'access_key', 'secret_key'}.issubset(cos_config.keys()):
            access_key, secret_key = cos_config['access_key'], cos_config['secret_key']
            try:
                test_apikey_and_bucket((access_key, secret_key), 'hmac')
                if not chosen_key:
                    chosen_key = (access_key, secret_key)
                    chosen_key_type = KEY_TYPE.HMAC
                    output['ibm_cos'].update({'access_key': access_key, 'secret_key': secret_key})
            except:  # more than a single possible exception may arise
                access_key, secret_key = ARG_STATUS.INVALID, ARG_STATUS.INVALID
                print(color_msg("Invalid access_key and/or secret_key", Color.RED))

        elif 'access_key' in cos_config.keys() or 'secret_key' in cos_config.keys():
            print(color_msg("both access_key and secret_key are essential parts of the HMAC credential", Color.RED))

        return chosen_key, chosen_key_type, api_key, access_key, secret_key

    def _verify_region_endpoint():
        """:returns endpoint and region values after a basic validity check. """

        endpoint, region = '', ''
        private_endpoint_template = 'https://s3.private.{}.cloud-object-storage.appdomain.cloud'

        if 'endpoint' in cos_config and 'private_endpoint' in cos_config:
            if cos_config['endpoint'] not in [PUBLIC_ENDPOINT_TEMPLATE.format(region) for region in BUCKET_REGIONS]:
                print(color_msg(
                    f"endpoint must be of the format {PUBLIC_ENDPOINT_TEMPLATE.replace('{}', '<region>')}",
                    Color.RED))
            else:
                if cos_config['private_endpoint'] not in [private_endpoint_template.format(region) for region in
                                                          BUCKET_REGIONS]:
                    print(color_msg(
                        f"private_endpoint must be of the format {private_endpoint_template.replace('{}', '<region>')}",
                        Color.RED))
                else:  # endpoint's value will be set only if a valid private endpoint was also provided
                    endpoint = cos_config['endpoint']

        elif 'region' not in cos_config:
            print(color_msg(
                "Either 'region' or both 'endpoint' and 'private_endpoint' fields must be provided to configure COS",
                Color.RED))
            cos_config['region'] = ''

        if 'region' in cos_config:
            if cos_config['region'] not in BUCKET_REGIONS:
                print(color_msg(f"Field 'region' must be a value from the following list:{BUCKET_REGIONS}",
                                Color.RED))
            else:
                region = cos_config['region']

        return endpoint, region

    def _verify_bucket_match_config(endpoint, region):
        """:returns updated output if specified bucket corresponds with the rest of the input file's parameters"""

        if 'storage_bucket' not in cos_config:
            cos_config['storage_bucket'] = ''

        if not cos_config['storage_bucket']:
            print(color_msg('Bucket name is a mandatory field necessary to configure COS', Color.RED))

        else:
            bucket = cos_config['storage_bucket']
            output['ibm_cos']['storage_bucket'] = bucket

            bucket_endpoint = verify_bucket(chosen_key, chosen_key_type, '', bucket)

            if bucket_endpoint:
                if endpoint:
                    if bucket_endpoint != endpoint:
                        print(color_msg("Provided endpoint doesn't match bucket's endpoint", Color.RED))
                    else:
                        output['ibm_cos'] = {'endpoint': endpoint, 'private_endpoint': cos_config['private_endpoint']}
                        return output

                if region:
                    if region not in bucket_endpoint:
                        print(color_msg("Provided region doesn't match bucket's region", Color.RED))
                    else:
                        output['ibm_cos']['region'] = region
                        return output

                # complete missing field: 'region' using available info:
                region = bucket_endpoint[bucket_endpoint.find('.') + 1:bucket_endpoint.find('.cloud')]
                output['ibm_cos']['region'] = region
                return output

    chosen_key, chosen_key_type, api_key, access_key, secret_key = _pick_viable_key()
    endpoint, region = _verify_region_endpoint()

    if chosen_key:  # bucket could be verified only if a valid key was found.
        verified_config = _verify_bucket_match_config(endpoint, region)
        if verified_config:
            return verified_config

    # user didn't provide any credentials
    if not chosen_key and ARG_STATUS.INVALID not in {iam_api_key, api_key, access_key}:
        print(color_msg('Either an IAmApiKey, COS apiKey, or HMAC credentials must be provided', Color.RED))

    return reconfigure(base_config, output)


def test_apikey_and_bucket(key, key_type: KEY_TYPE, endpoint=None, bucket=None):
    """runs a function using user's credentials to test whether credentials are valid
       and/or whether the bucket exists within given region.
       :exception is raised in accordance with faulty values and handled by the calling function. """

    dummy_bucket = 'b'  # an already taken bucket name, that can't possibly be provided by user

    if not bucket:  # verify key given with placeholder values
        bucket = dummy_bucket
        endpoint = PUBLIC_ENDPOINT_TEMPLATE.format('eu-de')
    if key_type == KEY_TYPE.API:  # iamapikey or cloud foundry api
        client_config = ibm_botocore.client.Config(signature_version='oauth')
        token_manager = DefaultTokenManager(api_key_id=key)
        cos_client = ibm_boto3.client('s3', token_manager=token_manager,
                                      endpoint_url=endpoint, config=client_config)
    else:  # HMAC key
        cos_client = ibm_boto3.client('s3',aws_access_key_id=key[0],
                                      aws_secret_access_key=key[1],
                                      endpoint_url=endpoint)

    try:
        cos_client.get_bucket_location(Bucket=bucket)

    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchBucket':
            if bucket != dummy_bucket:  # disregard bucket exceptions when verifying keys (thus using dummy bucket).
                raise
        else:
            raise


def verify_bucket(key, key_type, endpoint, bucket):
    """ :returns endpoint in which the bucket was found, else returns None.
        verifies the existence of a bucket within the cos-package instance that is certified by the provided key.
        if no valid region/endpoint was provided, the bucket is searched for across all available regions.
        """

    if bucket and key != ARG_STATUS.INVALID:
        error_msg = 'No such bucket exists '
        if endpoint:
            error_msg += 'in specified region'
            try:
                test_apikey_and_bucket(key, key_type, endpoint, bucket)
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchBucket':
                    print(color_msg(error_msg, Color.RED))
                    return None
        else:
            for endpoint in [PUBLIC_ENDPOINT_TEMPLATE.format(region) for region in BUCKET_REGIONS]:
                try:
                    test_apikey_and_bucket(key, key_type, endpoint, bucket)
                    return endpoint
                except:
                    pass

            print(color_msg(error_msg, Color.RED))
            return None


def reconfigure(base_config, output):
    """Directs the user to repeat the reconfiguration process and returns the recreated cos configuration"""

    iamapikey = base_config['ibm']['iam_api_key']

    should_reconfigure = get_confirmation(color_msg("Unable to configure the COS segment due to invalid critical field(s)."
                                             " Would you like to reconfigure this segment?", Color.RED))['answer']
    if should_reconfigure:
        if not iamapikey or iamapikey == ARG_STATUS.INVALID:
            base_config['ibm']['iam_api_key'] = ''
            ApiKeyConfig(base_config).run()  # sets base_config's iam_api_key value

        CosConfig(base_config).run()  # sets base_config's cos segment
        output['ibm_cos'] = base_config['ibm_cos']
        return output





