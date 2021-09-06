from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list, find_default


class ProfileConfig(ConfigBuilder):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    @update_decorator
    def run(self) -> Dict[str, Any]:

        @spinner
        def get_instance_profile_objects():
            return self.ibm_vpc_client.list_instance_profiles().get_result()['profiles']

        instance_profile_objects = get_instance_profile_objects()

        default = find_default(
            self.base_config, instance_profile_objects, name='instance_profile_name')
        instance_profile = get_option_from_list(
            'Carefully choose instance profile, please refer to https://cloud.ibm.com/docs/vpc?topic=vpc-profiles', instance_profile_objects, default=default)

        
        return instance_profile['name']