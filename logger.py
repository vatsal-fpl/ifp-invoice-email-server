import logging


def get_logger(name):
    logger = logging.getLogger(name=name)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('logfile.log')
    formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)
    # add file handler to logger
    logger.addHandler(file_handler)
    return logger
