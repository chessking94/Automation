"""db

Author: Ethan Hunt
Creation Date: 2023-06-17

"""

import logging
import os
import shutil
import subprocess
import time

import pandas as pd
import pyodbc as sql

from . import BOOLEANS
from .misc import get_config


class db:
    """Class to handle processes related to databases

    Can be used directly or as a context manager

    Attributes
    ----------
    conn : Connection
        Object representing database connection

    Notes
    -----
    Only has been tested with SQL Server

    TODO
    ----
    Add general query execution stuff, will need injection defenses
    Rework how connection works, want it to take a custom connection string or key value for config
    Add ability to not immediately connect or require a connection string to use

    """
    def __init__(self, config_path: str = None):
        """Inits db class

        Parameters
        ----------
        config_path : str, optional (default None)
            Directory in which the library configuration file resides.

        Raises
        ------
        FileNotFoundError
            If config_path does not exist

        TODO
        ----
        Convert config_path to config_file, and parse it with dirname/basename

        """
        if not os.path.isdir(config_path):
            raise FileNotFoundError

        self.conn = sql.connect(get_config('db_connectionString', config_path))

    def close(self):
        """Closes a db object"""
        self.conn.close()

    def __enter__(self, config_path: str = None):
        """Opens a db object from a context manager"""
        if config_path and not os.path.isdir(config_path):
            raise FileNotFoundError

        self.conn = sql.connect(get_config('db_connectionString', config_path))
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Closes a db object opened with a context manager"""
        self.conn.close()

    def _is_job_running(self, job_name: str) -> bool:
        """Determines if a SQL Server job is still running

        Parameters
        ----------
        job_name : str
            Name of job to check if is running

        Returns
        -------
        bool : Whether or not the job is running

        """
        qry_text = f"""
SELECT
CASE WHEN act.stop_execution_date IS NULL THEN 1 ELSE 0 END AS is_running

FROM msdb.dbo.sysjobs job
JOIN msdb.dbo.sysjobactivity act ON
    job.job_id = act.job_id
JOIN msdb.dbo.syssessions sess ON
    sess.session_id = act.session_id
JOIN (
    SELECT
    MAX(agent_start_date) AS max_agent_start_date
    FROM msdb.dbo.syssessions
) sess_max ON
    sess.agent_start_date = sess_max.max_agent_start_date

WHERE job.name = '{job_name}'
    """
        logging.debug(qry_text)
        return bool(int(pd.read_sql(qry_text, self.conn).values[0][0]))

    def run_job(self, job_name: str, wait_for_completion: bool = False) -> bool:
        """Executes a SQL Server job

        Starts a SQL Server job and optionally waits for it to finish

        Parameters
        ----------
        job_name : str
            Name of job to run
        wait_for_completion : bool, optional (default False)
            Indicates if the script should pause executing until the job completes

        Returns
        -------
        bool : Whether the job is still running at the time the script ends

        """
        wait_for_completion = wait_for_completion if wait_for_completion in BOOLEANS else False
        csr = self.conn.cursor()
        csr.execute(f"EXEC msdb.dbo.sp_start_job @job_name = '{job_name}'")

        logging.debug(f'SQL job "{job_name}" started')
        is_running = True
        if wait_for_completion:
            while is_running:
                time.sleep(10)
                is_running = self._is_job_running(job_name)
            logging.debug(f'SQL job "{job_name}" ended')

        return is_running

    def script_objects(self, root_path: str, server: str, database: str) -> int:
        """Scripts SQL Server objects using mssql-scripter

        Starts a SQL Server job and optionally waits for it to finish

        Parameters
        ----------
        root_path : str
            Primary directory in which objects are scripted to. Actual scripting directory will be root/database
        server : str
            Name of server objects will be scripted from
        database : str
            Name of database objects will be scripted from

        Returns
        -------
        int : the same return value as os.system()

        Raises
        ------
        FileNotFoundError
            If root_path directory does not exists
            If mssql-script is not installed in the environment

        """
        if not os.path.isdir(root_path):
            raise FileNotFoundError(f"path '{root_path}' does not exist")

        try:
            subprocess.run(['mssql-scripter', '--version'], shell=True)
        except FileNotFoundError:
            raise FileNotFoundError('mssql-scripter is not installed in the environment')

        output_path = os.path.join(root_path, database)
        if os.path.isdir(output_path):
            shutil.rmtree(output_path)
        os.mkdir(output_path)

        cmd_text = f'mssql-scripter -S {server} -d {database}'
        cmd_text = cmd_text + ' --file-per-object'
        cmd_text = cmd_text + ' --script-create'
        cmd_text = cmd_text + ' --collation'
        cmd_text = cmd_text + ' --exclude-headers'
        cmd_text = cmd_text + ' --display-progress'
        cmd_text = cmd_text + f' -f {output_path}'
        if os.getcwd != root_path:
            os.chdir(root_path)
        rtnval = os.system('cmd /C ' + cmd_text)

        return rtnval
