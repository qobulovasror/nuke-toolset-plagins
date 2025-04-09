import os
#import posixpath
import sys
import inspect
import logging
import platform

# current platform
NKPD_PLATFORM = platform.system()
# set up source code path for easy code flow
curDir = os.path.dirname(inspect.getfile(inspect.currentframe())) or os.path.abspath(os.path.curdir)
# if curDir is empty, this was run from the command line
#os.chdir(curDir) # FOR WINDOWS

NKPD_PROJECT_ROOT = os.path.dirname(curDir)
NKPD_LIB_PATH = os.path.join(NKPD_PROJECT_ROOT, 'lib')
NKPD_MENU_ICON_PATH = os.path.join(NKPD_PROJECT_ROOT, 'view', 'resources', 'icons', 'nuke', 'NukepediaMenuIcon.png')
#NKPD_SUPPORT_PATH = os.path.dirname(QtCore.QSettings(QtCore.QSettings.IniFormat,
                                                     #QtCore.QSettings.UserScope,
                                                     #"Nukepedia",
                                                     #"nuBridge").fileName())

# this path holds settings.ini, NKPD.log and keyring info if required
NKPD_SUPPORT_PATH = os.path.expanduser('~/.config/Nukepedia/nuBridge')
NKPD_DB_NAME = 'NukepediaDB.sqlite'

if not os.path.isdir(NKPD_SUPPORT_PATH):
    os.makedirs(NKPD_SUPPORT_PATH)

if NKPD_PROJECT_ROOT not in sys.path:
    sys.path.append(NKPD_PROJECT_ROOT)
if NKPD_LIB_PATH not in sys.path:
    sys.path.insert(0, NKPD_LIB_PATH) # insert instead of append to make sure to use included lib in case local versions exist

from Qt import QtCore, QtWidgets, IsPySide
import model.NukepediaDB
pyside_version = 2 - int(IsPySide)
from model.NukepediaDB import ConnectionError
from model.NKPD import ToolItemProxy
##################################################
# DEAL WITH LOGGING
logLevelDict = {'critical':logging.CRITICAL,
                'error':logging.ERROR,
                'warning':logging.WARNING,
                'info':logging.INFO,
                'debug':logging.DEBUG}

try:
    logEnvVal = os.environ['NKPD_LOG_LEVEL'].lower()
    FILE_LOG_LEVEL = logLevelDict.get(logEnvVal, None)
except KeyError:
    # no env var set, so let the main controller use the user settings
    FILE_LOG_LEVEL = None
##################################################

##################################################
# DEAL WITH REPO LOCATION
# get repo location from environment variable
REPO_PATH = os.environ.get('NKPD_REPO_PATH', None)
if REPO_PATH and NKPD_PLATFORM == 'Windows' and REPO_PATH[0].isdigit():
    # looks like we are dealing with a UNC PATH without leading slashes, lets add them
    REPO_PATH = '//' + REPO_PATH
##################################################

##################################################
# DEAL WITH DOWNLOAD ONLY SETTING
# get value from environment variable (value can be anything in this case)
DOWNLOAD_ONLY = os.environ.get('NKPD_DOWNLOAD_ONLY', False)
##################################################

##################################################
# DEAL WITH GIZMO BAKING
# get value from environment variable (valid values are 0, 1 and 2 which correspond to "per tool", "always" and "never")
BAKE_GIZMOS = os.environ.get('NKPD_BAKE_GIZMOS', None)
try:
    BAKE_GIZMOS = int(BAKE_GIZMOS)
    if BAKE_GIZMOS not in (0, 1, 2):
        # if an invalid value was found reset to the default value (per tool)
        BAKE_GIZMOS = None
except:
    # if an invalid value was found reset to the default value (per tool)
    BAKE_GIZMOS = None
##################################################

class NKPDSettings(QtCore.QSettings):
    '''Manage settings and default values'''

    timeOutChanged = QtCore.Signal(float)
    bakeGizmosChanged = QtCore.Signal(int)

    def __init__(self, path=os.path.join(NKPD_SUPPORT_PATH, 'settings.ini'), iniFormat=QtCore.QSettings.IniFormat):
        QtCore.QSettings.__init__(self, path, iniFormat)
        #self.setPath(QtCore.QSettings.IniFormat,
                     #QtCore.QSettings.UserScope,
                     #path
                     #)
        self.setFallbacksEnabled(False)    # File only, no fallback to registry
        self.__showToolTips = True
        self.boolDict = {'false':False,
                         'true':True}

    def __strToInt(self, value, defValue):
        if value:
            return int(value)
        else:
            return defValue

    def __strToFloat(self, value, defValue):
        if value:
            return float(value)
        else:
            return defValue
        
    # --- getters
    @property
    def bakeGizmos(self):
        if not BAKE_GIZMOS is None:
            return BAKE_GIZMOS
        val = self.value('options/bakeGizmos')
        if val:
            return int(val)
        else:
            return 0

    @property
    def repoLocation(self):
        if REPO_PATH:
            # environment variable is used so kust return that value
            return REPO_PATH

        else:
            # no environment variable found, so uread the settings file (or the default value)
            defaultPath = os.path.normpath(os.path.expanduser(os.path.join('~','Nukepedia'))).replace('\\', '/')
            return self.value('options/repoLocation') or defaultPath

    @property
    def scrollBarDirection(self):
        val = self.value('options/scrollBarDirection')
        if val:
            return int(val)
        else:
            return 0

    @property
    def showToolTips(self):
        return self.boolDict.get(self.value('options/showToolTips'), True)

    @property
    def downloadOnly(self):
        return bool(DOWNLOAD_ONLY) or self.boolDict.get(self.value('options/downloadOnly'), False)

    @property
    def maxThreadCount(self):
        return self.__strToInt(self.value('options/maxThreadCount'), 5)

    @property
    def timeOut(self):
        return self.__strToFloat(self.value('options/timeOut'), 10.0)  

    @property
    def writeLogs(self):
        if FILE_LOG_LEVEL:
            # environment variable is used so kust return that value           
            return self.__logLevelFromEnv
        else:
            # no environment variable found, so uread the settings file (or the default value)
            return self.boolDict.get(self.value('options/writeLogs'), False)

    
    def setBakeGizmos(self, value):
        self.setValue('options/bakeGizmos', value)
        self.bakeGizmosChanged.emit(value)

    def setDownloadOnly(self, value):
        if DOWNLOAD_ONLY:
            # environment variable is used, don't write anything to the settings file
            pass
        else:
            # no env variable is set so write value to settings file
            self.setValue('options/downloadOnly', bool(value))

    def setMaxThreadCount(self, value):
        self.setValue('options/maxThreadCount', value)

    def setRepoLocation(self, value):
        if REPO_PATH:
            # environment variable is used, don't write anything to the settings file
            return
        else:
            # no env variable is set so write value to settings file
            self.setValue('options/repoLocation', value)
        
    def setTimeOutValue(self, value):
        self.timeOutChanged.emit(float(value))
        self.setValue('options/timeOut', value)
    
    def setShowToolTips(self, value):
        self.setValue('options/showToolTips', bool(value))

    def setFileLogLevel(self, value):
        if FILE_LOG_LEVEL:
            # environment variable is used, don't write anything to the settings file
            self.__logLevelFromEnv = value
        else:
            # no env variable is set so write value to settings file
            self.setValue('options/writeLogs', bool(value))

    def setScrollBarDirection(self, value):
        self.setValue('options/scrollBarDirection', value)

def openSystemFileBrowser(p):
    '''Opens the system file browser'''

    import subprocess
    normPath = os.path.normpath(p) # needed for UNC paths
    if NKPD_PLATFORM == 'Darwin':  
        subprocess.Popen(['open', normPath])
    elif NKPD_PLATFORM == 'Linux':
        subprocess.Popen(['xdg-open', normPath])
    elif NKPD_PLATFORM == 'Windows':
        os.startfile(normPath)

def getToolItemProxies(toolItem, latestVersionsOnly=False, parent=None):
    '''
    Return a list of ToolItemProxies for each file in toolItem that was selected by the user in the file chooser.
    If latestOnly is True, only the latest file for the given tool is returned
    '''
    # not sure why I put those imports in here - keep an eye on this and clean up if possible
    from view.Dialogs import FileChoserWidget
    from model.NKPD import ToolItemProxy
    # if alt key is pressed, all files are shown, not just the one(s) belonging to the latest version

    latestVersions = toolItem.getLatestVersions()
    proxyList = [] # list of tool item proxies with active files set (needed when users want to download different builds of the same tool)

    if latestVersionsOnly and len(latestVersions) == 1:
        # there is only one file associated with the latest version, so simply use that
        toolProxy = ToolItemProxy(toolItem)
        toolProxy.activeFile = latestVersions[0]
        proxyList.append(toolProxy)
        
    else:
        w = FileChoserWidget(toolItem, latestOnly=latestVersionsOnly, mainUI=parent)
        if w.exec_():
            for f in w.fileView.getSelectedFiles():
                toolProxy = ToolItemProxy(toolItem)
                toolProxy.activeFile = f
                proxyList.append(toolProxy)

    return sorted(proxyList) #sort by file version

class DBTaskQueue(QtCore.QObject):
    queueIsFinished = QtCore.Signal()

    def __init__(self, npdbInstance, task=None, parent=None):
        QtCore.QObject.__init__(self, parent)
        #self.parent = parent
        self.npdbInstance = npdbInstance
        #self.startMonitor = False
        self.expectedTaskCount = 1
        self.finishedTasks = 0

        if task:
            self.setTask(task)
        self.pool = QtCore.QThreadPool()

    def cancel(self):
        self.worker.cancelled = True

    def createNewRunnable(self, npdbInstance):
        '''
        Overwrite the initial runnable to fill the same queue.
        Needed to force subsequent downloads rather than concurrent ones
        '''
        self.runnable = DBTaskManager(npdbInstance, self.task)
        self.worker = self.runnable.worker # for convenience in main code
        self.worker.finished.connect(self.monitorTasks)

    def monitorTasks(self):
        self.finishedTasks += 1
        if self.finishedTasks == self.expectedTaskCount:
            self.queueIsFinished.emit()
        #if self.startMonitor and (self.pool.activeThreadCount() == 0):
            #self.queueIsFinished.emit()
            #self.startMonitor = False

    def setExpectedTaskCount(self, taskCount):
        self.expectedTaskCount = taskCount

    def setTask(self, task):
        '''Sets the task or mode for the database instance'''
        self.task = task
        self.createNewRunnable(self.npdbInstance)

    def showConnectionError(self, message):
        '''Open a dialog to show connection errors'''
        msg = QtWidgets.QMessageBox()
        msg.critical(None, 'Connection Error', message, QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)

    def showObsoleteError(self):
        message = "This client version is obsolete.<br>Please download a new version from <a href='http://www.nukepedia.com/nubridge'>Nukepedia.com</a>"
        QtWidgets.QMessageBox.critical(None, 'Obsolete Client Version', message, QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)        

    def showOutOfDateWarning(self):
        message = "A newer version of nuBridge is available at <a href='http://www.nukepedia.com/nubridge'>Nukepedia.com</a>"
        QtWidgets.QMessageBox.warning(None, 'Client Out of Date', message, QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)        


    def start(self):
        '''Add task to queue and run it'''
        self.npdbInstance.wasCancelled = False
        self.runnable.worker.connectionError.connect(self.showConnectionError)
        self.runnable.worker.clientIsObsolete.connect(self.showObsoleteError)
        self.runnable.worker.clientIsOld.connect(self.showOutOfDateWarning)
        self.pool.start(self.runnable)

class DBTaskManager(QtCore.QRunnable):
    '''Mini interface to run the database queries in a consistent manner'''
       
    def __init__(self, npdbInstance, task):
        super(DBTaskManager, self).__init__()
        self.worker = DBTask(npdbInstance)
        self.task = getattr(self.worker, task)

    def run(self):
        self.task()


def makeThreadSafe(message):
    '''
    Decorator to check for cancelled signal, control signals for database wrapper
    and catch connection errors'''
    def addMessage(fn):
        def fn_wrapper(self):
            if not self.cancelled:
                self.progressInfo.emit(message)
                try:
                    fn(self)
                except ConnectionError as e:
                    self.connectionError.emit('{} ({})'.format(e, fn))
            else:
                self.npdb.wasCancelled = True
                self.wasCancelled.emit()
        return fn_wrapper
    return addMessage

class DBTask(QtCore.QObject):
    '''
    Wrapper to run database requests on a separate thread
    and report back with corresponding data via signals'''
    clientIsObsolete = QtCore.Signal()
    clientIsOld = QtCore.Signal()
    connectionError = QtCore.Signal(str)
    try:
        # Python2
        setFavResponse = QtCore.Signal(unicode)
        retrievedDescription = QtCore.Signal(unicode)
    except NameError:
        # Python3
        setFavResponse = QtCore.Signal(str)
        retrievedDescription = QtCore.Signal(str)
    finished = QtCore.Signal()
    downloadedTool = QtCore.Signal(ToolItemProxy)
    wasCancelled = QtCore.Signal()
    retrievedTools = QtCore.Signal(dict)
    retrievedNews = QtCore.Signal(str)
    retrievedFavorites = QtCore.Signal(list)
    retrievedKey = QtCore.Signal(str)
    retrievedLicense = QtCore.Signal(str)
    retrievedUserInfo = QtCore.Signal(dict)
    progressInfo = QtCore.Signal(str)
    
    
    def __init__(self, npdbInstance):
        super(DBTask, self).__init__()
        self.npdb = npdbInstance
        self.cancelled = False
        #self.wasCancelled.connect(self.deleteLater) # avoids crashes when logging in after a cancelled log in attempt
  
    def initAll(self):
        self.toolData = []
        maxLoopCount = 10
        loop = 1        
        while not self.toolData and loop <= maxLoopCount:
            # this loop is experimental to see if it fixes those random empty key returns
            # it also causes successful connections after timeout errors, so that needs to be fixed.
            #print 'current attempt:', loop
            self.getTools()
            loop += 1
        self.getNews()
        self.getFavorites()
        if not self.cancelled:
            # Once finished emit all the signals that might be of interest
            try:
                self.retrievedTools.emit(self.toolData)
                self.retrievedNews.emit(self.news)
                self.retrievedFavorites.emit(self.favs)
                self.finished.emit()
            except AttributeError:
                # this happens when there was a timeout error
                pass

    @makeThreadSafe('downloading file...')
    def downloadFile(self):
        self.npdb.downloadFile(self.tool.getDownloadData(),
                               True,
                               self.targetFolder)

        self.downloadedTool.emit(self.tool)
        self.finished.emit()

    @makeThreadSafe('retrieving tool data...')
    def getTools(self):
        self.toolData = self.npdb.getTools()
        
    @makeThreadSafe('retrieving license...')
    def getLicense(self):
        self.retrievedLicense.emit(self.npdb.getLicenseText(self.tools))
        self.finished.emit()

    @makeThreadSafe('checking for news...')
    def getNews(self):
        self.news = self.npdb.getNewsFlash()

    @makeThreadSafe('retrieving favorites...')
    def getFavorites(self):
        self.favs = self.npdb.getFavorites()

    @makeThreadSafe('checking user credentials...')
    def whoAmI(self):
        self.retrievedUserInfo.emit(self.npdb.whoAmI())
        self.finished.emit()

    @makeThreadSafe('checking user credentials...')
    def getKey(self):
        key = ""
        maxLoopCount = 10
        loop = 1
        while not key.startswith("-----BEGIN PUBLIC KEY-----") and not key.endswith("-----END PUBLIC KEY-----") and loop <= maxLoopCount:
            # this loop is experimental to see if it fixes those random empty key returns
            key = self.npdb.getKey() # hand shake with server code - sets "old" and "obsolete" attr for client version,
                                    # so that needs to be checked first to ensure we are dealing with a compatible client
            if self.npdb.isObsolete:
                self.clientIsObsolete.emit()
                # client version is not copmatible anymore, so there is nothign else to do...
                return
            if self.npdb.isOutOfDate:
                self.clientIsOld.emit()
            loop += 1
        self.retrievedKey.emit(key)
        self.finished.emit()
        
    @makeThreadSafe('retrieving tool description...')
    def getDescription(self):
        self.retrievedDescription.emit(self.npdb.getDescription(self.tool.id_))
        self.finished.emit()

    @makeThreadSafe('saving favorite list...')    
    def setFavorite(self):
        response = self.npdb.setFavorite(self.fav.id_,
                         self.fav.getOnlineData(),
                         self.fav.name,
                         self.fav.desc)
        self.setFavResponse.emit(response)
        self.finished.emit()        
    
    def setFav(self, fav):
        '''favorite list to save online'''
        self.fav = fav
    
    def setTargetFolder(self, path):
        '''Set the target folder for downloads'''
        self.targetFolder = path

    def setTool(self, tool):
        '''sets the tool to download or to retrieve description for'''

        self.tool = tool
        #print 'setting tool:', self.tool
        
    def setTools(self, *toolList):
        '''sets the list of tools for which to retrieve the licenses'''

        self.tools = toolList
