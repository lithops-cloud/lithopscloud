import sys

import ibm_cloud_sdk_core
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services import IamIdentityV1
from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list, color_msg, Color
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

        verify_iam_api_key(api_key)
        ConfigBuilder.iam_api_key = api_key
        return api_key

    def update_config(self, iam_api_key) -> Dict[str, Any]:
        self.base_config['ibm'] = {'iam_api_key': iam_api_key}
        return self.base_config


def verify_iam_api_key(apikey):
    """Terminates the config tool if no IAM_API_KEY matching the provided value exists"""

    iam_identity_service = IamIdentityV1(authenticator=IAMAuthenticator(apikey))
    try:
        iam_identity_service.get_api_keys_details(iam_api_key=apikey)
    except ibm_cloud_sdk_core.api_exception.ApiException:
        print(color_msg("No ApiKey matching the given value was found.", color=Color.RED))
        sys.exit()
    except Exception as e:
        print(color_msg(f'ApiKey Error : {e}', color=Color.RED))
        sys.exit()
