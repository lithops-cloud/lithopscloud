from lithopscloud.modules.vpc import VPCConfig
from typing import Any, Dict


class RayVPCConfig(VPCConfig):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

        self.vpc_name = 'ray-cluster-vpc'
        self.sg_rules = {'outbound_tcp_all': 'selected security group is missing rule permitting outbound TCP access\n', 'outbound_udp_all': 'selected security group is missing rule permitting outbound UDP access\n', 'inbound_tcp_sg': 'selected security group is missing rule permiting inbound tcp traffic inside selected security group\n', 'inbound_tcp_22': 'selected security group is missing rule permiting inbound traffic to tcp port 22 required for ssh\n', 'inbound_tcp_6379': 'selected security group is missing rule permiting inbound traffic to tcp port 6379 required for Redis\n', 'inbound_tcp_8265': 'selected security group is missing rule permiting inbound traffic to tcp port 8265 required to access Ray Dashboard\n'}

    def update_config(self, vpc_obj, zone_obj, sec_group_id, subnet_id):
        self.base_config['provider']['zone_name'] = zone_obj['name']

        node_config = {
                'vpc_id': vpc_obj['id'],
                'resource_group_id': vpc_obj['resource_group']['id'],
                'security_group_id': sec_group_id,
                'subnet_id': subnet_id
        }
        
        if self.base_config.get('available_node_types'):
            for available_node_type in self.base_config['available_node_types']:
                self.base_config['available_node_types'][available_node_type]['node_config'].update(node_config)
        else:
            self.base_config['available_node_types'] = {'ray_head_default': {'node_config': node_config}}
