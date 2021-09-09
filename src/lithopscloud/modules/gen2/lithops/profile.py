from typing import Any, Dict

from lithopscloud.modules.gen2.profile import ProfileConfig


class LithopsProfileConfig(ProfileConfig):
   
   def __init__(self, base_config: Dict[str, Any]) -> None:
      super().__init__(base_config)
      self.defaults['profile_name'] = base_config['ibm_vpc'].get('profile_name')
    
   def update_config(self, profile_name):
      self.base_config['ibm_vpc']['profile_name'] = profile_name
