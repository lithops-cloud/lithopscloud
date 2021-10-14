from typing import Any, Dict

from lithops import config
from lithopscloud.modules.runtime import RuntimeConfig, update_decorator
import sys
import lithops
import docker
from lithopscloud.modules.utils import color_msg, Color, get_option_from_list, free_dialog, 
import requests
import tempfile
import os

BASE_RUNTIME_PREIX = 'ibmfunctions/lithops-ce-v'

class CERuntimeConfig(RuntimeConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['runtime'] = base_config['code_engine'].get('runtime')        

    @update_decorator
    def run(self) -> Dict[str, Any]:

        AUTO = 'Automatically'
        USER_INPUT = 'User input'
        option = get_option_from_list("Select lithops runtime", [AUTO, USER_INPUT], default=AUTO)

        
        client = docker.from_env()

        def is_image_in_registry(image):
            try:
                client.images.get_registry_data(image)
                return True
            except:
                return False

        runtime = None

        if option == USER_INPUT:
            runtime = free_dialog(f"Runtime image compatible to installed lithops {lithops.__version__}",
                              default=self.defaults.get('runtime'), validate=is_image_in_registry)['answer']
        else:
            options = []

            if self.defaults.get('runtime'):
                # validate that docker image exists in public docker registry
                try:
                    client.images.get_registry_data(self.defaults['runtime'])
                    options.append[self.defaults['runtime']]
                except:
                    print(color_msg(f'Warning, template derrived runtime docker image {self.defaults["runtime"]} is missing from the docker registry, ommiting it', color=Color.RED))
                    del self.defaults['runtime']

            # find current python version
            PYTHON_SUPPORTED = {"375": 'Python 3.7', "385": 'Python 3.8'}

            python_version = None
            try:
                python_version = next(p for p in PYTHON_SUPPORTED.keys() if p.startswith(f'{sys.version_info.major}{sys.version_info.minor}'))
            except:
                pass

            if not python_version:
                print(color_msg(f'Warning, current python version {sys.version_info.major}.{sys.version_info.minor} is not in the list of prebuilded base runtimes {[v for v in PYTHON_SUPPORTED.values()]}', color=Color.RED))
                        
            # find installed lithops version
            lithops_version = lithops.__version__.replace('.', '')

            # generate compatible base runtime image string, e.g. ibmfunctions/lithops-ce-v375:254
            base_docker_image = f'{BASE_RUNTIME_PREIX}{python_version}:{lithops_version}'

            print(f'Checking that base docker image {base_docker_image} exists in docker registry')

            EXTEND = f"Extend {base_docker_image} with custom python modules"
            
            # validate that docker image exists in public docker registry
            try:
                client.images.get_registry_data(base_docker_image)
                options.insert(len(options), base_docker_image)
                options.insert(len(options), EXTEND)
            except:
                print(f'')
                print(color_msg(f'Warning, base runtime docker image {base_docker_image} is missing from the docker registry', color=Color.RED))

            if options:
                option = get_option_from_list("Select lithops runtime", options)                

                if option == EXTEND:
                    print(color_msg(f'You must me logged in to your account on docker hub in order to complete extending {base_docker_image}', color=Color.YELLOW))
                    print(color_msg(f'If not logged in yet, please exit using Ctrl ^C and login to docker using `docker login`', color=Color.YELLOW))

                    runtime = self._extend_image(base_docker_image)
                else:
                    runtime = option

                return runtime
            else:
                exit(1)

    def _extend_image(base_docker_image):
        def validate_modules_exist(modules):
            res = True
            for module in modules.split(','):
                response = requests.get("http://pypi.python.org/pypi/{}/json"
                        .format(module))
                if response.status_code != 200:
                    print(color_msg(f'Error, module {module} is missing from pypi', color=Color.RED))
                    res = False

            return res
        
        modules = free_dialog(f"Provide comma separated list of python modules",
                              validate=validate_modules_exist)['answer']

        print('modules validated, generating Dockerfile')

        ext_docker_file = tempfile.mkstemp(suffix='.dockerfile')[1]

        # Generate Dockerfile extended with function dependencies and function
        with open(ext_docker_file, 'w') as df:
            df.write('\n'.join([
                            'FROM {}'.format(base_docker_image),
                            f'RUN pip install {modules}'
            ]))

        
        def validate_image_name(image_name):
            pass

        image_name = free_dialog(f"Please provide the image name, <USER>/<IMAGENAME>[:TAG]",
                              validate=validate_image_name)['answer']

        # Build new extended runtime tagged by function hash
        cwd = os.getcwd()
        os.chdir(tempfile.tempdir)

        # using lithops to build and publish runtime :)
        from lithops.scripts import cli
        cli.build(image_name, ext_docker_file, None, 'code_engine')
        os.chdir(cwd)

        return image_name

    def update_config(self, runtime) -> Dict[str, Any]:
        self.base_config['code_engine']['runtime'] = runtime
        return self.base_config

