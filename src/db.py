"""db

Author: Ethan Hunt
Date: 2023-06-17
Version: 1.0

"""

import logging
import os
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
