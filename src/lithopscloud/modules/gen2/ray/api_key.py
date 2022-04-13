from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.config_builder import ConfigBuilder
from lithopscloud.modules.utils import verify_iam_api_key

class RayApiKeyConfig(ApiKeyConfig):

    def update_config(self, iam_api_key, compute_iam_endpoint=None, cos_iam_api_key=None):
        self.base_config['provider']['iam_api_key'] = iam_api_key
        self.base_config.pop('ibm', None)
        return self.base_config

    def verify(self, base_config):
        api_key = base_config['provider']['iam_api_key']

        verify_iam_api_key(None, api_key)
        ConfigBuilder.iam_api_key = api_key

        return base_config
