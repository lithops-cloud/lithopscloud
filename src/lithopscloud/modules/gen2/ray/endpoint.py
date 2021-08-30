from lithopscloud.modules.gen2.endpoint import EndpointConfig
from typing import Any, Dict
from lithopscloud.modules.utils import get_region_by_endpoint

class RayEndpointConfig(EndpointConfig):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

        base_endpoint = self.base_config['provider'].get('endpoint')
        self.defaults['region'] = get_region_by_endpoint(base_endpoint) if base_endpoint else None

    def update_config(self, endpoint):
        self.base_config['provider']['endpoint'] = endpoint
        self.base_config['provider']['region'] = get_region_by_endpoint(endpoint)
