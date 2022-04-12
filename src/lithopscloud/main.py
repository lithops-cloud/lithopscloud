import importlib
import pkg_resources
import os
import click
import yaml
from lithopscloud.modules.config_verification import verify_config_file

from lithopscloud.modules.utils import get_option_from_list, color_msg, Color, verify_paths

LITHOPS_GEN2, LITHOPS_CF, LITHOPS_CE, RAY_GEN2, LOCAL_HOST = 'Lithops Gen2', 'Lithops Cloud Functions', \
                                                             'Lithops Code Engine', 'Ray Gen2', 'Local Host'


backends = [
    {'name': LITHOPS_GEN2, 'path': 'gen2.lithops'},
    {'name': LITHOPS_CF, 'path': 'cloud_functions'},
    {'name': LITHOPS_CE, 'path': 'code_engine'},
    {'name': RAY_GEN2, 'path': 'gen2.ray'},
    {'name': LOCAL_HOST, 'path': 'local_host'}
]

def load_base_config(backend):
    backend_path = backend['path'].replace('.', '/')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    input_file = f"{dir_path}/modules/{backend_path}/defaults.yaml"

    base_config = None
    with open(input_file) as f:
        base_config = yaml.safe_load(f)
        
    return base_config

def select_backend(input_file):
    # select backend
    base_config = {}

    if input_file:
        with open(input_file) as f:
            base_config = yaml.safe_load(f)
    # TODO: also verify existence of base_config['lithops']['backend']
    default = None
    if base_config.get('lithops'):
        mode = base_config['lithops']['mode'] if base_config['lithops'].get(
            'mode') else None
        if mode == 'standalone':
            default = LITHOPS_GEN2
        elif mode == 'code_engine':
            default = LITHOPS_CE
        elif mode == 'ibm_cf':
            default = LITHOPS_CF
    elif base_config.get('provider'):
        default = RAY_GEN2

    backend = get_option_from_list("Please select a compute backend", backends, default=default)

    # in case input file didn't match selected option we either need to raise error or start it from scratch (defaults), currently startin from defaults
    # import pdb;pdb.set_trace()
    if backend['name'] != default:
        base_config = load_base_config(backend)

    # now find the right modules
    modules = importlib.import_module(f"lithopscloud.modules.{backend['path']}").MODULES

    return base_config, modules

def validate_api_keys(base_config, modules, iam_api_key, compute_iam_endpoint, cos_iam_api_key):
    # ugly hack to support case when api_key been provided by user as parameter to lithopscloud
    # TODO: consider better approach
    # we know that the first module has to be API_KEY module
    # we invoke the first module with provided api key and pop it from list
    api_key_module = modules[0]
    base_config = api_key_module(base_config).run(api_key=iam_api_key,
                                                  compute_iam_endpoint=compute_iam_endpoint,
                                                  cos_iam_api_key=cos_iam_api_key)

    modules = modules[1:]
    return base_config, modules
    
@click.command()
@click.option('--output-file', '-o', help='Output filename to save configurations')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--verify-config', help="Path to a lithops config file you'd wish to verify."
                                      " Outputs a usable config file if possible.")
@click.option('--compute-iam-endpoint', help='IAM endpoint url used for compute instead of default https://iam.cloud.ibm.com')
@click.option('--cos-iam-api-key', help='IAM_API_KEY used to communicate with cos separately')
@click.option('--endpoint', help='IBM Cloud API endpoint')
def builder(iam_api_key, output_file, input_file, version, verify_config, compute_iam_endpoint, cos_iam_api_key, endpoint):
    if version:
        print(f"{pkg_resources.get_distribution('lithopscloud').project_name} "
              f"{pkg_resources.get_distribution('lithopscloud').version}")
        exit(0)

    print(color_msg("\nWelcome to lithops cloud config export helper\n", color=Color.YELLOW))

    input_file, output_file = verify_paths(input_file, output_file, verify_config)

    if verify_config:
        verify_config_file(verify_config, output_file)
        exit(0)

    base_config, modules = select_backend(input_file)
    base_config, modules = validate_api_keys(base_config, modules, iam_api_key, compute_iam_endpoint, cos_iam_api_key)
    breakpoint()

    if endpoint:
        base_config['ibm_vpc']['endpoint'] = endpoint

    for module in modules:
        next_module = module(base_config)
        base_config = next_module.run()

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config, outfile, default_flow_style=False)

    print("\n\n=================================================")
    print(color_msg(f"Cluster config file: {output_file}", color=Color.LIGHTGREEN))
    print("=================================================")

def generate_config(backend_name, iam_api_key, region,
                    image_id=None, profile_name=None,
                    key_id=None, ssh_key_filename=None,
                    vpc_id=None, cos_bucket_name=None,
                    compute_iam_endpoint=None, cos_iam_api_key=None,
                    input_file=None, output_file=None):
    def error(msg):
        print(msg)
        raise Exception(msg)

    input_file, output_file = verify_paths(input_file, output_file, None)
    
    backend = None
    for b in backends:
        if b['name']  == backend_name:
            backend = b
            break
        
    if not backend:
        error(f"Provided backend {backend} not in supported backends list {[b['name'] for b in backends]}")
    
    base_config = load_base_config(backend)
     
    base_config['ibm_vpc']['vpc_id'] = vpc_id
    base_config['ibm_vpc']['image_id'] = image_id
    base_config['ibm_vpc']['profile_name'] = profile_name
    base_config['ibm_vpc']['ssh_key_filename'] = ssh_key_filename
    base_config['ibm_vpc']['key_id'] = key_id
    
    if cos_bucket_name:
        base_config['ibm_cos']['storage_bucket'] = cos_bucket_name
    if cos_iam_api_key:
        base_config['ibm_cos']['iam_api_key'] = cos_iam_api_key
        
    base_config['ibm_vpc']['endpoint'] = f'https://{region}.iaas.cloud.ibm.com'
    
    # now find the right modules
    modules = importlib.import_module(f"lithopscloud.modules.{backend['path']}").MODULES

    base_config, modules = validate_api_keys(base_config, modules, iam_api_key, compute_iam_endpoint, cos_iam_api_key)

    for module in modules:
        base_config = module(base_config).verify(base_config)

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config, outfile, default_flow_style=False)

    print("\n\n=================================================")
    print(color_msg(f"Cluster config file: {output_file}", color=Color.LIGHTGREEN))
    print("=================================================")

    return output_file

    
if __name__ == '__main__':
    try:
        builder()
    except KeyboardInterrupt:
        # User interrupt the program
        exit()
