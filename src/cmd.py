"""cmd

Author: Ethan Hunt
Date: 2023-06-17
Version: 1.0

"""

import logging
import os


class cmd_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class cmd:
    def __init__(self):
        pass

    def run_script(self, program_name: str, script_path: str, script_name: str, parameters: str = None) -> int:
        if not os.path.isdir(script_path):
            raise FileNotFoundError

        if not os.path.isfile(os.path.join(script_path, script_name)):
            raise FileNotFoundError

        program_name = program_name if isinstance(program_name, str) else None
        cmd_text = f'{program_name} {script_name}' if program_name is not None else script_name
        cmd_text = f'{cmd_text} {parameters}' if parameters is not None else cmd_text

        start_log = f'Begin {program_name} command "{cmd_text}"' if program_name is not None else f'Begin command "{cmd_text}"'
        end_log = f'End {program_name} command "{cmd_text}"' if program_name is not None else f'End command "{cmd_text}"'

        logging.debug(start_log)
        if os.getcwd != script_path:
            os.chdir(script_path)
        rtnval = os.system('cmd /C ' + cmd_text)
        logging.debug(end_log)

        return rtnval

    def run_command(self, command: str, command_path: str = None) -> int:
        if not command:
            raise RuntimeError('command not provided')

        if command_path is None:
            command_path = os.getcwd()

        if not os.path.isdir(command_path):
            raise FileNotFoundError(f'invalid path: {command_path}')

        logging.debug(command)
        if os.getcwd != command_path:
            os.chdir(command_path)
        rtnval = os.system('cmd /C ' + command)

        return rtnval
