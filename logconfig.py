# dedicated logging file
# https://stackoverflow.com/questions/6386698/how-to-write-to-a-file-using-the-logging-python-module
import logging
import sys
import os

from requests.models import Response
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

# NOTE: Standard Output Logging and File Logging Output are enabled with relevant file handlers
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)
# TODO: Add support for home directory path, see other scripts where it is done
# python3 is not recognizing ~ for home directory so use os.path.expanduser
local_path = os.path.expanduser('~/dev/node-python/tech-tracker/logs/tech-tracker.log')
file_handler = logging.FileHandler(local_path)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
# disabling standard output
# logger.addHandler(stdout_handler)
logger.info('** info logging enabled **')
