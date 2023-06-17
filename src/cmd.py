"""run

Author: Ethan Hunt
Date: 2023-06-17
Version: 1.0

"""

import logging
import os

MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class cmd:
    def __init__(self):
        pass

    def run_script(program: str, script_path: str, script_name: str, parameters: str = None):
        program = program if isinstance(program, str) else None
        cmd_text = f'{program} {script_name}' if program is not None else script_name
        cmd_text = f'{cmd_text} {parameters}' if parameters is not None else cmd_text

        start_log = f'Begin {program} command "{cmd_text}"' if program is not None else f'Begin command "{cmd_text}"'
        end_log = f'End {program} command "{cmd_text}"' if program is not None else f'End command "{cmd_text}"'

        logging.debug(start_log)
        if os.getcwd != script_path:
            os.chdir(script_path)
        os.system('cmd /C ' + cmd_text)
        logging.debug(end_log)
