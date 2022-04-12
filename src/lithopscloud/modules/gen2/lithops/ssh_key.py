from typing import Any, Dict

from lithopscloud.modules.gen2.ssh_key import SshKeyConfig


class LithopsSshKeyConfig(SshKeyConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['key_id'] = base_config['ibm_vpc'].get('key_id')
        self.defaults['ssh_key_filename'] = base_config['ibm_vpc'].get(
            'ssh_key_filename')
        self.defaults['ssh_user'] = base_config['ibm_vpc'].get('ssh_user')

    def update_config(self, ssh_key_id, ssh_key_path, ssh_user):
        self.base_config['ibm_vpc']['key_id'] = ssh_key_id
        self.base_config['ibm_vpc']['ssh_key_filename'] = ssh_key_path
        self.base_config['ibm_vpc']['ssh_user'] = ssh_user
