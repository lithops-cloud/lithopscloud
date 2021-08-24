from lithopscloud.modules.lithops.ssh_key import LithopsSshKeyConfig
from lithopscloud.modules.lithops.endpoint import LithopsEndpointConfig
from lithopscloud.modules.lithops.vpc import LithopsVPCConfig
from lithopscloud.modules.lithops.image import LithopsImageConfig
from lithopscloud.modules.lithops.cos import CosConfig
from lithopscloud.modules.lithops.runtime import RuntimeConfig


MODULES = [LithopsEndpointConfig, LithopsVPCConfig, LithopsSshKeyConfig, LithopsImageConfig, CosConfig, RuntimeConfig]