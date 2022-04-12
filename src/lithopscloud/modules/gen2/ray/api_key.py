from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.api_key import ApiKeyConfig

class RayApiKeyConfig(ApiKeyConfig):

    def update_config(self, iam_api_key, compute_iam_endpoint=None, cos_iam_api_key=None):
        self.base_config['provider']['iam_api_key'] = iam_api_key
        self.base_config.pop('ibm', None)
        return self.base_config
