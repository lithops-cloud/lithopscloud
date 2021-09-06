from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.gen2.lithops.ssh_key import LithopsSshKeyConfig
from lithopscloud.modules.gen2.lithops.endpoint import LithopsEndpointConfig
from lithopscloud.modules.gen2.lithops.vpc import LithopsVPCConfig
from lithopscloud.modules.gen2.lithops.image import LithopsImageConfig
from lithopscloud.modules.cos import CosConfig
from lithopscloud.modules.gen2.lithops.runtime import VPCRuntimeConfig
from lithopscloud.modules.gen2.lithops.dismantle import DismantleConfig
from lithopscloud.modules.gen2.lithops.profile import LithopsProfileConfig


MODULES = [ApiKeyConfig, LithopsEndpointConfig, LithopsVPCConfig, LithopsSshKeyConfig, LithopsImageConfig, CosConfig, VPCRuntimeConfig, DismantleConfig, LithopsProfileConfig]