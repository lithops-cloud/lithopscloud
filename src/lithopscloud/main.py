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

backends_str = {'gen2': LITHOPS_GEN2,
                'cf': LITHOPS_CF,
                'ce': LITHOPS_CE,
                'ray': RAY_GEN2,
                'local': LOCAL_HOST}


def select_backend(input_file, backend_short):
    backend = None
    default = None
    if backend_short:
        # find in backends structure
        b_name = backends_str[backend_short]
        backend = next((b for b in backends if b['name'] == b_name), None)
        if not backend:
            error(f"Provided backend {backend_short} not in supported backends list {backends_str}")
    else:
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
    backend_pkg = importlib.import_module(f"lithopscloud.modules.{backend['path']}")

    return base_config, backend_pkg

def load_base_config(backend):
    backend_path = backend['path'].replace('.', '/')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    input_file = f"{dir_path}/modules/{backend_path}/defaults.yaml"

    base_config = None
    with open(input_file) as f:
        base_config = yaml.safe_load(f)

    return base_config

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
@click.option('--defaults', help=f'Create defaults if not exist and generate default config', is_flag=True)
@click.option('--backend', '-b', help=f'One of following backends: {backends_str}')
def builder(iam_api_key, output_file, input_file, version, verify_config, compute_iam_endpoint, cos_iam_api_key, endpoint, backend, defaults):
    
    if version:
        print(f"{pkg_resources.get_distribution('lithopscloud').project_name} "
              f"{pkg_resources.get_distribution('lithopscloud').version}")
        exit(0)

    print(color_msg("\nWelcome to lithops cloud config export helper\n", color=Color.YELLOW))

    input_file, output_file = verify_paths(input_file, output_file, verify_config)

    if verify_config:
        verify_config_file(verify_config, output_file)
        exit(0)

    base_config, backend_pkg = select_backend(input_file, backend)
    
    modules = backend_pkg.MODULES
    base_config['create_defaults'] = defaults
    base_config, modules = validate_api_keys(base_config, modules, iam_api_key, compute_iam_endpoint, cos_iam_api_key)

    if endpoint and 'ibm_vpc' in base_config:
        base_config['ibm_vpc']['endpoint'] = endpoint
    elif endpoint and 'provider' in base_config:
        base_config['provider']['endpoint'] = endpoint

    for module in modules:
        next_module = module(base_config)
        
        if defaults:
            base_config = next_module.create_default()
        else:
            base_config = next_module.run()

    with open(output_file, 'w') as outfile:
        del base_config['create_defaults']
        yaml.dump(base_config, outfile, default_flow_style=False)

    if hasattr(backend_pkg, 'finish_message'):
        print(backend_pkg.finish_message(output_file))
    else:
        print("\n\n=================================================")
        print(color_msg(f"Cluster config file: {output_file}", color=Color.LIGHTGREEN))
        print("=================================================")

def error(msg):
    print(msg)
    raise Exception(msg)

# def get_config_template(backend_name):
#     input_file, output_file = verify_paths(input_file, output_file, None)
    
#     backend = None
#     for b in backends:
#         if b['name']  == backend_name:
#             backend = b
#             break
        
#     if not backend:
#         error(f"Provided backend {backend} not in supported backends list {[b['name'] for b in backends]}")
    
#     return load_base_config(backend)

def generate_config(backend_name, *args, **kwargs):
    def error(msg):
        print(msg)
        raise Exception(msg)

    _, output_file = verify_paths(None, None)
    
    backend = None
    for b in backends:
        if b['name']  == backend_name:
            backend = b
            break

    if not backend:
        error(f"Provided backend {backend} not in supported backends list {[b['name'] for b in backends]}")
    
    # now update base config with backend specific params
    base_config = importlib.import_module(f"lithopscloud.modules.{backend['path']}").load_config(backend, *args, **kwargs)
    
    # now find the right modules
    modules = importlib.import_module(f"lithopscloud.modules.{backend['path']}").MODULES
    
    for module in modules:
        base_config = module(base_config).verify(base_config)

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config, outfile, default_flow_style=False)

    print("\n\n=================================================")
    print(color_msg(f"Cluster config file: {output_file}", color=Color.LIGHTGREEN))
    print("=================================================")

    return output_file

# currently implemented only for lithops and ray gen2 backends
def delete_config(config_file_path):
    config = None
    with open(config_file_path) as f:
        config = yaml.safe_load(f)
        
    from lithopscloud.modules.gen2 import delete_config
    delete_config(config)      
    
if __name__ == '__main__':
    try:
        builder()
    except KeyboardInterrupt:
        # User interrupt the program
        exit()
