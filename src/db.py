"""db

Author: Ethan Hunt
Date: 2023-06-17
Version: 1.0

"""

import logging
import os
import shutil
import subprocess
import time

import pandas as pd
import pyodbc as sql

from .constants import BOOLEANS as BOOLEANS
from .misc import get_config as get_config

# TODO: Add general query execution stuff, will need injection defenses


class db_constants:
    MODULE_NAME = os.path.splitext(os.path.basename(__file__))[0]


class db:
    # only have tested this with SQL Server
    def __init__(self):
        self.conn = sql.connect(get_config(db_constants.MODULE_NAME, 'connectionString'))

    def __enter__(self):
        self.conn = sql.connect(get_config(db_constants.MODULE_NAME, 'connectionString'))
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.conn.close()

    def _is_job_running(self, job_name: str) -> str:
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
        return pd.read_sql(qry_text, self.conn).values[0][0]

    def run_job(self, job_name: str, wait_for_completion: bool = False):
        wait_for_completion = wait_for_completion if wait_for_completion in BOOLEANS else False
        csr = self.conn.cursor()
        csr.execute(f"EXEC msdb.dbo.sp_start_job @job_name = '{job_name}'")

        logging.debug(f'SQL job "{job_name}" started')
        if wait_for_completion:
            is_running = 1
            while is_running:
                time.sleep(10)
                is_running = self._is_job_running(job_name)
            logging.debug(f'SQL job "{job_name}" ended')

    def script_objects(self, root_path: str, server: str, database: str):
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
        os.system('cmd /C ' + cmd_text)
