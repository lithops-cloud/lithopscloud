from typing import Any, Dict

import inquirer
from lithopscloud.modules.config_builder import ConfigBuilder


class DismantleConfig(ConfigBuilder):

    def run(self) -> Dict[str, Any]:
        print('\n')
        STOP_AFTER_FINISHED = f'\033[92mStop\033[0m VM after grace period when task finished'
        DELETE_AFTER_FINISHED = f'\033[92mDelete\033[0m VM after grace period when task finished'
        KEEP = f'\033[92mKeep\033[0m VM after task finished'

        default_auto_dismantle = self.base_config['standalone'].get(
            'auto_dismantle')
        default_delete_on_dismantle = self.base_config['ibm_vpc'].get(
            'delete_on_dismantle', True)

        default = DELETE_AFTER_FINISHED
        if not default_auto_dismantle:
            default = KEEP
        elif not default_delete_on_dismantle:
            default = STOP_AFTER_FINISHED

        q = [
            inquirer.List('answer', message='Choose VM dismantle policy', choices=[
                          STOP_AFTER_FINISHED, DELETE_AFTER_FINISHED, KEEP], default=default)
        ]

        answers = inquirer.prompt(q, raise_keyboard_interrupt=True)
        if answers['answer'] == KEEP:
            self.base_config['standalone']['auto_dismantle'] = False
        else:
            self.base_config['standalone']['auto_dismantle'] = True
            if answers['answer'] == STOP_AFTER_FINISHED:
                self.base_config['ibm_vpc']['delete_on_dismantle'] = False
            elif answers['answer'] == STOP_AFTER_FINISHED:
                self.base_config['ibm_vpc']['delete_on_dismantle'] = True

            # TODO: set dismantle grace periods
            
        return self.base_config

