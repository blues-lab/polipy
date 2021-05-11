import logging, sys

def get_logger(verbose=False):
    logger = logging.getLogger('polipy')

    datefmt = '%Y-%m-%d %H:%M:%S'
    log_format = '[%(asctime)s] - %(levelname)-8s %(message)s'
    formatter = logging.Formatter(log_format, datefmt)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.INFO) if verbose else logger.setLevel(logging.WARNING)
    return logger
