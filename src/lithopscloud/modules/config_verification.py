import importlib
import os
import yaml
from inquirer import errors
from lithopscloud.modules.api_key import verify_iam_api_key
from lithopscloud.modules.utils import color_msg, Color, ARG_STATUS, MSG_STATUS, free_dialog, inquire_user

# TODO: change ibm_cos path to cos after cos-package name changes to cos
CONFIGURABLE_STORAGE = [{'config_title': 'ibm_cos', 'path': 'cos-package'},
                        {'config_title': 'localhost', 'path': 'local_host'}]
CONFIGURABLE_COMPUTE = [{'config_title': 'ibm_cf', 'path': 'cloud_functions'},
                        {'config_title': 'code_engine', 'path': 'code_engine'},
                        {'config_title': 'localhost', 'path': 'local_host'}]


def verify_config_file(config_file, output_file):
    """executed via cli flag 'verify-config', this function outputs error messages based on lacking or invalid values
       of the provided lithops config file.  """

    verify_file_path(config_file)
    with open(config_file) as f:
        base_config = yaml.safe_load(f)

    verify_iamapikey(base_config)  # verify once a commonly shared resource in various backends

    chosen_compute, chosen_storage = get_backends(base_config)
    output_config = {'lithops': base_config['lithops']}

    storage_path = next((x['path'] for x in CONFIGURABLE_STORAGE if x['config_title'] == chosen_storage))
    compute_path = next((x['path'] for x in CONFIGURABLE_COMPUTE if x['config_title'] == chosen_compute))

    for path in [storage_path, compute_path]:
        verify_module = importlib.import_module(f"lithopscloud.modules.{path}.verify")
        verify_func = verify_module.__getattribute__('verify')
        res = verify_func(base_config)
        if res:
            output_config.update(res)
        else:
            print(color_msg(f"{MSG_STATUS.ERROR.value} Couldn't produce a valid lithops config file from input", Color.RED))
            exit(1)

    with open(output_file, 'w') as outfile:
        yaml.dump(output_config, outfile, default_flow_style=False)

    print("\n\n=================================================")
    print(color_msg(f"Extracted config file: {output_file}", color=Color.LIGHTGREEN))
    print("=================================================")


def get_backends(base_config):
    if base_config.get('lithops'):
        if base_config['lithops'].get('backend'):
            chosen_compute = base_config['lithops'].get('backend')
            if chosen_compute not in [compute['config_title'] for compute in CONFIGURABLE_COMPUTE]:
                print(color_msg(f"{MSG_STATUS.ERROR.value} chosen compute backend isn't configurable at this point in time."
                                f"\nAvailable compute backends: {[backend['config_title'] for backend in CONFIGURABLE_COMPUTE]}",Color.RED))
                exit(1)
        else:
            print(color_msg("Missing chosen compute backend under lithops->backend",Color.RED))
            chosen_compute = get_missing_backend(base_config, CONFIGURABLE_COMPUTE)

        if base_config['lithops'].get('storage'):
            chosen_storage = base_config['lithops'].get('storage')
            if chosen_storage not in [storage['config_title'] for storage in CONFIGURABLE_STORAGE]:
                print(color_msg(f"{MSG_STATUS.ERROR.value} chosen storage backend isn't configurable at this point in time."
                                f"\nAvailable storage backends: {[backend['config_title'] for backend in CONFIGURABLE_STORAGE]}",Color.RED))
                exit(1)
        else:
            print(color_msg("Missing chosen storage backend under lithops->storage", Color.RED))
            chosen_storage = get_missing_backend(base_config, CONFIGURABLE_STORAGE)
    else:
        base_config['lithops'] = {'backend': '', 'storage': ''}
        chosen_compute = get_missing_backend(base_config, CONFIGURABLE_COMPUTE)
        chosen_storage = get_missing_backend(base_config, CONFIGURABLE_STORAGE)

    return chosen_compute, chosen_storage


def get_missing_backend(config_data, backend_list):
    """returns the missing compute/storage backend title, the user would like to verify in the verification process."""

    input_file_backends = {backend['config_title'] for backend in backend_list}.intersection(config_data.keys())
    backend_type = 'computation' if backend_list == CONFIGURABLE_COMPUTE else 'storage'
    backend_header = 'backend' if backend_list == CONFIGURABLE_COMPUTE else 'storage'

    if len(input_file_backends) > 1:
        chosen_backend = inquire_user("please choose a single computation backend", input_file_backends,
                                      handle_strings=True)
        config_data['lithops'].update({f'{backend_header}': chosen_backend})
    elif len(input_file_backends) == 1:
        chosen_backend = next((x for x in input_file_backends))  # set: {} doesn't support '[]' get item operation
        config_data['lithops'].update({f'{backend_header}': chosen_backend})
    else:
        print(color_msg(f"[Error] No supported {backend_type} backends were found in the config file", Color.RED))
        exit(1)
    return chosen_backend


def verify_iamapikey(base_config):
    if 'ibm' in base_config and base_config['ibm'] and 'iam_api_key' in base_config['ibm']:
        try:
            verify_iam_api_key('', base_config['ibm']['iam_api_key'])
        except errors.ValidationError:
            base_config['ibm']['iam_api_key'] = ARG_STATUS.INVALID
            print(color_msg('No IAmApiKey matching the given value was found', Color.RED))
    else:
        base_config['ibm'] = {'iam_api_key': ''}


def verify_file_path(config_file):
    def _is_valid_input_path(path):
        if not os.path.isfile(path):
            print(color_msg(f"\nError - Path: '{path}' doesn't point to a file. ", color=Color.RED))
            return False
        return True

    while True:
        if _is_valid_input_path(config_file):
            return config_file
        else:
            config_file = free_dialog('Provide a path to an existing config file')['answer']


