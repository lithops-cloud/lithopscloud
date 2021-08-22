import os
import click
from util_func import init_constants, update_config_file, get_option_from_list, get_resource_groups,\
    get_confirmation, free_dialog, init_iam_api_key,test_config_file
from cos import config_cos
from cloud_function import config_cf
from code_engine import config_ce

CONFIGURABLE_STORAGE = {'IBM COS': {'config_title': 'ibm_cos', 'config_func': config_cos}}
CONFIGURABLE_COMPUTE = {'IBM Cloud Functions': {'config_title': 'ibm_cf', 'config_func': config_cf},
                        'Code Engine': {'config_title': 'code_engine', 'config_func': config_ce}}

@click.command()
@click.option('--output_path', '-o', help="Path of user's output configuration file")
@click.option('--iam-api-key','-k', help='IAM_API_KEY')
def config_generator(output_path, iam_api_key):
    if not iam_api_key:
        iam_api_key = os.environ.get('IAM_API_KEY')  # for testing purposes
    init_iam_api_key(iam_api_key)

    if not output_path:
        output_path = free_dialog("Please indicate a path where your lithops config file will be created")['answer']
    output_path = output_path if os.path.isfile(output_path) else \
        os.path.abspath(os.path.join(__file__, "../config_file.yaml"))

    available_resource_groups = get_resource_groups()
    chosen_resource_group = get_option_from_list('Please choose the resource group your resource instances belong to :',
                                                 list(available_resource_groups.keys()))['answer']
    resource_group_id = available_resource_groups[chosen_resource_group]

    init_constants(output_path,resource_group_id)

    selected_storage_backends = get_option_from_list('Please choose one OR MORE storage backends you would like to '
                                                     'configure:',
                                                     list(CONFIGURABLE_STORAGE.keys()), multiple_choice=True)['answer']
    selected_storage_backends = selected_storage_backends if type(selected_storage_backends) is list else [selected_storage_backends]

    selected_compute_backends = get_option_from_list('Please choose one OR MORE compute backends you would like to '
                                                     'configure:',
                                                     list(CONFIGURABLE_COMPUTE.keys()), multiple_choice=True)['answer']
    selected_compute_backends = selected_compute_backends if type(selected_compute_backends) is list else [selected_compute_backends]

    # execute configuring functions of selected backends:
    for storage in selected_storage_backends:
        CONFIGURABLE_STORAGE[storage]['config_func']()
    for compute in selected_compute_backends:
        CONFIGURABLE_COMPUTE[compute]['config_func']()

    default_storage_backend = get_option_from_list('Please select a default storage backend:',
                                                   selected_storage_backends)['answer']
    default_compute_backends = get_option_from_list('Please select a default compute backend:',
                                                    selected_compute_backends)['answer']

    update_config_file(f"""lithops:
                            storage_backend: {CONFIGURABLE_STORAGE[default_storage_backend]['config_title']}
                            backend: {CONFIGURABLE_COMPUTE[default_compute_backends]['config_title']}""")

    update_config_file(f"""ibm:
                            iam_api_key: {iam_api_key}""")

    print('------Lithops config file was configured successfully------')

    run_test = get_confirmation("Would you like to verify your lithops configuration file is configured correctly? ")['answer']
    if run_test:
        test_config_file()


if __name__ == "__main__":
    config_generator()




