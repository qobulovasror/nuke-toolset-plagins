## add plugin paths for active tools in local database
#import logging
import nuke
#import Nukepedia # for logger
from common import NKPDSettings, NKPD_DB_NAME
from model.NukepediaDBLocal import NPDBLocal

try:
    #logger = logging.getLogger('Nukepedia.init')
    __NPDB_LOCAL_DB = NPDBLocal(os.path.join(NKPDSettings().repoLocation, NKPD_DB_NAME))
    for p in __NPDB_LOCAL_DB.getPaths(pathType='pluginPath'):
        nuke.pluginAddPath(p)
except:
    # catch all to ensure Nuke starts
    print("ERROR",  sys.exc_info())
    #logger.critical('INIT ERROR: {}'.format(sys.exc_info()))
    pass
