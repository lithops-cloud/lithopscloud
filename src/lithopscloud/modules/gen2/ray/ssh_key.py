from lithopscloud.modules.gen2.ssh_key import SshKeyConfig

class RaySshKeyConfig(SshKeyConfig):

    def update_config(self, ssh_key_id, ssh_key_path, ssh_user):        
        self.base_config['auth']['ssh_private_key'] = ssh_key_path
        self.base_config['auth']['ssh_user'] = ssh_user

        if self.base_config.get('available_node_types'):
            for available_node_type in self.base_config['available_node_types']:
                self.base_config['available_node_types'][available_node_type]['node_config']['key_id'] = ssh_key_id
        else:
            self.base_config['available_node_types'] = {'ray_head_default': {'node_config': {'key_id': ssh_key_id}}}
