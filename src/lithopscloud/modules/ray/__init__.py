from lithopscloud.modules.ray.endpoint import RayEndpointConfig
from lithopscloud.modules.ray.vpc import RayVPCConfig
from lithopscloud.modules.ray.ssh_key import RaySshKeyConfig
from lithopscloud.modules.ray.image import RayImageConfig
from lithopscloud.modules.ray.floating_ip import FloatingIpConfig
from lithopscloud.modules.ray.workers import WorkersConfig

MODULES = [RayEndpointConfig, RayVPCConfig, RaySshKeyConfig, RayImageConfig, FloatingIpConfig, WorkersConfig]