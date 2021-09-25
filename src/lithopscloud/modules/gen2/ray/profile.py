from lithopscloud.modules.gen2.profile import ProfileConfig

class RayProfileConfig(ProfileConfig):
    
   def update_config(self, profile_name):
      if self.base_config.get('available_node_types'):
         for available_node_type in self.base_config['available_node_types']:
             self.base_config['available_node_types'][available_node_type][
                    'node_config']['instance_profile_name'] = profile_name
      else:
         self.base_config['available_node_types']['ray_head_default']['node_config']['instance_profile_name'] = profile_name
