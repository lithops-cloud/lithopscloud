from typing import Any, Dict

import inquirer
from lithopscloud.modules.config_builder import ConfigBuilder


class RuntimeConfig(ConfigBuilder):

    def run(self) -> Dict[str, Any]:

        default_runtime_name = self.base_config['standalone'].get(
            'runtime', 'ibmfunctions/lithops-cf-v385-1:2217b2')

        question = [
            inquirer.Text(
                'name', message="Runtime name, either leave default or type a new one", default=default_runtime_name)
        ]

        answers = inquirer.prompt(question, raise_keyboard_interrupt=True)
        self.base_config['standalone']['runtime'] = answers['name']

        return self.base_config
