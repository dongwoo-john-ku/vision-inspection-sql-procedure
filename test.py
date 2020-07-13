import logging
import logging.handlers

log = logging.getLogger('myLogger')
log.setLevel(logging.INFO)

formatter = logging.Formatter('[%(levelname)s] (%(filename)s:%(lineno)d) > %(message)s')
fileHandler = logging.FileHandler('./log.txt')
fileHandler.setFormatter(formatter)
log.addHandler(fileHandler)

if __name__ == '__main__':
    log.debug('debug')
    log.info('info')