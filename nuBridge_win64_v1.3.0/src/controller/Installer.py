import common
import logging
import os
import posixpath
import shutil
import sys
import zipfile
import common
#from PySide import QtCore, QtGui
from Qt import QtCore
from model.NukepediaDB import NPDB
from model.NukepediaDBLocal import NPDBLocal
from model.NKPD import ToolItemProxy
from view.FancyButton import FancyButtonSmall
logger = logging.getLogger('Nukepedia.Installer')

infoTextHoldingArea = '''
Nukepedia Bride - Holding Area
This is the destination folder that is used to download files via the Nukepedia Bridge.

If automatic installation is successful, copies of the files in this location are placed into a directory structure parallel to this one
for Nuke to load them from there.

The contents of this folder are monitored by the Nukepedia Bridge in order to provide information about available updates for installed tools.

To remove files please from this location please use the "Installed Tools" tab in the Settings dialog (gear button)
'''

def createNukepediaMenu():
    '''
    Create the Nukepepedia menu in Nuke's toolbar. This is run via from controller.menu.py
    as well as after relevant tools were installed to make the menu update immediately.
    '''
    try:
        import nuke
    except ImportError:
        logger.debug('Not running inside of Nuke. Failed to create Nukepedia menu')
        return
    logging.info('creating Nukepedia menu')
    nuke.menu('Nodes').addMenu('Nukepedia', icon=common.NKPD_MENU_ICON_PATH)

class Installer(QtCore.QObject):
    '''Download and install tools based on their type'''
    signalInstallProgress = QtCore.Signal(str)
    downloadFailed = QtCore.Signal(tuple)
    downloadSuccessful = QtCore.Signal(str)
    postDownloadInfo = QtCore.Signal(ToolItemProxy)
    installFailed = QtCore.Signal(tuple)
    installSuccessful = QtCore.Signal(tuple)
    downloadedTool = QtCore.Signal(ToolItemProxy) # not used in processor flow anymore, but could come in handy
    downloadQueueFinished = QtCore.Signal()

    def __init__(self, installObjects={}, settings=None, mainWidget=None):
        '''
        InstallObjects is a dictionary with a widget as keys and the tool items to instal for values.
        The widget must have a "setValue" method which updates a progressbar somewhere in the UI
        during download.
        This way the installer can be responsible for updating the respective progressbar during download,
        resetting it etc.
        '''
        super(Installer, self).__init__()
        self.mainWidget = mainWidget
        logger.debug('\n')
        logger.debug('*' * 10)
        logger.debug('*** CREATING NEW INSTALLER INSTANCE')
        #self.npdbInstance = npdbInstance
        #self.setTools(installObjects.values())
        self.installObjects = installObjects
        self.downloadOnly = settings.downloadOnly
        self.timeout = settings.timeOut
        self.maxThreadCount = settings.maxThreadCount
        self.setRootDir(settings.repoLocation)
        self.holdingAreaName = 'downloaded'
        self.holdingArea = posixpath.join(self.rootDir, self.holdingAreaName) # try to keep forward slashes for paths in DB to stay OS independent just in case
        self.dbFile = os.sep.join([self.rootDir, common.NKPD_DB_NAME])
        self.__connectPostDownloadProcesses()
        logger.debug('rootDir is: {0}'.format(self.rootDir))

    def __download(self, tool):
        '''download the tool list into the rootDir'''         
        def collectTool(tool):
            self.downloadedTools.append(tool)

        logger.debug('\n')
        downloadFolder = '_'.join([tool.title, str(tool.id_)])
        #holdingAreaWithID = os.path.join(self.holdingArea, downloadFolder, tool.version)
        # keep paths in DB OS independet by only using forward slashes.
        holdingAreaWithID = posixpath.join(self.holdingArea, downloadFolder, tool.version)
        tool.downloadPath = posixpath.relpath(posixpath.join(holdingAreaWithID, tool.fileName), self.rootDir)
        
        logger.debug('\t\t*** downloading {0} to {1}'.format(tool.title, holdingAreaWithID))
        logger.debug('tool data: {0}'.format(tool.toolData))

        self.signalInstallProgress.emit('downloading %s to %s' % (tool.title, holdingAreaWithID))
        self.taskQueue.worker.setTool(tool)
        self.taskQueue.worker.setTargetFolder(holdingAreaWithID)
        self.taskQueue.worker.connectionError.connect(self.mainWidget.ui.splashScreen.hide)
        self.taskQueue.worker.downloadedTool.connect(collectTool, type=QtCore.Qt.DirectConnection)
        self.taskQueue.start()

    def __connectPostDownloadProcesses(self):
        from Nukepedia import nkpd_post_download_processes

        for f in nkpd_post_download_processes:
            self.postDownloadInfo.connect(f)

    def __createHoldingArea(self):
        # create output folder and README file
        if not os.path.isdir(self.holdingArea):
            logger.debug('*** CREATING HOLDING AREA: {0}'.format(self.holdingArea))
            os.makedirs(self.holdingArea)

        readMeFilePath = os.path.join(self.holdingArea, '__README')
        if common.NKPD_PLATFORM == 'Windows':
            # add extension for windows so there is a sensible file association
            readMeFilePath += '.txt'
        if not os.path.isfile(readMeFilePath):
            logger.debug('*** README INHOLDING AREA')
            with open(readMeFilePath, 'w') as _fh:
                _fh.write(infoTextHoldingArea)

    def __getProcessor(self):
        '''
        Instantiate default processor or a custom one if it exists.
        Make sure it's signals are connected to the Installer so that
        it can report back anything we may need to log in the database
        '''
        from Nukepedia import npdb_custom_processor
        if not npdb_custom_processor:          
            from Processor import Processor
            # default processor
            processor = Processor(self.rootDir)
        else:
            # custom processor
            processor = npdb_custom_processor(self.rootDir)

        # connect processor to installer to report new file paths and menu commands for DB entry
        processor.newFilePathsReceived.connect(self.updateLocalDBWithPaths)
        processor.newPluginPathsReceived.connect(self.updateLocalDBWithPluginPaths)
        processor.newMenuInfo.connect(self.updateLocalDBWithMenuCommands)
        return processor

    def setRootDir(self, dirPath):
        '''root dir to install tools into'''
        self.rootDir = os.path.expanduser(dirPath)
        if not os.path.isdir(self.rootDir):
            os.makedirs(self.rootDir)

    def addToLocalDB(self, tool):
        '''
        record the downloads in the local database
        tool = ToolItem
        '''
        logger.debug('adding to local database: {}'.format(tool))
        
        # update the values that drive button decorators:
        tool.updateAvailable = False # this assumes that the downloaded file is the latest file - might have to adjust this absed on user feedback
        tool.hasBeenDownloaded = True

        self.npdbLocal = NPDBLocal(self.dbFile)
        self.npdbLocal.createTables() # only creates db file and table if it doesn't already exist
        self.curFileID = self.npdbLocal.insertTool(tool) # keep track of ID as it's needed for the processor to update the file with the local path
        self.npdbLocal.setToolVersionAsActive(self.curFileID) # mark downloaded tool file as active (and all peers as inactive to avoid unexpected results in Nuke)

    def install(self):
        '''download and install the requested tools'''
        self.__createHoldingArea()
        self.downloadErrors = []
        self.installErrors = []
        self.downloadedTools = []

        logger.debug('*** DOWNLOADING {0} file(s)...'.format(len(self.installObjects.values())))

        self.taskQueue = common.DBTaskQueue(self.mainWidget.npdbInstance,
                                            task='downloadFile',
                                            parent=self.mainWidget)

        non_existing_tool_count = 0

        for widget, versionList in iter(self.installObjects.items()):
            if not isinstance(widget, FancyButtonSmall):
                # unless we are installing from the drop stack don't run downloads asynchronously
                # a drop stack download means one version per widget
                self.taskQueue.pool.setMaxThreadCount(1)
            else:
                # for the drop stack set maximum threads to user setting (default = 5)
                self.taskQueue.pool.setMaxThreadCount(self.maxThreadCount)

            # versionList is a list of files belonging to the same tool
            for versionFile in versionList:
                if not versionFile.activeFile:
                    # tool no longer exists in the Nukepedia database, so skip it
                    logger.debug(u"Tool no longer exists: {}".format(versionFile.title))
                    non_existing_tool_count += 1
                    continue
                # create a new NPDB instance per download and hand over the required
                # attributes from the main NPDB instance
                npdbInstance_download = NPDB(self.timeout)
                npdbInstance_download.setUser(self.mainWidget.npdbInstance.uName)
                npdbInstance_download.setPwd(self.mainWidget.npdbInstance.passwd)
                npdbInstance_download.setMachineInfo(self.mainWidget.npdbInstance.machineInfo)
                try:
                    npdbInstance_download.fileDownloadProgress.connect(widget.setValue, QtCore.Qt.UniqueConnection)
                except RuntimeError:
                    # this makes sure signals are only ever connected once for each widget
                    # e.g. when the same drop stack is downloaded multiple times
                    pass
                # overwrite default runnable to ensure independent downloads and progress bars
                self.taskQueue.createNewRunnable(npdbInstance_download)
                self.__download(versionFile)

        # get total file download count so the queue knows when it's done
        totalDownloadCount = len([item for sublist in self.installObjects.values() for item in sublist]) - non_existing_tool_count
        self.taskQueue.setExpectedTaskCount(totalDownloadCount) # this tells the queue when it's finished
        self.taskQueue.queueIsFinished.connect(self.postInstallRoutines)

    def postInstallRoutines(self):
        '''Runs once per download queue'''
        # first run routines per tool:
        self.postInstallRoutinesPerTool()

        # now run the global routine
        logger.debug('>>>running post install for queue')
        self.mainWidget.ui.splashScreen.hide()

        if self.downloadErrors:
            # if this happens we need to do something about it
            self.downloadFailed.emit(('Download Error',
                                      '\n'.join(self.downloadErrors)))
        if self.installErrors:
            # some files could not be installed automatically
            postInstallMsg = 'The below files could not be installed automatically.\nPlease go to the download area and install them manually.\n'
            self.installFailed.emit((self.holdingArea,
                                     postInstallMsg,
                                     '\n'.join(self.installErrors)))
        else:
            # everything was installed fine
            postInstallMsg = 'The downloaded files can be found here:\n{0}'.format(self.holdingArea)
            if self.downloadOnly:
                postInstallMsg += '\n\nThe "download only" option is checked, so no installation occured.'
            self.installSuccessful.emit((self.holdingArea,
                                         postInstallMsg))

        # check if global init.py needs updating to point to Nukepedia repo
        logger.debug('checking user init file in {0}'.format(self.rootDir))       
        self.downloadQueueFinished.emit()

    def postInstallRoutinesPerTool(self):
        '''Runs once per downloaded tool'''
        for tool in self.downloadedTools:
            logger.debug('>>>running post install for tool {}'.format(tool))
            tool.hasBeenDownloaded = True
            self.addToLocalDB(tool)
            self.downloadSuccessful.emit(tool.container)
            self.postDownloadInfo.emit(tool) # for custom post download callbacks
            # then try to install via processor unless "download only" is checked in the options
            if not self.downloadOnly:
                try:
                    # let the Processor process the downloaded file and report back via signals (see __getProcessor for connections)
                    self.processDownloadedTool(tool)
                except IOError:
                    instErr = "<b>{0}</b>\t(id:{1}):<br>\t{2}<br>".format(tool.title, tool.id_, os.path.join(self.rootDir, tool.downloadPath))
                    self.installErrors.append(instErr)

    def processDownloadedTool(self, toolItem):
        '''Emit tool item so that the active processor can deal with it'''
        processor = self.__getProcessor() # reset processor each time for predictable results
        processor.setToolItem(toolItem) # set and process tool

    def updateLocalDBWithMenuCommands(self, menuInfoList):
        '''
        Log the menu command to be executed via the UI in the DB
        so it can be rebuild when Nuke starts up
        menuCommand  -  must be a valid Nuke command (string)
        '''
        for menuInfo in menuInfoList:
            menuCmd = u"""nuke.menu("Nodes").addCommand("Nukepedia/{title}", '''{command}''')""".format(**menuInfo)
            logger.debug('**** updating local DB with menu command:\n\t{}'.format(menuCmd))
            #self.npdbLocal.updateDBAttr(self.npdbLocal.TABLE_NAME_VERSIONS, self.curFileID)
            self.npdbLocal.addMenuCommandsForVersion(self.curFileID, [menuCmd])
            try:
                import nuke
                createNukepediaMenu()
                eval(menuCmd)
            except ImportError:
                # this happens when nuBridge is run from outside of Nuke
                # so we don't actually care about adding a plugin path
                pass

    def updateLocalDBWithPaths(self, pathList, pathType='filePath'):
        '''
        Record new file paths for the current tool version.
        These paths will be used for removing the tool version from the database
        as well as vor copying/moving the repository.
        The Processor is responsible for sending the required paths.
        Paths are recorded as relative paths in teh DB for flexibility and security
        '''
        logger.debug('**** updating local DB with new file paths: {}'.format(pathList))
        for p in pathList:
            self.npdbLocal.addPathForVersion(self.curFileID, os.path.relpath(p, self.rootDir), pathType=pathType)

    def updateLocalDBWithPluginPaths(self, pluginPathList):
        '''
        Record new plugin paths for the current tool version.
        These paths will be added to Nuke's plugin path on startup.
        The Processor is responsible for sending the required paths
        '''
        logger.debug('**** updating local DB with new plugin paths: {}'.format(pluginPathList))
        self.updateLocalDBWithPaths(pluginPathList, pathType='pluginPath')
        for pluginPath in pluginPathList:
            try:
                # load the new plugin path on the fly (inside of nuke)
                import nuke
                nuke.tprint('adding plugin path {}'.format(pluginPath))
                if pluginPath not in nuke.pluginPath():
                    nuke.pluginAddPath(pluginPath)
            except ImportError:
                # this happens when nuBridge is run from outside of Nuke
                # so we don't actually care about adding a plugin path
                pass