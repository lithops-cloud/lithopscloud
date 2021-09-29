import importlib
import pkg_resources
import os
import click
import yaml

from lithopscloud.modules.utils import get_option_from_list, test_config_file, color_msg, Color, verify_paths

LITHOPS_GEN2, LITHOPS_CF, LITHOPS_CE, RAY_GEN2, LOCAL_HOST = 'Lithops Gen2', 'Lithops Cloud Functions', \
                                                             'Lithops Code Engine', 'Ray Gen2', 'Local Host'


def select_backend(input_file, iam_api_key):
    # select backend
    backends = [
        {'name': LITHOPS_GEN2, 'path': 'gen2.lithops'},
        {'name': LITHOPS_CF, 'path': 'cloud_functions'},
        {'name': LITHOPS_CE, 'path': 'code_engine'},
        {'name': RAY_GEN2, 'path': 'gen2.ray'},
        {'name': LOCAL_HOST, 'path': 'local_host'}
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

    backend = get_option_from_list("Please select a compute backend", backends, default=default)

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
@click.option('--iam-api-key', '-a', help='IAM_API_KEY')
@click.option('--version', '-v', help=f'Get package version', is_flag=True)
@click.option('--verify-config', help="Path to a lithops config file you'd wish to verify via testing")
def builder(iam_api_key, output_file, input_file, version, verify_config):
    if version:
        print(f"{pkg_resources.get_distribution('lithopscloud').project_name} "
              f"{pkg_resources.get_distribution('lithopscloud').version}")
        exit(0)

    if verify_config:
        test_config_file(verify_config)
        exit(0)

    print(color_msg("\nWelcome to lithops cloud config export helper\n", color=Color.YELLOW))
    input_file, output_file = verify_paths(input_file, output_file)

    base_config, modules = select_backend(input_file, iam_api_key)

    for module in modules:
        next_module = module(base_config)
        base_config = next_module.run()

    with open(output_file, 'w') as outfile:
        yaml.dump(base_config, outfile, default_flow_style=False)

    print("\n\n=================================================")
    print(color_msg(f"Cluster config file: {output_file}", color=Color.LIGHTGREEN))
    print("=================================================")


if __name__ == '__main__':
    try:
        builder()
    except KeyboardInterrupt:
        # User interrupt the program
        exit()
