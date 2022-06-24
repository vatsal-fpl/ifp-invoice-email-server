from logger import get_logger


logger1 = get_logger('typeOne', 'logfile1.log')
logger2 = get_logger('typeTwo', 'logfile2.log')


def func_one():
    logger1.info("function one")
    print("function one")


def func_two():
    logger2.info("function two")
    print("function two")


func_one()
func_two()
