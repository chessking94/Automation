"""cmd

Author: Ethan Hunt
Creation Date: 2023-06-17

"""

import logging
import os


class cmd_constants:
    """A class for constants necessary for the cmd module"""
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class cmd:
    """Windows cmd prompt wrapper to execute commands. More focused than simply os.system() usage"""
    def __init__(self):
        pass

    def run_script(self, program_name: str, script_path: str, script_name: str, parameters: str = None) -> int:
        """Execute scripts or programs

        Parameters
        ----------
        program_name : str
            Name of external program to use to run the script or executable
        script_path : str
            The directory in which the script or executable resides
        script_name : str
            The name of the script or executable to run
        parameters : str, optional (default None)
            Custom parameters for the program to use

        Returns
        ----------
        int : the same return value as os.system()

        Raises
        ----------
        FileNotFoundError
            If the script_path location does not exist in the file system
            If the script_name file does not exist at the script_path location in the file system

        Examples
        ----------
        >>> print(run_script('python', 'C:/Windows', 'test.py'))
        0

        """
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

    def run_command(self, command: str, command_path: str = os.getcwd()) -> int:
        """Execute a command via cmd prompt

        Parameters
        ----------
        command : str
            The actual command text to run
        command_path : str, optional (default current working directory)
            The directory in which the command is to be run

        Returns
        -------
        int : the same return value as os.system()

        Raises
        ------
        RuntimeError
            If no command is provided
        FileNotFoundError
            If the command_path location does not exist in the file system

        Examples
        ----------
        >>> cmd_text = 'echo test >> test.txt'
        >>> print(run_command(cmd_text))
        0

        """
        if not command:
            raise RuntimeError('command not provided')

        if not os.path.isdir(command_path):
            raise FileNotFoundError(f"invalid path: '{command_path}'")

        logging.debug(command)
        if os.getcwd != command_path:
            os.chdir(command_path)
        rtnval = os.system('cmd /C ' + command)

        return rtnval
