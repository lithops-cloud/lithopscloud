from typing import Any, Dict

import inquirer
from lithopscloud.modules.config_builder import ConfigBuilder

DELETE_AFTER_FINISHED = f'\033[92mDelete\033[0m workers VMs immediately after all tasks finished'
KEEP = f'\033[92mKeep\033[0m workers VMs for reuse for some grace period after all tasks finished'
STOP_AFTER_FINISHED = f'\033[92mStop\033[0m workers VMs immediately after all tasks finished'
KEEP_FOREVER = f'\033[92mNever\033[0m delete worker VMs, keep forever'

class DismantleConfig(ConfigBuilder):

    def run(self) -> Dict[str, Any]:
        print('\n')

        default_auto_dismantle = self.base_config['standalone'].get(
            'auto_dismantle')
        default_delete_on_dismantle = self.base_config['ibm_vpc'].get(
            'delete_on_dismantle', True)
        default_mode = self.base_config['standalone'].get('exec_mode', 'create')

        default = DELETE_AFTER_FINISHED
        if default_mode == 'reuse':
            default = KEEP
        elif not default_delete_on_dismantle:
            default = STOP_AFTER_FINISHED

        q = [
            inquirer.List('answer', message='Choose VM dismantle policy', choices=[
                          DELETE_AFTER_FINISHED, KEEP, STOP_AFTER_FINISHED, KEEP_FOREVER], default=default)
        ]

        answers = inquirer.prompt(q, raise_keyboard_interrupt=True)
        if answers['answer'] == KEEP:
            self.base_config['standalone']['auto_dismantle'] = True
            self.base_config['ibm_vpc']['delete_on_dismantle'] = True
            self.base_config['standalone']['exec_mode'] = 'reuse'
        else:
            
            self.base_config['standalone']['exec_mode'] = 'create'

            if answers['answer'] == KEEP_FOREVER:
                self.base_config['ibm_vpc']['delete_on_dismantle'] = False
                self.base_config['standalone']['auto_dismantle'] = False
                self.base_config['lithops']['data_cleaner'] = False
            else:
                self.base_config['standalone']['auto_dismantle'] = True
                
                if answers['answer'] == DELETE_AFTER_FINISHED:
                    self.base_config['ibm_vpc']['delete_on_dismantle'] = True
                elif answers['answer'] == STOP_AFTER_FINISHED:
                    self.base_config['ibm_vpc']['delete_on_dismantle'] = False

            # TODO: set dismantle grace periods
            
        return self.base_config

    def create_default(self):

        self.base_config['standalone']['exec_mode'] = 'create'
        self.base_config['standalone']['auto_dismantle'] = True
        self.base_config['ibm_vpc']['delete_on_dismantle'] = True
        
        print(f"Dismantle policy set: {DELETE_AFTER_FINISHED}")
        
        return self.base_config