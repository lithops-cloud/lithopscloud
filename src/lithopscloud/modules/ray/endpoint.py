from lithopscloud.modules.endpoint import EndpointConfig
from typing import Any, Dict
from lithopscloud.modules.utils import get_region_by_endpoint

class RayEndpointConfig(EndpointConfig):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        self.iam_api_key = base_config['provider']['iam_api_key']
        super().__init__(base_config)

    def update_config(self, endpoint):
        self.base_config['provider']['endpoint'] = endpoint
        self.base_config['provider']['region'] = get_region_by_endpoint(endpoint)
