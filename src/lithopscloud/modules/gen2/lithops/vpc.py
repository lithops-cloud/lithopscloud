from lithopscloud.modules.gen2.vpc import VPCConfig
from typing import Any, Dict

REQUIRED_RULES = {'outbound_tcp_all': 'selected security group is missing rule permitting outbound TCP access\n', 'outbound_udp_all': 'selected security group is missing rule permitting outbound UDP access\n', 'inbound_tcp_sg': 'selected security group is missing rule permiting inbound tcp traffic inside selected security group\n', 'inbound_tcp_22': 'selected security group is missing rule permiting inbound traffic to tcp port 22 required for ssh\n'}

class LithopsVPCConfig(VPCConfig):
    
    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

        self.vpc_name = 'lithops-cluster-vpc'
        self.sg_rules = REQUIRED_RULES
        self.defaults = self.base_config['ibm_vpc']

    def update_config(self, vpc_obj, zone_obj, subnet_id):
        sec_group_id = vpc_obj['default_security_group']['id']

        self.base_config['ibm_vpc']['vpc_id'] = vpc_obj['id']
        self.base_config['ibm_vpc']['zone_name'] = zone_obj['name']
        self.base_config['ibm_vpc']['resource_group_id'] = vpc_obj['resource_group']['id']
        self.base_config['ibm_vpc']['security_group_id'] = sec_group_id
        self.base_config['ibm_vpc']['subnet_id'] = subnet_id


        


