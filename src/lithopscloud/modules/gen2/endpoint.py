from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list


class EndpointConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    @update_decorator
    def run(self) -> Dict[str, Any]:

        @spinner
        def get_regions_objects():
            return self.ibm_vpc_client.list_regions().get_result()['regions']

        regions_objects = get_regions_objects()
        
        default = self.defaults.get('region')
        region_obj = get_option_from_list("Choose region", regions_objects, default = default)

        # update global ibm_vpc_client to selected endpoint
        ConfigBuilder.ibm_vpc_client.set_service_url(region_obj['endpoint'] + '/v1')
        
        return region_obj['endpoint']
