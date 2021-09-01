import importlib
import tempfile
import pkg_resources
import os
import click
import yaml

from lithopscloud.modules.utils import get_option_from_list


LITHOPS_GEN2, LITHOPS_CF, LITHOPS_CE, RAY_GEN2 = 'Lithops Gen2', 'Lithops Cloud Functions', 'Lithops Code Engine', 'Ray Gen2'

def select_backend(input_file, iam_api_key):
    # select backend
    backends = [
                {'name': LITHOPS_GEN2, 'path': 'gen2.lithops'}, 
                {'name': LITHOPS_CF, 'path': 'cloud_functions'},
                {'name': LITHOPS_CE, 'path': 'code_engine'}, 
                {'name': RAY_GEN2, 'path': 'gen2.ray'}
    ]

    base_config = {}

    if input_file:
        with open(input_file) as f:
            base_config = yaml.safe_load(f)

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

    def validate(answers, current):
        if current == LITHOPS_CF:
            from inquirer.errors import ValidationError
            raise ValidationError(current, reason=f'{current} not supported yet by this project')
        return True

    backend = get_option_from_list(
        "Please select backend", backends, default=default, validate=validate)

    # in case input file didn't match selected option we either need to raise error or start it from scratch (defaults), currently startin from defaults
    # import pdb;pdb.set_trace()
    if backend['name'] != default:
        dir_path = os.path.dirname(os.path.realpath(__file__))

        input_file = f"{dir_path}/modules/{backend['path'].replace('.', '/')}/defaults.yaml"

        with open(input_file) as f:
            base_config = yaml.safe_load(f)

    # now find the right modules
    modules = importlib.import_module(f"lithopscloud.modules.{backend['path']}").MODULES

    if iam_api_key:
        # ugly hack to support case when api_key been provided by user as parameter to lithopscloud
        # TODO: consider better approach
        # we know that the first module has to be API_KEY module
        # we invoke the first module with provided api key and pop it from list
        api_key_module = modules[0]
        base_config = api_key_module(base_config).run(api_key=iam_api_key)

        modules = modules[1:]

    return base_config, modules


@click.command()
@click.option('--output-file', '-o', help='Output filename to save configurations')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
def builder(iam_api_key, output_file, input_file, version):

    if version:
        print(f"{pkg_resources.get_distribution('lithopscloud').project_name} {pkg_resources.get_distribution('lithopscloud').version}")
        exit(0)

    print(f"\n\033[92mWelcome to vpc config export helper\033[0m\n")

    base_config, modules = select_backend(input_file, iam_api_key)

    for module in modules:        
        next_module = module(base_config)
        base_config = next_module.run()

    if not output_file:
        output_file = tempfile.mkstemp(suffix='.yaml')[1]

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config,  outfile, default_flow_style=False)

    print("\n\n=================================================")
    print(f"\033[92mCluster config file: {output_file}\033[0m")
    print("=================================================")


if __name__ == '__main__':
    try:
        builder()
    except KeyboardInterrupt:
        # User interrupt the program
        exit()

