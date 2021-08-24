import re
import inquirer
from inquirer import errors
import os


def get_option_from_list(msg, choices, default=None, choice_key='name', do_nothing=None):
    if(len(choices) == 0 and do_nothing==None):
        error_msg = f"There no option for {msg}"
        print(error_msg)
        raise Exception(error_msg)

    if(len(choices) == 1 and not do_nothing):
        return(choices[0])

    choices_keys = [choice[choice_key] for choice in choices]
    if do_nothing:
        choices_keys.insert(0, do_nothing)

    questions = [
            inquirer.List('answer',
                message=msg,
                choices=choices_keys,
                default=default,
            ),]
    answers = inquirer.prompt(questions)

    # now find the object by name in the list
    if answers['answer'] == do_nothing:
        return do_nothing
    else:
        return next((x for x in choices if x[choice_key] == answers['answer']), None)

def find_name_id(objects, msg, obj_id=None, obj_name=None, default=None, do_nothing=None):
    if obj_id:
        # just validating that obj exists
        obj_name = next((obj['name'] for obj in objects if obj['id'] == obj_id), None)
        if not obj_name:
            raise Exception(f'Object with specified id {obj_id} not found')
    if obj_name:
        obj_id = next((obj['id'] for obj in objects if obj['name'] == obj_name), None)

    if not obj_id and not obj_name:
        obj = get_option_from_list(msg, objects, default=default, do_nothing=do_nothing)
        if do_nothing and obj == do_nothing:
            return None, None

        obj_id = obj['id']
        obj_name = obj['name']

    return obj_name, obj_id

def validate_not_empty(answers, current):
    if not current:
        raise errors.ValidationError('', reason=f"Key name can't be empty")
    return True

def validate_exists(answers, current):
    if not current or not os.path.exists(os.path.abspath(os.path.expanduser(current))):
        raise errors.ValidationError('', reason=f"File {current} doesn't exist")
    return True

def get_region_by_endpoint(endpoint):
    return re.search('//(.+?).iaas.cloud.ibm.com', endpoint).group(1)

def find_default(template_dict, objects, name=None, id=None):
    val = None
    for k, v in template_dict.items():
        if isinstance(v, dict):
            return find_default(v, objects, name=name, id=id)
        else:
            if name:
                key = 'name'
                if k == name:
                    val = v
            elif id:
                key='id'
                if k == id:
                    val = v

            if val:
                obj = next((obj for obj in objects if obj[key] == val), None)
                if obj:
                    return obj['name']

def free_dialog(msg, default=None):
    question = [
        inquirer.Text('answer',
                      message=msg,
                      default=default)]
    answer = inquirer.prompt(question)
    return answer

def get_option_from_list_alt(msg, choices, instance_to_create=None, default=None, multiple_choice=False):
    """prompt options to user and returns user choice.
      :param str instance_to_create: when initialized to true adds a 'create' option that allows the user
                            to create an instance rather than to opt for one of the options."""
    if len(choices) == 0:
        raise Exception(f"No options were found to satisfy the following request: {msg}")

    if len(choices) == 1:
        print(f"\033[92mA single option was found in response to the request: '{msg}'. \n{choices[0]} was automatically chosen\n\033[0m")
        return {'answer': choices[0]}

    if instance_to_create:
        choices.append(f'Create a new {instance_to_create}')

    questions = [
        inquirer.List('answer',
                      message=msg,
                      choices=choices,
                      default=default,
                      )] if not multiple_choice else \
        [inquirer.Checkbox('answer',
                           message=msg,
                           choices=choices,
                           default=default,
                           )]

    answers = inquirer.prompt(questions)

    while not answers['answer'] and multiple_choice:
        print("You must choose at least one option.\n"
              "To pick an option please use the right arrow key '->' to select and the left arrow key '<-' to cancel.")
        answers = inquirer.prompt(questions)

    return answers
