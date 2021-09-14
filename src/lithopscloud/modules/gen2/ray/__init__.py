from lithopscloud.modules.gen2.ray.api_key import RayApiKeyConfig
from lithopscloud.modules.gen2.ray.endpoint import RayEndpointConfig
from lithopscloud.modules.gen2.ray.floating_ip import FloatingIpConfig
from lithopscloud.modules.gen2.ray.image import RayImageConfig
from lithopscloud.modules.gen2.ray.ssh_key import RaySshKeyConfig
from lithopscloud.modules.gen2.ray.vpc import RayVPCConfig
from lithopscloud.modules.gen2.ray.workers import WorkersConfig
from lithopscloud.modules.gen2.ray.profile import RayProfileConfig

MODULES = [RayApiKeyConfig, RayEndpointConfig, RayVPCConfig,
           RaySshKeyConfig, RayImageConfig, FloatingIpConfig, WorkersConfig, RayProfileConfig]
