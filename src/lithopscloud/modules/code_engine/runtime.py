from typing import Any, Dict
from lithopscloud.modules.runtime import RuntimeConfig


class CERuntimeConfig(RuntimeConfig):

    def __init__(self, base_config: Dict[str, Any]) -> None:
        super().__init__(base_config)
        self.defaults['runtime'] = base_config['code_engine'].get('runtime')

    def update_config(self, runtime) -> Dict[str, Any]:
        self.base_config['code_engine']['runtime'] = runtime
        return self.base_config

