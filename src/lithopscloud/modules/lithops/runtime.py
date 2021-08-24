from lithopscloud.config_builder import ConfigBuilder
from typing import Any, Dict

from lithopscloud.modules.utils import free_dialog, get_option_from_list_alt as get_option_from_list

import ibm_boto3
from ibm_botocore.client import Config
from ibm_botocore.exceptions import ClientError
import inquirer


class RuntimeConfig(ConfigBuilder):
    
    def run(self) -> Dict[str, Any]:

        default_runtime_name = self.base_config['standalone'].get('runtime', 'ibmfunctions/lithops-cf-v385-1:2217b2')

        question = [
            inquirer.Text('name', message="Runtime name, either leave default or type a new one", default=default_runtime_name)
        ]

        answers = inquirer.prompt(question)
        self.base_config['standalone']['runtime'] = answers['name']

        return self.base_config
