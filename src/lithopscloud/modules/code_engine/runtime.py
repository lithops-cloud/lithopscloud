import os
import re
import subprocess
import sys
import tempfile
import types
from typing import Any, Dict

import docker
import lithops
from inquirer import errors
from lithops.scripts import cli
from lithops.utils import verify_runtime_name
from lithopscloud.modules.runtime import RuntimeConfig, update_decorator
from lithopscloud.modules.utils import (Color, color_msg, free_dialog,
                                        get_option_from_list)

BASE_RUNTIME_PREFIX = 'ibmfunctions/lithops-ce-v'


class CERuntimeConfig(RuntimeConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['runtime'] = base_config['code_engine'].get('runtime')

    @update_decorator
    def run(self) -> Dict[str, Any]:

        AUTO = 'Automatically'
        USER_INPUT = 'User input'
        option = get_option_from_list("Select lithops runtime", [
                                      AUTO, USER_INPUT], choice_key=None, default=AUTO)

        client = docker.from_env()

        def is_image_in_registry(image):
            try:
                client.images.get_registry_data(image)
                return True
            except:
                return False

        def validate_is_image_in_registry(answers, image):
            if is_image_in_registry(image):
                return True
            else:
                raise errors.ValidationError(
                    '', reason=f"Docker image {image} is missing from Docker registry")

        runtime = None

        if option == USER_INPUT:
            runtime = free_dialog(f"Runtime image compatible to installed lithops {lithops.__version__}",
                                  default=self.defaults.get('runtime'), validate=validate_is_image_in_registry)['answer']
        else:
            options = []

            if self.defaults.get('runtime'):
                # validate that docker image exists in public docker registry
                try:
                    client.images.get_registry_data(self.defaults['runtime'])
                    options.append[self.defaults['runtime']]
                except:
                    print(color_msg(
                        f'Warning, template derrived runtime docker image {self.defaults["runtime"]} is missing from the docker registry, ommiting it', color=Color.RED))
                    del self.defaults['runtime']

            # find current python version
            PYTHON_SUPPORTED = {"375": 'Python 3.7', "385": 'Python 3.8'}

            python_version = None
            try:
                python_version = next(p for p in PYTHON_SUPPORTED.keys() if p.startswith(
                    f'{sys.version_info.major}{sys.version_info.minor}'))
            except:
                pass

            if not python_version:
                print(color_msg(
                    f'Warning, current python version {sys.version_info.major}.{sys.version_info.minor} is not in the list of prebuilded base runtimes {[v for v in PYTHON_SUPPORTED.values()]}', color=Color.RED))

            # find installed lithops version
            lithops_version = lithops.__version__.replace('.', '')

            # generate compatible base runtime image string, e.g. ibmfunctions/lithops-ce-v375:254
            base_docker_image = f'{BASE_RUNTIME_PREFIX}{python_version}:{lithops_version}'

            print(
                f'Checking that base docker image {base_docker_image} exists in docker registry')

            EXTEND = f"Extend {base_docker_image} with custom python modules"

            # validate that docker image exists in public docker registry
            try:
                client.images.get_registry_data(base_docker_image)
                options.insert(len(options), base_docker_image)
                options.insert(len(options), EXTEND)
            except:
                print(f'')
                print(color_msg(
                    f'Warning, base runtime docker image {base_docker_image} is missing from the docker registry', color=Color.RED))

            if options:
                option = get_option_from_list(
                    "Select lithops runtime", options, choice_key=None)

                if option == EXTEND:
                    print(color_msg(
                        f'You must me logged in to your account on docker hub in order to complete extending {base_docker_image}', color=Color.YELLOW))
                    print(color_msg(
                        f'If not logged in yet, please exit using Ctrl ^C and login to docker using `docker login`', color=Color.YELLOW))

                    runtime = self._extend_image(base_docker_image)
                else:
                    runtime = option
            else:
                exit(1)
        return runtime

    def _extend_image(self, base_docker_image):

        def validate_modules_exist(answers, answer):
            if not answer:
                raise errors.ValidationError(
                    '', reason=f"Error, module list empty")

            res = True

            modules = list(filter(None, re.split("[, ]+", answer)))

            for module in modules:
                cmd = f'pip install {module}=='
                p = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = p.stdout.readlines()

                if "(from versions: none)" in str(output[0]):
                    if res:
                        print('')
                    print(
                        color_msg(f'Error, module {module} is missing from pypi', color=Color.RED))
                    res = False

            return res

        answer = free_dialog(f"Provide space or comma separated list of python modules",
                             validate=validate_modules_exist)['answer']

        print('modules validated, generating Dockerfile')
        modules = list(filter(None, re.split("[, ]+", answer)))

        tempdirpath = tempfile.mkdtemp()
        ext_docker_file = tempfile.mkstemp(
            dir=tempdirpath, suffix='.dockerfile')[1]

        # Generate Dockerfile extended with function dependencies and function
        with open(ext_docker_file, 'w') as df:
            df.write('\n'.join([
                'FROM {}'.format(base_docker_image),
                f'RUN pip install {" ".join(modules)}'
            ]))

        def validate_image_name(answers, image_name):
            try:
                verify_runtime_name(image_name)
            except:
                raise errors.ValidationError(
                    '', reason=f"{image_name} is not a valid docker image name")
                return False

            return True

        image_name = free_dialog(f"Please provide new image name in a form <USER>/<IMAGENAME>[:TAG]",
                                 validate=validate_image_name)['answer']

        # Build new extended runtime tagged by function hash
        cwd = os.getcwd()
        os.chdir(tempdirpath)

        # using lithops to build and publish runtime :)
        build_foo = cli.build
        for foo in build_foo.__dict__.values():
            if isinstance(foo, types.FunctionType) and foo.__name__ == 'build':
                foo(image_name, ext_docker_file, None, "code_engine", False)

        os.chdir(cwd)

        return image_name

    def update_config(self, runtime) -> Dict[str, Any]:
        self.base_config['code_engine']['runtime'] = runtime
        return self.base_config

