import os
from typing import Any, Dict

import inquirer
from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator, spinner
from lithopscloud.modules.utils import (find_default, find_name_id,
                                        validate_exists, validate_not_empty)


def register_ssh_key(ibm_vpc_client, config):
    if config.get('ibm_vpc'):
        resource_group_id = config['ibm_vpc']['resource_group_id']
    else:
        for available_node_type in config['available_node_types']:
            resource_group_id = config['available_node_types'][available_node_type]['node_config']['resource_group_id']
            break

    questions = [
        inquirer.Text(
            'keyname', message='Please specify a name for the new key', validate=validate_not_empty)
    ]
    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
    keyname = answers['keyname']

    EXISTING_CONTENTS = 'Paste existing public key contents'
    EXISTING_PATH = 'Provide path to existing public key'
    GENERATE_NEW = 'Generate new public key'

    questions = [
        inquirer.List('answer',
                      message="Please choose",
                      choices=[EXISTING_PATH, EXISTING_CONTENTS, GENERATE_NEW]
                      )]

    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
    ssh_key_data = ""
    ssh_key_path = None
    if answers["answer"] == EXISTING_CONTENTS:
        print("Registering from file contents")
        ssh_key_data = input(
            "[\033[33m?\033[0m] Please paste the contents of your public ssh key. It should start with ssh-rsa: ")
    elif answers["answer"] == EXISTING_PATH:
        print("Register in vpc existing key from path")
        questions = [
            inquirer.Text(
                "public_key_path", message='Please paste path to your \033[92mpublic\033[0m ssh key', validate=validate_exists)
        ]
        answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)

        with open(answers["public_key_path"], 'r') as file:
            ssh_key_data = file.read()
    else:
        filename = f"id.rsa.{keyname}"
        os.system(f'ssh-keygen -b 2048 -t rsa -f {filename} -q -N ""')
        print(f"\n\n\033[92mSSH key pair been generated\n")
        print(f"private key: {os.path.abspath(filename)}")
        print(f"public key {os.path.abspath(filename)}.pub\033[0m")
        with open(f"{filename}.pub", 'r') as file:
            ssh_key_data = file.read()
        ssh_key_path = os.path.abspath(filename)

    response = ibm_vpc_client.create_key(public_key=ssh_key_data, name=keyname, resource_group={
                                         "id": resource_group_id}, type='rsa')

    print(f"\033[92mnew SSH key {keyname} been registered in vpc\033[0m")

    result = response.get_result()
    return result['name'], result['id'], ssh_key_path


DEPENDENCIES = {'ibm_vpc': {'resource_group_id': None}}


class SshKeyConfig(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.base_config = base_config

    @update_decorator
    def run(self) -> Dict[str, Any]:
        @spinner
        def get_ssh_key_objects():
            return self.ibm_vpc_client.list_keys().get_result()['keys']

        ssh_key_objects = get_ssh_key_objects()

        CREATE_NEW_SSH_KEY = "Register new SSH key in IBM VPC"

        default = find_default(self.defaults, ssh_key_objects, id='key_id')
        ssh_key_name, ssh_key_id = find_name_id(
            ssh_key_objects, 'Choose ssh key', do_nothing=CREATE_NEW_SSH_KEY, default=default)

        ssh_key_path = None
        if not ssh_key_name:
            ssh_key_name, ssh_key_id, ssh_key_path = register_ssh_key(
                self.ibm_vpc_client, self.base_config)

        if not ssh_key_path:
            questions = [
                inquirer.Text(
                    "private_key_path", message=f'Please paste path to \033[92mprivate\033[0m ssh key associated with selected public key {ssh_key_name}', validate=validate_exists, default=self.defaults.get('ssh_key_filename') or "~/.ssh/id_rsa")
            ]
            answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
            ssh_key_path = os.path.abspath(
                os.path.expanduser(answers["private_key_path"]))

        # currently the user is hardcoded to root
        return ssh_key_id, ssh_key_path, 'root'
