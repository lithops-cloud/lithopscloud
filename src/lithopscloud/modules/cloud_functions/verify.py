import ast
import base64
import http.client

from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.cloud_functions import CloudFunction
from lithopscloud.modules.cloud_functions.cloud_function import CF_REGIONS
from lithopscloud.modules.utils import color_msg, ARG_STATUS, Color, inquire_user, get_confirmation


def verify(base_config):
    """ this function outputs error messages based on lacking or invalid values in regard the cloud functions segment
        of the lithops config file. Prioritizing iam-api-key based configuration over an apikey based configuration.
       :param dict base_config: contents of provided config file.  """

    endpoint_template = 'https://{}.functions.cloud.ibm.com'
    required_params = {'endpoint': '', 'namespace': ''}

    cf_config = base_config['ibm_cf']
    iam_api_key = base_config['ibm']['iam_api_key']
    namespace_id = cf_config.get('namespace_id', '')  # required to configure using iamapikey
    output = {'ibm_cf': {}}
    region_provided = ''

    def _verify_cf_apikey_match():
        """:returns the apikey value provided if its valid, otherwise flags it as invalid."""

        api_key = cf_config.get('api_key', '')
        if api_key:
            namespace_data = verify_cf_api_key(api_key)  # matching namespace for given apikey.

            if namespace_data:
                region = namespace_data['region']
                output['ibm_cf']['endpoint'] = endpoint_template.format(region)
                namespace = namespace_data['namespace']
                output['ibm_cf']['namespace'] = namespace

                if region_provided:  # endpoint was provided and contains a valid value
                    if region not in region_provided:
                        print(color_msg(f"Cloud Foundry api key provided belongs to the region '{region}' rather than '{region_provided}'", Color.RED))

                if required_params['namespace']:
                    if required_params['namespace'] != namespace:
                        print(color_msg(f"Cloud Foundry api key provided belongs to the namespace '{namespace}' rather than '{required_params['namespace']}'",Color.RED))

            else:
                api_key = ARG_STATUS.INVALID

        return api_key

    def _verify_iamapikey_match(api_key):
        """:returns a valid ibm_cf configuration if provided iamapikey match the rest of the specified parameters"""

        if not namespace_id:
            if not api_key:
                print(color_msg(f"namespace_id is mandatory in 'ibm_cf' section of the configuration "
                      f"when configuring with an IAM-API-KEY", Color.RED))
        elif iam_api_key != ARG_STATUS.INVALID:
            params_matched = 0
            cf = CloudFunction(base_config)
            namespaces = cf.get_cloud_function_namespaces()
            matched_namespace = next((space for space in namespaces if space['type'] == 'API_based' and space['id'] == namespace_id),None)

            if not matched_namespace:
                print(color_msg("no namespace that is certified with the provided iamapikey "
                                "can be identified by the specified namespace id", Color.RED))
            else:
                if region_provided:
                    if matched_namespace['region'] != region_provided:
                        print(color_msg(f"IAM Api Key and namespace id provided points to a namespace in region '{matched_namespace['region']}' "
                                        f"rather than '{region_provided}'", Color.RED))
                    else:
                        params_matched += 1
                output['ibm_cf']['endpoint'] = endpoint_template.format(matched_namespace['region'])

                if required_params['namespace']:
                    if matched_namespace['name'] != required_params['namespace']:
                        print(color_msg(f"provided IAM Api Key and namespace id point to a namespace named"
                                        f" '{matched_namespace['name']}' rather than the specified: '{required_params['namespace']}'", Color.RED))
                    else:
                        params_matched += 1
                output['ibm_cf']['namespace'] = matched_namespace['name']

                output['ibm'] = {'iam_api_key': iam_api_key}
                output['ibm_cf']['namespace_id'] = namespace_id
                return output

    for param in required_params:
        if param not in cf_config:
            print(color_msg(f"{param} is mandatory in 'ibm_cf' section of the configuration", Color.RED))
        else:
            required_params[param] = cf_config[param]

    if required_params['endpoint']:
        if required_params['endpoint'] not in [endpoint_template.format(region) for region in CF_REGIONS]:
            print(color_msg(f"endpoint must be of the format {endpoint_template.replace('{}','<region>')}", Color.RED))
            required_params['endpoint'] = ARG_STATUS.INVALID
        else:
            region_provided = required_params['endpoint'][required_params['endpoint'].find('//') + 2:required_params['endpoint'].find('.')]

    api_key = _verify_cf_apikey_match()

    if iam_api_key:
        iamapikey_based_output = _verify_iamapikey_match(api_key)
        if iamapikey_based_output:
            return iamapikey_based_output

    elif not api_key:
        print(color_msg('Credentials of type IAmApiKey, or Cloud Foundry apiKey must be provided to configure Cloud Functions', Color.RED))

    if api_key and api_key != ARG_STATUS.INVALID:  # at this point iamapikey based configuration isn't possible
        output['ibm_cf']['api_key'] = api_key
        return output

    return reconfigure(base_config, output)


def verify_cf_api_key(api_key):
    """:returns the namespace's name and region that the provided cloud foundry api key matches.
        None is returned in response to an invalid api key. """

    api_key = str.encode(api_key)
    auth_token = base64.encodebytes(api_key).replace(b'\n', b'')
    iam_token = 'Basic %s' % auth_token.decode('UTF-8')

    for region in CF_REGIONS:
        conn = http.client.HTTPSConnection(f"{region}.functions.cloud.ibm.com")
        conn.request("GET", f"/api/v1/namespaces",
                     headers={'content-type': 'application/json', 'Authorization': iam_token})
        res = conn.getresponse()
        namespace = res.read().decode("utf-8")
        namespace = ast.literal_eval(namespace)  # turn string to represented datatype, e.g. '[]' to list

        if 'error' not in namespace:
            return {'namespace': namespace[0], 'region': region}

    print(color_msg(f"Invalid Cloud Foundry api key", Color.RED))


def reconfigure(base_config, output):
    """Directs the user to repeat the reconfiguration process and returns the recreated ibm_cf configuration"""

    iamapikey = base_config['ibm']['iam_api_key']

    should_reconfigure = get_confirmation(color_msg("Unable to configure the Cloud Functions segment due to invalid critical fields"
                                             "Would you like to reconfigure this segment?", Color.RED))['answer']
    if should_reconfigure:
        if not iamapikey or iamapikey == ARG_STATUS.INVALID:
            base_config['ibm']['iam_api_key'] = ''
            ApiKeyConfig(base_config).run()  # sets base_config's iam_api_key value

        base_config['ibm_cf']['namespace_id'] = ''
        CloudFunction(base_config).run()  # sets base_config's ibm_cf segment
        output['ibm_cf'] = base_config['ibm_cf']
        return output
