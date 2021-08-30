from typing import Any, Dict
from lithopscloud.modules.runtime import RuntimeConfig


class VPCRuntimeConfig(RuntimeConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['runtime'] = base_config['standalone'].get('runtime')

    def update_config(self, runtime) -> Dict[str, Any]:
        self.base_config['standalone']['runtime'] = runtime
        return self.base_config

