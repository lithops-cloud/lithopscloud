from typing import Any, Dict
from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator
from lithopscloud.modules.utils import free_dialog


class RuntimeConfig(ConfigBuilder):

    @update_decorator
    def run(self) -> Dict[str, Any]:
        runtime = free_dialog("Runtime image compatible with installed lithops version",
                              default=self.defaults.get('runtime'))['answer']

        return runtime
