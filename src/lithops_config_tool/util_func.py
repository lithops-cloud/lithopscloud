import os
import platform
import subprocess

import inquirer
import yaml
from ibm_platform_services import ResourceControllerV2, ResourceManagerV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import IAMTokenManager

OUTPUT_FILE_PATH = ''
IAM_API_KEY = ''
RESOURCE_GROUP_ID = ''


def init_constants(output_file_path, resource_group_id):
    global OUTPUT_FILE_PATH, RESOURCE_GROUP_ID
    OUTPUT_FILE_PATH = output_file_path
    RESOURCE_GROUP_ID = resource_group_id


def init_iam_api_key(iam_api_key):
    global IAM_API_KEY
    IAM_API_KEY = iam_api_key


def get_iam_api_key():
    return IAM_API_KEY


def get_resource_group_id():
    return RESOURCE_GROUP_ID


def get_resource_instances():
    """return the entire resource list (except cloud foundry based name-spaces)
    belonging to a given resource group."""
    authenticator = IAMAuthenticator(IAM_API_KEY)
    resource_controller_service = ResourceControllerV2(authenticator=authenticator)
    return resource_controller_service.list_resource_instances(resource_group_id=RESOURCE_GROUP_ID).get_result()


def get_oauth_token():
    iam_token_manager = IAMTokenManager(apikey=IAM_API_KEY)
    return iam_token_manager.get_token()


def get_resource_groups():
    """returns list of resource groups. if user hasn't created any, the 'Default' group is returned. """
    group = {}
    authenticator = IAMAuthenticator(IAM_API_KEY)
    service_client = ResourceManagerV2(authenticator=authenticator)
    resource_group_list = service_client.list_resource_groups()

    for resource in resource_group_list.result['resources']:
        group[resource['name']] = [resource['id']]

    return group

    # return [resource_groups['name'] for resource_groups in resource_group_list.result['resources']]


def get_option_from_list(msg, choices, instance_to_create=None, default=None, multiple_choice=False):
    """prompt options to user and returns user choice.
      :param str instance_to_create: when initialized to true adds a 'create' option that allows the user
                            to create an instance rather than to opt for one of the options."""
    if len(choices) == 0:
        raise Exception(f"No options were found to satisfy the following request: {msg}")

    if len(choices) == 1:
        print(f'''A single option was found in response to the request: "{msg}".
              \n--*-- {choices[0]} was automatically chosen --*--\n''')
        return {'answer': choices[0]}

    if instance_to_create:
        choices.append(f'Create a new {instance_to_create}')

    questions = [
        inquirer.List('answer',
                      message=msg,
                      choices=choices,
                      default=default,
                      )] if not multiple_choice else \
        [inquirer.Checkbox('answer',
                           message=msg,
                           choices=choices,
                           default=default,
                           )]

    answers = inquirer.prompt(questions)

    while not answers['answer'] and multiple_choice:
        print("You must choose at least one option.\n"
              "To pick an option please use the right arrow key '->' to select and the left arrow key '<-' to cancel.")
        answers = inquirer.prompt(questions)

    return answers


def get_confirmation(msg, default=None):
    questions = [
        inquirer.Confirm('answer',
                         message=msg,
                         default=default,
                         ), ]
    answer = inquirer.prompt(questions)

    return answer


def free_dialog(msg, default=None):
    question = [
        inquirer.Text('answer',
                      message=msg,
                      default=default)]
    answer = inquirer.prompt(question)
    return answer


def update_config_file(data):
    """Update the fields of the lithops config file using provided data """
    try:
        with open(OUTPUT_FILE_PATH) as config_file:
            config = yaml.safe_load(config_file)
    except:  # config file is yet to be created
        config = {}

    config.update(yaml.safe_load(data))

    with open(OUTPUT_FILE_PATH, 'w') as config_file:
        config_file.write(yaml.dump(config, sort_keys=False))


def test_config_file():
    """testing the created config file with a simple test  """
    args = f"python3 -m lithops.tests.tests_main -t test_call_async -c {OUTPUT_FILE_PATH}".split()
    process = subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=1)  # force the process not to buffer the output.
    for line in iter(process.stdout.readline, b''):
        print(line.decode())
    process.stdout.close()
    process.wait()


def install_ibmcloud_cli():
    """installs ibmcloud stand alone cli in case it isn't already installed.
     stream.read guarantees process won't continue until current execution is finished. """

    stream = os.popen('ibmcloud --version')
    if stream.read():
        print("ibmcloud cli is already installed.")

    else:
        print("installing ibmcloud cli...")
        plt = platform.system()
        if 'linux' in plt:
            pass
        if plt == 'Darwin':
            stream = os.popen('curl -fsSL https://clis.cloud.ibm.com/install/osx | sh')
        elif plt == 'Linux':
            stream = os.popen('curl -fsSL https://clis.cloud.ibm.com/install/linux | sh')
        else:  # windows
            stream = os.popen(
                'iex(New-Object Net.WebClient).DownloadString("https://clis.cloud.ibm.com/install/powershell")')
        print(stream.read())  # allow user to interact with cli


def install_ibmcloud_plugin(plugin):
    """installs given ibmcloud plugin in case it isn't already installed"""
    plugins = {
        'IBM COS': {'command': 'cos', 'plugin_name': 'cloud-object-storage'},
        'IBM Cloud Functions': {'command': 'cloud-functions', 'plugin_name': 'cloud-functions'},
        'Code Engine': {'command': 'code-engine', 'plugin_name': 'code-engine'},
    }

    if plugin in plugins:
        stream = os.popen(f'ibmcloud {plugins[plugin]["command"]}')
        if stream.read():
            print(f'{plugins[plugin]["plugin_name"]} plugin for ibmcloud cli is already installed.')

        else:
            print(f'installing {plugins[plugin]["plugin_name"]} plugin for ibmcloud cli...')
            stream = os.popen(f'ibmcloud plugin install {plugins[plugin]["plugin_name"]}')
            print(stream.read())
    else:
        raise Exception("Unrecognized plugin")
