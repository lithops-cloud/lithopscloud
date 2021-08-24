from lithopscloud.modules.ssh_key import SshKeyConfig

class LithopsSshKeyConfig(SshKeyConfig):

    def update_config(self, ssh_key_id, ssh_key_path, ssh_user):
        self.base_config['ibm_vpc']['key_id'] = ssh_key_id
        self.base_config['ibm_vpc']['ssh_key_filename'] = ssh_key_path
        self.base_config['ibm_vpc']['ssh_user'] = 'root'
