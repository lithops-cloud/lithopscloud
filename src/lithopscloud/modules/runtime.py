from typing import Any, Dict

import inquirer
from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator


class RuntimeConfig(ConfigBuilder):

    @update_decorator
    def run(self) -> Dict[str, Any]:
        question = [
            inquirer.Text(
                'name', message="Please provide a runtime image suitable for your current lithops version", default=self.defaults.get('runtime'))
        ]

        answers = inquirer.prompt(question, raise_keyboard_interrupt=True)

        return answers['name']


