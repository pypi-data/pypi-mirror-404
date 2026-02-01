import os
import time
import random
import json
import requests
import boto3
import pandas as pd

from SharedData.Metadata import Metadata  
from SharedData.Logger import Logger
from SharedData.Routines.WorkerLib import *
Logger.connect(__file__)


Logger.log.info('ROUTINE STARTED!')

own_ip = get_own_ip()

# Use IP as the identifier instead of COMPUTERNAME for consistency with initial description
own_id = os.environ.get('COMPUTERNAME', own_ip)
own_id = own_id.replace('.','#')

cluster_folder = 'CLUSTERS/MASTER/'
own_path = f'{cluster_folder}{own_id}'
init_worker_election(own_path, own_ip, own_id)

# Variables for master confirmation
master_count = 0

while True:
    # Add random jitter
    jitter = random.uniform(0, 2)
    time.sleep(jitter)
    
    run_worker_election(cluster_folder, own_path, own_id, own_ip)

    # Sleep to make loop ~15 seconds total
    time.sleep(15 - jitter)