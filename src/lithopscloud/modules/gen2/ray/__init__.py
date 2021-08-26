from lithopscloud.modules.api_key import ApiKeyConfig
from lithopscloud.modules.gen2.ray.endpoint import RayEndpointConfig
from lithopscloud.modules.gen2.ray.floating_ip import FloatingIpConfig
from lithopscloud.modules.gen2.ray.image import RayImageConfig
from lithopscloud.modules.gen2.ray.ssh_key import RaySshKeyConfig
from lithopscloud.modules.gen2.ray.vpc import RayVPCConfig
from lithopscloud.modules.gen2.ray.workers import WorkersConfig

MODULES = [ApiKeyConfig, RayEndpointConfig, RayVPCConfig,
           RaySshKeyConfig, RayImageConfig, FloatingIpConfig, WorkersConfig]
