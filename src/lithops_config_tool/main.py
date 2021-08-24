import os
import click
import yaml

from util_func import init_constants, update_config_file, get_option_from_list, get_resource_groups, \
    get_confirmation, init_iam_api_key, test_config_file
from cos import config_cos, verify_cos
from cloud_function import config_cf, verify_ibm_cf
from code_engine import config_ce, verify_code_engine

CONFIGURABLE_STORAGE = {'IBM COS': {'config_title': 'ibm_cos', 'config_func': config_cos, 'verify_func': verify_cos}}
CONFIGURABLE_COMPUTE = {
    'IBM Cloud Functions': {'config_title': 'ibm_cf', 'config_func': config_cf, 'verify_func': verify_code_engine},
    'Code Engine': {'config_title': 'code_engine', 'config_func': config_ce, 'verify_func': verify_ibm_cf}}


@click.command()
@click.option('--output_path', '-o', help="Path of user's output configuration file")
@click.option('--iam-api-key', '-k', help='IAM_API_KEY')
@click.option('--verify_file', '-v', help='Verify provided lithops config file instead of creating one.')
def config_generator(output_path, iam_api_key, verify_file):
    if not iam_api_key:
        iam_api_key = os.environ.get('RESEARCH_IAM_API_KEY')  # for testing purposes  RESEARCH_IAM_API_KEY
    init_iam_api_key(iam_api_key)

    available_resource_groups = get_resource_groups()
    chosen_resource_group = get_option_from_list('Please choose the resource group your resource instances belong to :',
                                                 list(available_resource_groups.keys()))['answer']
    resource_group_id = available_resource_groups[chosen_resource_group]

    if not output_path:  # user didn't provide a path to the output file via a flag
        output_path = '' if verify_file else input("Please indicate a path where your lithops config file "
                                                   "will be created: ")
    output_path = output_path if os.path.isfile(output_path) else \
        os.path.abspath(os.path.join(__file__, "../config_file.yaml"))

    init_constants(output_path, resource_group_id)

    if verify_file:
        if not os.path.isfile(output_path):
            print("a config file wasn't found at provided path")
            return
        else:
            scan_file(verify_file)
    else:
        selected_storage_backends = get_option_from_list('Please choose '
                                                         'one OR MORE storage backends you would like to configure:'
                                                         ,list(CONFIGURABLE_STORAGE.keys()), multiple_choice=True,
                                                         skip="Don't configure a storage backend")['answer']

        selected_storage_backends = selected_storage_backends if type(selected_storage_backends) is list else [
            selected_storage_backends]

        selected_compute_backends = get_option_from_list('Please choose '
                                                         'one OR MORE compute backends you would like to configure:'
                                                         , list(CONFIGURABLE_COMPUTE.keys()), multiple_choice=True,
                                                         skip="Don't configure a compute backend")['answer']
        selected_compute_backends = selected_compute_backends if type(selected_compute_backends) is list else [
            selected_compute_backends]

        # execute configuring functions of selected backends:
        for storage in selected_storage_backends:
            CONFIGURABLE_STORAGE[storage]['config_func']()
        for compute in selected_compute_backends:
            CONFIGURABLE_COMPUTE[compute]['config_func']()

        default_storage_backend = get_option_from_list('Please select a default storage backend:',
                                                       selected_storage_backends)['answer'] if selected_storage_backends else selected_storage_backends
        default_compute_backends = get_option_from_list('Please select a default compute backend:',
                                                        selected_compute_backends)['answer'] if selected_compute_backends else selected_compute_backends

        if default_storage_backend:
            update_config_file(f"""lithops:
                                    storage_backend: {CONFIGURABLE_STORAGE[default_storage_backend]['config_title']}""")

        if default_compute_backends:
            update_config_file(f"""lithops:
                                    backend: {CONFIGURABLE_COMPUTE[default_compute_backends]['config_title']}""")

        update_config_file(f"""ibm:
                                iam_api_key: {iam_api_key}""")

        print('------Lithops config file was configured successfully------')

        run_test = get_confirmation("Would you like to verify your lithops configuration file "
                                    "is configured correctly? ")['answer']
        if run_test:
            test_config_file()


def scan_file(verify_file):

    with open(verify_file) as config_file:
        config = yaml.safe_load(config_file)
    headers = list(config.keys())

    for storage_backend in CONFIGURABLE_STORAGE:
        if CONFIGURABLE_STORAGE[storage_backend]['config_title'] in headers:
            CONFIGURABLE_STORAGE[storage_backend]['verify_func'](config)

    for compute_backend in CONFIGURABLE_COMPUTE:
        if CONFIGURABLE_COMPUTE[compute_backend]['config_title'] in headers:
            CONFIGURABLE_COMPUTE[compute_backend]['verify_func'](config)


if __name__ == "__main__":
    config_generator()
