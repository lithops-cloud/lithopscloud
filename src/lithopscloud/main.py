import importlib
import pkg_resources
import yaml
import tempfile
import click
import os

def get_base_config(input_file, format):
    
    if not input_file:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        input_file = f'{dir_path}/modules/{format}/defaults.yaml'

    with open(input_file) as f:
        template_config = yaml.safe_load(f)
        return template_config
        

@click.command()
@click.option('--output-file', '-o', help='Output filename to save configurations')
@click.option('--input-file', '-i', help=f'Template for the new configuration')
@click.option('--iam-api-key', help='IAM_API_KEY')
@click.option('--format', type=click.Choice(['lithops', 'ray']), help='format of the output file')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
def builder(iam_api_key, output_file, input_file, format, version):

    if version:
        print(f"{pkg_resources.get_distribution('lithopscloud').project_name} {pkg_resources.get_distribution('lithopscloud').version}")
        exit(0)

    if not iam_api_key:
        print(f"Error: Missing option '--iam-api-key'")
        exit(1)

    if not format:
        print(f"Error: Missing option 'format'")
        exit(1)

    print(f"\n\033[92mWelcome to vpc config export helper\033[0m\n")

    base_config = get_base_config(input_file, format)

    MODULES = importlib.import_module(f'lithopscloud.modules.{format}').MODULES

    if format == 'lithops':
        base_config['ibm']['iam_api_key'] = iam_api_key
    else:
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
