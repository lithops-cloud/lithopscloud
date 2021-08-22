from lithopscloud.modules.image import ImageConfig

class LithopsImageConfig(ImageConfig):
    
     def update_config(self, image_id):
        self.base_config['ibm_vpc']['image_id'] = image_id
