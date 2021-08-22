from src.lithopscloud.modules.lithops import MODULES as LITHOPS_MODULES
from src.lithopscloud.modules.ray import MODULES as RAY_MODULES
from src.lithopscloud.modules.utils import ValidationException

import yaml
import tempfile
import click

def get_base_config(input_file, format):
    
    if not input_file:
        input_file = f'./src/lithopscloud/modules/{format}/defaults.yaml'

    with open(input_file) as f:
        template_config = yaml.safe_load(f)
        return template_config
        

@click.command()
@click.option('--output-file', '-o', help='Output filename to save configurations')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', required=True, help='IAM_API_KEY')
@click.option('--format', type=click.Choice(['lithops', 'ray']), required=True, help='format of the output file')
def builder(iam_api_key, output_file, input_file, format):
    print(f"\n\033[92mWelcome to vpc config export helper\033[0m\n")

    base_config = get_base_config(input_file, format)

    if format == 'lithops':
        MODULES = LITHOPS_MODULES
        base_config['ibm']['iam_api_key'] = iam_api_key
    else:
        MODULES = RAY_MODULES
        base_config['provider']['iam_api_key'] = iam_api_key

    for module in MODULES:
        next_module = module(base_config)
        base_config = next_module.run()

    if not output_file:
        output_file = tempfile.mkstemp(suffix = '.yaml')[1]

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config,  outfile, default_flow_style=False)
    
    print("\n\n=================================================")
    print(f"\033[92mCluster config file: {output_file}\033[0m")
    print("=================================================")

if __name__ == '__main__':
    builder()