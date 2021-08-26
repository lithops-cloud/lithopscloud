from typing import Any, Dict

from lithopscloud.modules.gen2.endpoint import EndpointConfig
from lithopscloud.modules.utils import get_region_by_endpoint


class LithopsEndpointConfig(EndpointConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

        base_endpoint = self.base_config['ibm_vpc'].get(
            'endpoint') if self.base_config.setdefault('ibm_vpc', {}) else None
        self.defaults['region'] = get_region_by_endpoint(
            base_endpoint) if base_endpoint else None

    def update_config(self, endpoint):
        self.base_config['ibm_vpc']['endpoint'] = endpoint
