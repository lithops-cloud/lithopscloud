from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator
from typing import Any, Dict
from lithopscloud.modules.utils import find_name_id, find_default


class ImageConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    @update_decorator
    def run(self) -> Dict[str, Any]:
        image_objects = self.ibm_vpc_client.list_images().get_result()['images']        

        default = find_default(self.defaults, image_objects, id='image_id') or 'ibm-ubuntu-20-04-minimal-amd64-2'
        _, image_id = find_name_id(image_objects, 'Please choose \033[92mUbuntu\033[0m 20.04 VM image, currently only Ubuntu supported', default=default)
        
        return image_id