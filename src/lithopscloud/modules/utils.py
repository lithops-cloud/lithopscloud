import os
import re
import subprocess
import sys
import tempfile
import time
from enum import Enum
import inquirer
from inquirer import errors

CACHE = {}
NEW_INSTANCE = 'Create a new'  # guaranteed substring in every 'create new instance' option prompted to user.


def get_option_from_list(msg, choices, default=None, choice_key='name', do_nothing=None, validate=True, carousel=True):
    if (len(choices) == 0 and do_nothing == None):
        error_msg = f"There no option for {msg}"
        print(error_msg)
        raise Exception(error_msg)

    if (len(choices) == 1 and not do_nothing):
        return (choices[0])

    choices_keys = [choice[choice_key] for choice in choices]
    if do_nothing:
        choices_keys.insert(0, do_nothing)

    questions = [
        inquirer.List('answer',
                      message=msg,
                      choices=choices_keys,
                      default=default,
                      validate=validate,
                      carousel=carousel,
                      ), ]
    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)

    # now find the object by name in the list
    if answers['answer'] == do_nothing:
        return do_nothing
    else:
        return next((x for x in choices if x[choice_key] == answers['answer']), None)


def find_name_id(objects, msg, obj_id=None, obj_name=None, default=None, do_nothing=None):
    if obj_id:
        # just validating that obj exists
        obj_name = next((obj['name']
                         for obj in objects if obj['id'] == obj_id), None)
        if not obj_name:
            raise Exception(f'Object with specified id {obj_id} not found')
    if obj_name:
        obj_id = next((obj['id']
                       for obj in objects if obj['name'] == obj_name), None)

    if not obj_id and not obj_name:
        obj = get_option_from_list(
            msg, objects, default=default, do_nothing=do_nothing)
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
        raise errors.ValidationError(
            '', reason=f"File {current} doesn't exist")
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
                key = 'id'
                if k == id:
                    val = v

            if val:
                obj = next((obj for obj in objects if obj[key] == val), None)
                if obj:
                    return obj['name']


def free_dialog(msg, default=None, validate=True):
    question = [
        inquirer.Text('answer',
                      message=msg,
                      default=default,
                      validate=validate)]
    answer = inquirer.prompt(question, raise_keyboard_interrupt=True)
    return answer


def get_confirmation(msg, default=None):
    questions = [
        inquirer.Confirm('answer',
                         message=msg,
                         default=default,
                         ), ]
    answer = inquirer.prompt(questions, raise_keyboard_interrupt=True)

    return answer


def get_option_from_list_alt(msg, choices, instance_to_create=None, default=None, carousel=True):
    """prompt options to user and returns user choice.
      :param str instance_to_create: when initialized to true adds a 'create' option that allows the user
                            to create an instance rather than to opt for one of the options."""

    if instance_to_create:
        choices.insert(0, color_msg(f'Create a new {instance_to_create}', style=Style.ITALIC))

    if len(choices) == 0:
        raise Exception(
            f"No options were found to satisfy the following request: {msg}")

    if len(choices) == 1:
        if instance_to_create:
            print(color_msg(f"\nNo existing instances were found in relation to the request: "
                            f"'{msg}'. Create a new one to proceed. ", color=Color.RED))
        else:
            print(color_msg(f"single option was found in response to the request: '{msg}'."
                            f" \n{choices[0]} was automatically chosen\n", color=Color.ORANGE))
            return {'answer': choices[0]}

    questions = [
        inquirer.List('answer',
                      message=msg,
                      choices=choices,
                      default=default,
                      carousel=carousel
                      )]

    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)

    return answers


def retry_on_except(retries, sleep_duration):
    """A decorator that calls the decorated function up to a number of times equals to 'retires' with a given
      'sleep_duration' in between"""

    def retry_on_except_warpper(func):
        def func_wrapper(*args, **kwargs):
            function_name = func.__name__

            for retry in range(retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    msg = f"Error in {function_name}, {e}, retries left {retries - retry - 1}"
                    print(color_msg(msg, color=Color.RED))

                    if retry < retries - 1:  # avoid sleeping after last failure
                        time.sleep(sleep_duration)
            print(color_msg(f"\nConfig tool was terminated, "
                            f"as it can't progress without the successful activation of {function_name}",
                            color=Color.RED))
            sys.exit()

        return func_wrapper

    return retry_on_except_warpper


def test_config_file(config_file_path):
    """testing the created config file with a simple test  """

    # small buffer size forces the process not to buffer the output, thus printing it instantly.
    process = subprocess.Popen(f"lithops test -c {config_file_path}", stdout=subprocess.PIPE, bufsize=1, shell=True)
    for line in iter(process.stdout.readline, b''):
        print(line.decode())
    process.stdout.close()
    process.wait()


def verify_path(path, verify_input_file: 'bool'):
    """:returns a valid path file to an existing input file if verify_input_file is true,
        else returns a valid output path for the resulting config file"""

    def _is_valid_input_path():
        if not os.path.isfile(path):
            print(color_msg(f"\nError - Path: '{path}' doesn't point to a file. ", color=Color.RED))
            return False
        return True

    def _is_valid_output_path():
        prefix_directory = path.rsplit('/', 1)[0]
        if os.path.isdir(prefix_directory):
            return path
        else:
            print(color_msg(f"{prefix_directory} doesn't lead to an existing directory", color=Color.RED))
            return False

    if verify_input_file:
        default_config_file = ''
        verify_func = _is_valid_input_path
        request = "Provide a path to your existing config file, or leave blank to configure from template"
        default_msg = '\nDefault input file was chosen\n'
    else:
        default_config_file = tempfile.mkstemp(suffix='.yaml')[1]
        verify_func = _is_valid_output_path
        request = "Provide a custom path for your config file, or leave blank for default output location"
        default_msg = '\nDefault output path was chosen\n'

    while True:
        if not path:
            print(color_msg(default_msg, color=Color.LIGHTGREEN))
            return default_config_file

        if verify_func():
            return path
        else:
            path = free_dialog(request)['answer']


def color_msg(msg, color=None, style=None, background=None):
    """reformat a given string and returns it, matching the desired color,style and background in Ansi color code.
        parameters are Enums of the classes: Color, Style and Background."""

    init = '\033['
    end = '\033[m'
    font = ''

    if color:
        font += color.value

    if style:
        font = font + ';' if font else font
        font += style.value

    if background:
        font = font + ';' if font else font
        font += background.value

    return init + font + 'm' + msg + end


class Color(Enum):
    BLACK = '30'
    RED = '31'
    GREEN = '32'
    BROWN = '33'
    BLUE = '34'
    PURPLE = '35'
    CYAN = '36'
    LIGHTGREY = '37'
    DARKGREY = '90'
    LIGHTRED = '91'
    LIGHTGREEN = '92'
    YELLOW = '93'
    LIGHTBLUE = '94'
    PINK = '95'
    LIGHTCYAN = '96'


class Style(Enum):
    RESET = '0'
    BOLD = '01'
    DISABLE = '02'
    ITALIC = '03'
    UNDERLINE = '04'
    REVERSE = '07'
    STRIKETHROUGH = '09'


class Background(Enum):
    BLACK = '40'
    RED = '41'
    GREEN = '42'
    ORANGE = '43'
    BLUE = '44'
    PURPLE = '45'
    CYAN = '46'
    LIGHTGREY = '47'
