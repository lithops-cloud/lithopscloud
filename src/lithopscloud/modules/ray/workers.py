from lithopscloud.config_builder import update_decorator
from lithopscloud.modules.endpoint import EndpointConfig
from lithopscloud.modules.utils import find_default, get_option_from_list
from typing import Any, Dict

import inquirer
import re

class WorkersConfig(EndpointConfig):
    
    def run(self) -> Dict[str, Any]:
        default_cluster_name = self.base_config.get('cluster_name', 'default')
        default_min_workers = self.base_config.get('min_workers', '0')
        default_max_workers = self.base_config.get('max_workers', default_min_workers)

        question = [
            inquirer.Text('name', message="Cluster name, either leave default or type a new one", default=default_cluster_name),
            inquirer.Text('min_workers', message="Minimum number of worker nodes", default=default_min_workers, validate=lambda _, x: re.match('^[+]?[0-9]+$', x)),
            inquirer.Text('max_workers', message="Maximum number of worker nodes", default=default_max_workers, validate=lambda answers, x: re.match('^[+]?[0-9]+$', x) and int(x) >= int(answers['min_workers']))
        ]

        answers = inquirer.prompt(question)
        self.base_config['cluster_name'] = answers['name']
        self.base_config['max_workers'] = int(answers['max_workers'])

        
        instance_profile_objects = self.ibm_vpc_client.list_instance_profiles().get_result()['profiles']
    
        default = find_default(self.base_config, instance_profile_objects, name='instance_profile_name')
        instance_profile = get_option_from_list('Carefully choose instance profile, please refer to https://cloud.ibm.com/docs/vpc?topic=vpc-profiles', instance_profile_objects, default=default)
        
        if self.base_config.get('available_node_types'):
            for available_node_type in self.base_config['available_node_types']:
                self.base_config['available_node_types'][available_node_type]['min_workers'] = int(answers['min_workers'])
                self.base_config['available_node_types'][available_node_type]['max_workers'] = int(answers['max_workers'])
                self.base_config['available_node_types'][available_node_type]['instance_profile_name'] = instance_profile['name']
        else:
            self.base_config['available_node_types']['ray_head_default']['min_workers'] = int(answers['min_workers'])
            self.base_config['available_node_types']['ray_head_default']['max_workers'] = int(answers['max_workers'])
            self.base_config['available_node_types']['ray_head_default']['instance_profile_name'] = instance_profile['name']

        return self.base_config
