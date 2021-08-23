from lithopscloud.config_builder import ConfigBuilder, update_decorator
from typing import Any, Dict
from lithopscloud.modules.utils import find_default, get_option_from_list


class EndpointConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    @update_decorator
    def run(self) -> Dict[str, Any]:
        # find region and endpoint
        endpoint = None
        regions_objects = self.ibm_vpc_client.list_regions().get_result()['regions']
        
        default = find_default(self.base_config, regions_objects, name='region')
        region_obj = get_option_from_list("Choose region", regions_objects, default = default)

        # update ibm_vpc_client to selected endpoint
        ConfigBuilder.ibm_vpc_client.set_service_url(region_obj['endpoint'] + '/v1')
        
        return region_obj['endpoint']
