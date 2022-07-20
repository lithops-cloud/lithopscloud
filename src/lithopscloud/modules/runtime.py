from typing import Any, Dict
from lithopscloud.modules.config_builder import ConfigBuilder, update_decorator
from lithopscloud.modules.utils import free_dialog


class RuntimeConfig(ConfigBuilder):

    @update_decorator
    def run(self) -> Dict[str, Any]:
        runtime = free_dialog("Runtime image compatible with installed lithops version",
                              default=self.defaults.get('runtime'))['answer']

        return runtime
    
    @update_decorator
    def create_default(self):
        print(f"Selected default runtime image {self.defaults.get('runtime')}")
        return self.defaults.get('runtime')
