from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list
import inquirer


class ApiKeyConfig(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['api_key'] = self.base_config['ibm']['iam_api_key'] if self.base_config.setdefault(
            'ibm', {}) else None

    @update_decorator
    def run(self, api_key=None) -> Dict[str, Any]:
        if not api_key:
            default = self.defaults.get('api_key')

            questions = [
                inquirer.Text(
                    "iam_api_key", message='Please provide \033[92mIBM API KEY \033[0m', default=default)
            ]

            answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
            api_key = answers["iam_api_key"]

        ConfigBuilder.iam_api_key = api_key
        return api_key

    def update_config(self, iam_api_key) -> Dict[str, Any]:
        self.base_config['ibm'] = {'iam_api_key': iam_api_key}
        return self.base_config
