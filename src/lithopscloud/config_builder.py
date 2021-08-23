import logging

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services import ResourceManagerV2, ResourceControllerV2
from ibm_vpc import VpcV1

from typing import Any, Dict

logger = logging.getLogger(__name__)

def update_decorator(f):
    def foo(*args, **kwargs):
        result = f(*args, **kwargs)
        update_config = getattr(args[0], 'update_config')
        if isinstance(result, tuple):
            update_config(*result)
        else:
            update_config(result)
        return args[0].base_config
    return foo

class ConfigBuilder:
    """
    Interface for building IBM Cloud config files for Lithops and Ray
    """
    ibm_vpc_client = None
    resource_service_client = None
    resource_controller_service = None

    def __init__(self, base_config: Dict[str, Any]) -> None:

        if not ConfigBuilder.ibm_vpc_client:            
            authenticator = IAMAuthenticator(self.iam_api_key)
            ConfigBuilder.ibm_vpc_client = VpcV1('2021-01-19', authenticator=authenticator)
            ConfigBuilder.resource_service_client = ResourceManagerV2(authenticator=authenticator)
            ConfigBuilder.resource_controller_service = ResourceControllerV2(authenticator=authenticator)

        self.ibm_vpc_client = ConfigBuilder.ibm_vpc_client
        self.resource_service_client = ConfigBuilder.resource_service_client
        self.resource_controller_service = ConfigBuilder.resource_controller_service

        self.base_config = base_config

    """Interacts with user to get all required parameters"""
    def run(self, config) -> Dict[str, Any]:
        """Return updated config dictionary that can be dumped to config file
        
        Run interactive questionnaire
        """
        raise NotImplementedError

    """Updates specified config dictionary"""
    def update_config(self, *args) -> Dict[str, Any]:
        """Updates config dictionary that can be dumped to config file"""
        raise NotImplementedError
    