import shutil
import json
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
from pathlib import Path
from SharedData.IO.AWSS3 import S3ListFolder, S3DeleteFolder, S3GetSession

from SharedData.SharedData import SharedData
shdata = SharedData(__file__, user='master')
from SharedData.Logger import Logger
from SharedData.MultiProc import io_bound_unordered
from SharedData.Metadata import Metadata

import concurrent.futures
from typing import Dict, Any, List

Logger.log.info('ROUTINE STARTED!')

def write_table(dftable_row: Dict[str, Any]) -> str:
    """Save a table from metadata and return status."""
    try:
        tablename = dftable_row['tablename']
        if dftable_row['partition'] != '':
            tablename = f"{dftable_row['tablename']}/{dftable_row['partition']}"
        tbl = shdata.table(
            dftable_row['database'],
            dftable_row['period'],
            dftable_row['source'],
            tablename
        )
        tbl.write(force_write=True)
        return f"Success: {tablename}"
    except Exception as e:
        Logger.log.error(f"Error saving {dftable_row} {e}")
        return f"Error: {dftable_row['tablename']} {e}"

# Load and filter table metadata
dftables = shdata.list_tables('')

saveidx = (dftables['last_modified_local'].notnull())
saveidx = saveidx & ((dftables['last_modified_local'] > dftables['last_modified_remote']) | (dftables['last_modified_remote'].isnull()))
saveidx = saveidx & (dftables['size_local'] > 1000)

Logger.log.info('Saving the following tables:')
for idx, row in dftables[saveidx].iterrows():
    Logger.log.info(idx)

to_save: List[Dict[str, Any]] = dftables[saveidx].to_dict(orient="records")

# Run in parallel using 8 processes
with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(write_table, to_save))


Logger.log.info('ROUTINE COMPLETED!')