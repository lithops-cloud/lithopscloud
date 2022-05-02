from typing import Any, Dict

from lithopscloud.modules.gen2.image import ImageConfig
from lithopscloud.modules.utils import find_obj, find_default

class LithopsImageConfig(ImageConfig):
   
   def __init__(self, base_config: Dict[str, Any]) -> None:
      super().__init__(base_config)
      self.defaults['image_id'] = base_config['ibm_vpc'].get('image_id')
    
   def update_config(self, image_id, minimum_provisioned_size, custom_image):
      self.base_config['ibm_vpc']['image_id'] = image_id
      self.base_config['ibm_vpc']['boot_volume_capacity'] = minimum_provisioned_size
