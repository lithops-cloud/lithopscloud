from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator, spinner
from typing import Any, Dict
from lithopscloud.modules.utils import get_option_from_list, find_default, find_obj


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
    
    @update_decorator
    def verify(self, base_config):
        profile_name = self.defaults['profile_name']
        instance_profile_objects = self.ibm_vpc_client.list_instance_profiles().get_result()['profiles']
        profile = find_obj(instance_profile_objects, 'dummy', obj_name=profile_name)
        if not profile:
            raise Exception(f'Specified profile {profile_name} not found in the profile list {instance_profile_objects}')
        return profile_name

    @update_decorator    
    def create_default(self):
        return 'bx2-2x8'
