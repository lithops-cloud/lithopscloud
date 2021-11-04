import os

from lithopscloud.modules.code_engine import CodeEngine
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
    namespace = ''
    kubeconfig = ''
    output = {}

    @spinner
    def _verify_namespace():

        if 'namespace' not in ce_config:
            ce_config['namespace'] = ''

        if ce_config['namespace']:  # verify namespace
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
            print(color_msg("Missing region segment in Code Engine",Color.RED))
            base_config['code_engine']['region'] = ''

        namespace = _verify_namespace()

    if not kubeconfig and not iam_api_key:  # returns None
        print(color_msg('Error - Either an IAmApiKey or kubeconfig path must be provided to configure Code Engine', Color.RED))

    elif namespace and namespace != ARG_STATUS.INVALID and ce_config['runtime']:
        output['code_engine'] = base_config['code_engine']
        return output

    elif kubeconfig:
        output['code_engine'] = {'kubecfg_path': kubeconfig}
        return output

    return reconfigure(base_config, output)


def reconfigure(base_config, output):
    """Directs the user to repeat the reconfiguration process and returns the recreated code engine configuration"""

    iamapikey = base_config['ibm']['iam_api_key']
    if iamapikey and iamapikey != ARG_STATUS.INVALID:
        should_reconfigure = get_confirmation(color_msg("Unable to configure the Code Engine segment due to invalid critical fields"
                                                 "Would you like to reconfigure this segment?", Color.RED))['answer']
        if should_reconfigure:
            ce = CodeEngine(base_config)
            new_config = ce.run()
            output['code_engine'] = new_config['code_engine']
            return output
