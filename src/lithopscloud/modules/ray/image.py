from lithopscloud.modules.image import ImageConfig

class RayImageConfig(ImageConfig):
    
   def update_config(self, image_id):
      if self.base_config.get('available_node_types'):
         for available_node_type in self.base_config['available_node_types']:
            self.base_config['available_node_types'][available_node_type]['node_config']['image_id'] = image_id
      else:
         self.base_config['available_node_types']['ray_head_default']['node_config']['image_id'] = image_id
