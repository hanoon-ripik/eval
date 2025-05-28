import logging

logger = logging.getLogger(__name__)

logging_level = 'info' 
logging_mode = 'console'
log_file_path = None

if logging_level == 'debug':
    logger.setLevel(logging.DEBUG)
elif logging_level == 'info':
    logger.setLevel(logging.INFO)
elif logging_level == 'warning':
    logger.setLevel(logging.WARNING)
elif logging_level == 'error':
    logger.setLevel(logging.ERROR)
else:
    print('Invalid logging level provided. Defaulting to INFO.')
    logger.setLevel(logging.INFO)

if logging_mode == 'file':
    if log_file_path is None:
        print('Log file not provided. Defaulting to console logging.')
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(log_file_path, mode='w')
elif logging_mode == 'console':
    handler = logging.StreamHandler()
else:
    print('Invalid logging mode provided. Defaulting to console.')
    handler = logging.StreamHandler()

handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s:\t%(message)s'))

logger.addHandler(handler)