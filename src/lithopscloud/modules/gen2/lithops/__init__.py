from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.gen2.lithops.ssh_key import LithopsSshKeyConfig
from lithopscloud.modules.gen2.lithops.endpoint import LithopsEndpointConfig
from lithopscloud.modules.gen2.lithops.vpc import LithopsVPCConfig
from lithopscloud.modules.gen2.lithops.image import LithopsImageConfig
from lithopscloud.modules.cos import CosConfig
from lithopscloud.modules.gen2.lithops.runtime import VPCRuntimeConfig
from lithopscloud.modules.gen2.lithops.dismantle import DismantleConfig
from lithopscloud.modules.gen2.lithops.profile import LithopsProfileConfig
from lithopscloud.main import load_base_config
from lithopscloud.modules.utils import color_msg, Color

MODULES = [ApiKeyConfig, LithopsEndpointConfig, LithopsVPCConfig, LithopsSshKeyConfig, LithopsImageConfig, CosConfig, VPCRuntimeConfig, DismantleConfig, LithopsProfileConfig]

def finish_message(output_file):
    return "\n\n================================================================\n" + \
        color_msg(f"Cluster config file: {output_file}",
                  color=Color.LIGHTGREEN) + \
        "\n\nTo start using it, you may run: " + \
        color_msg(f"export LITHOPS_CONFIG_FILE={output_file}",
                  color=Color.YELLOW) + \
        "\n================================================================"
        
def load_config(backend, iam_api_key, region=None,
                    image_id=None, profile_name='bx2-2x8',
                    key_id=None, ssh_key_filename=None,
                    vpc_id=None, cos_bucket_name=None,
                    compute_iam_endpoint=None, cos_iam_api_key=None):
    
    base_config = load_base_config(backend)
    
    base_config['ibm']['iam_api_key'] = iam_api_key
    base_config['ibm_vpc']['vpc_id'] = vpc_id
    base_config['ibm_vpc']['image_id'] = image_id
    base_config['ibm_vpc']['profile_name'] = profile_name
    base_config['ibm_vpc']['ssh_key_filename'] = ssh_key_filename
    base_config['ibm_vpc']['key_id'] = key_id
    
    base_config['ibm_cos']['storage_bucket'] = cos_bucket_name

    if cos_iam_api_key:
        base_config['ibm_cos']['iam_api_key'] = cos_iam_api_key
        
    if compute_iam_endpoint:
        base_config['ibm']['iam_endpoint'] = compute_iam_endpoint
        
    base_config['ibm_vpc']['endpoint'] = f'https://{region}.iaas.cloud.ibm.com'
    
    return base_config

def parse_config(config):
    res = {'iam_api_key': config['ibm']['iam_api_key']}    
    
    res['vpc_id'] = config['ibm_vpc']['vpc_id']
    res['key_id'] = config['ibm_vpc']['key_id']
    res['subnet_id'] = config['ibm_vpc']['subnet_id']
    
    res['endpoint'] = config['ibm_vpc']['endpoint']

    if 'iam_endpoint' in config['ibm']:
        res['iam_endpoint'] = config['ibm']['iam_endpoint']

    return res