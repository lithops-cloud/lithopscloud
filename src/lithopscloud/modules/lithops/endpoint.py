from lithopscloud.modules.endpoint import EndpointConfig
from typing import Any, Dict

class LithopsEndpointConfig(EndpointConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        self.iam_api_key = base_config['ibm']['iam_api_key']
        super().__init__(base_config)
    
    def update_config(self, endpoint):
        self.base_config['ibm_vpc']['endpoint'] = endpoint
        
        
