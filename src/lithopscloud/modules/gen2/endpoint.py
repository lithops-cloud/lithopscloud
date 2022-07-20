from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list


class EndpointConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        
    @spinner
    def _get_regions_objects(self):
        return ConfigBuilder.ibm_vpc_client.list_regions().get_result()['regions']
        
    @update_decorator
    def run(self) -> Dict[str, Any]:

        regions_objects = self._get_regions_objects()
        
        default = self.defaults.get('region')
        region_obj = get_option_from_list("Choose region", regions_objects, default = default)

        # update global ibm_vpc_client to selected endpoint
        ConfigBuilder.ibm_vpc_client.set_service_url(region_obj['endpoint'] + '/v1')
        ConfigBuilder.region = region_obj['name']
        
        return region_obj['endpoint']
    
    @update_decorator
    def create_default(self):
        # update global ibm_vpc_client to selected endpoint
        regions_objects = self._get_regions_objects()
        
        # currently hardcoded for us-south
        region_obj = next((r for r in regions_objects if r['name'] == 'us-south'), None)
        
        ConfigBuilder.ibm_vpc_client.set_service_url(region_obj['endpoint'] + '/v1')
        ConfigBuilder.region = region_obj['name']
        
        return region_obj['endpoint']
