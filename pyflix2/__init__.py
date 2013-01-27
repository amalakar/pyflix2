__title__ = 'pyflix2'
__version__ = '0.2.0'
__build__ = __version__
__author__ = 'Arup Malakar'
__license__ = 'BSD'
__copyright__ = 'Copyright 2012 Arup Malakar'

from pyflix2 import NetflixAPIV2, NetflixAPIV1, User, NetflixError, EXPANDS, SORT_ORDER, RENTAL_HISTORY_TYPE


def main():
    from pyflix2 import cmdline
    return cmdline.main()

if __name__ == '__main__':
    sys.exit(main())
