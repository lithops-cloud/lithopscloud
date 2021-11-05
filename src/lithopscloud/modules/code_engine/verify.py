import os

import docker

from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.code_engine import CodeEngine, CERuntimeConfig
from lithopscloud.modules.code_engine.code_engine import init_ce_region_list, CE_REGIONS
from lithopscloud.modules.config_builder import spinner
from lithopscloud.modules.utils import CACHE, ARG_STATUS, color_msg, Color, get_confirmation


def verify(base_config):
    """this function outputs error messages based on lacking or invalid values in regard the code engine segment of the
       lithops config file.
       :param dict base_config: contents of provided config file.  """

    ce_config = base_config['code_engine']
    iam_api_key = base_config['ibm']['iam_api_key']
    region = ''
    kubeconfig = ''
    output = {}

    @spinner
    def _verify_namespace():
        namespace = ''
        if 'namespace' not in ce_config:
            ce_config['namespace'] = ''
            if not kubeconfig:
                print(color_msg("'namespace' segment is mandatory when configuring Code Engine based on iamapikey",Color.RED))

        if ce_config['namespace'] and iam_api_key and iam_api_key != ARG_STATUS.INVALID:
            namespace = ce_config['namespace']
            match_found = False
            ce = CodeEngine(base_config)
            resource_groups = ce.resource_service_client.list_resource_groups().get_result()['resources']

            for res_grp in resource_groups:
                if match_found:
                    break
                CACHE['resource_group_id'] = res_grp['id']
                projects = ce.get_ce_instances(verbose=False)

                for project in projects:
                    if match_found:
                        break
                    if ce.get_project_namespace(project) == namespace:
                        if region and region != project['region']:
                            print(color_msg(f"Code Engine Namespace resides in {project['region']} rather than {region}",Color.RED))
                        base_config['code_engine']['region'] = project['region']
                        match_found = True

            if not match_found:
                namespace = ARG_STATUS.INVALID
                print(color_msg("Couldn't find a project with given namespace-id certified by the provided iamapikey.",Color.RED))

        return namespace

    if 'kubecfg_path' in base_config:
        kubeconfig = ce_config['kubecfg_path']
        if not os.path.isfile(kubeconfig):
            print(color_msg(f"kubeconfig file doesn't exist in your machine", Color.RED))
            kubeconfig = ARG_STATUS.INVALID
        if not os.environ['KUBECONFIG']:
            print(color_msg(f"environment variable 'KUBECONFIG' doesn't exist", Color.RED))

    is_runtime_configured = verify_runtime(base_config, kubeconfig)

    if iam_api_key and iam_api_key != ARG_STATUS.INVALID:
        output['ibm'] = base_config['ibm']

        init_ce_region_list()

        if 'region' in ce_config:
            if ce_config['region'] not in CE_REGIONS:
                region = ''
                print(color_msg(f"Code Engine project's 'region' must be a value from the following list: {CE_REGIONS}",
                                Color.RED))
            else:
                region = ce_config['region']
        else:
            base_config['code_engine']['region'] = ''
            if not kubeconfig:
                print(color_msg("'region' segment is mandatory when configuring Code Engine based on iamapikey",Color.RED))

    namespace = _verify_namespace()

    if not kubeconfig and not iam_api_key:
        print(color_msg('Error - Either an IAmApiKey or kubeconfig path must be provided to configure Code Engine', Color.RED))

    elif namespace and namespace != ARG_STATUS.INVALID and is_runtime_configured:
        output['code_engine'] = base_config['code_engine']
        return output

    elif kubeconfig:
        output['code_engine'] = {'kubecfg_path': kubeconfig}
        return output

    return reconfigure(base_config, output,is_runtime_configured)


def reconfigure(base_config, output,is_runtime_configured):
    """Directs the user to repeat the reconfiguration process and returns the recreated code engine configuration"""

    iamapikey = base_config['ibm']['iam_api_key']

    should_reconfigure = get_confirmation(color_msg("Unable to configure the Code Engine segment due to invalid critical field(s) "
                                             "Would you like to reconfigure this segment?", Color.RED))['answer']
    if should_reconfigure:
        if not iamapikey or iamapikey == ARG_STATUS.INVALID:
            base_config['ibm']['iam_api_key'] = ''
            ApiKeyConfig(base_config).run()  # sets base_config's iam_api_key value
        if not is_runtime_configured:
            CERuntimeConfig(base_config).run()  # sets base_config's runtime value
        CodeEngine(base_config).run()       # sets base_config's code engine's segment except runtime

        output['code_engine'] = base_config['code_engine']
        output['ibm'] = base_config['ibm']
        return output


def verify_runtime(base_config, kubeconfig):
    """verifies given runtime. if provided runtime isn't valid and it's necessary, i.e.
      configuration isn't based on kubeconfig, tries to update base config with newly generated runtime image.
      :returns True upon success."""

    def _generate_new_runtime():
        """:returns True if a valid runtime image was created or provided by user.
            upon success, said image is stored within base_config"""
        iam_api_key = base_config['ibm']['iam_api_key']

        # Can't generate a config file without a valid iamapikey, hence no use in fixing the runtime image.
        if iam_api_key and iam_api_key != ARG_STATUS.INVALID:
            should_reconfigure = get_confirmation(color_msg("Runtime is a mandatory field. Would you like to go through"
                                                            " the required configuration process?", Color.RED))['answer']
            if should_reconfigure:
                CERuntimeConfig(base_config).run()
                return True

    if 'runtime' in base_config['code_engine']:
        client = docker.from_env()
        try:
            client.images.get_registry_data(base_config['code_engine']['runtime'])
            return True
        except:
            print(color_msg("Specified runtime image can't be found on docker repository", Color.RED))
            return _generate_new_runtime()
    else:
        base_config['code_engine']['runtime'] = ''
        if not kubeconfig:  # runtime isn't necessary when kubeconfig is initialized.
            print(color_msg("Runtime image is a mandatory field when configuring Code Engine using iamapikey", Color.RED))
            return _generate_new_runtime()


