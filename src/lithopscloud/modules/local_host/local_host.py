from typing import Dict, Any

from lithopscloud import color_msg
from lithopscloud.modules.config_builder import ConfigBuilder


class LocalHost(ConfigBuilder):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)

    def run(self, api_key=None) -> Dict[str, Any]:
        return self.base_config
