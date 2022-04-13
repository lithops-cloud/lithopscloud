from typing import Any, Dict
from lithopscloud.modules.gen2.profile import ProfileConfig

class RayProfileConfig(ProfileConfig):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        if self.base_config.get('available_node_types'):
            for available_node_type in self.base_config['available_node_types']:
                self.defaults['profile_name'] = self.base_config['available_node_types'][available_node_type][
                    'node_config'].get('instance_profile_name')
                break
    
    def update_config(self, profile_name):

        # cpu number based on profile
        cpu_num = int(profile_name.split('-')[1].split('x')[0])

        if self.base_config.get('available_node_types'):
            for available_node_type in self.base_config['available_node_types']:
                self.base_config['available_node_types'][available_node_type][
                    'node_config']['instance_profile_name'] = profile_name
                self.base_config['available_node_types'][available_node_type]['resources']['CPU'] = cpu_num
        else:
            self.base_config['available_node_types']['ray_head_default']['node_config']['instance_profile_name'] = profile_name
            self.base_config['available_node_types']['ray_head_default']['resources']['CPU'] = cpu_num

