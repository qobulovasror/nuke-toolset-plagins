#!/usr/bin/python

################################################################################
# Nukepedia NukeBridge interface
# written by Frank Rueter with heavy mentoring by Aaron Richiger (2012)
# Server side programming by Paul McInnes
#
#
# Huge thanks for help with code and design go out to:
# Ivan Busquets, Jan Dubberke, Aaron Richiger, Tibold Kandrai, Sebastian Elsner, Johan Aberg


__author__  = 'Frank Rueter'
__version__ = '1.3.0' # this drives build/release versioning, so keep it up-to-date

from distutils.version import LooseVersion
import inspect
import sys
import os
import logging
import common
import webbrowser
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets
from compat import uni_str, range

### set up paths for code flow
sys.path.append(common.NKPD_PROJECT_ROOT)
sys.path.insert(0, common.NKPD_LIB_PATH) # insert instead of append to make sure to use included lib in case local versions exist

##########################################
####### set up logger ####
# set up root logger
logger = logging.getLogger('Nukepedia')
logger.setLevel(logging.INFO)

# configure file handler
fileHandler = logging.FileHandler(os.path.join(common.NKPD_SUPPORT_PATH, 'NKPD.log'), mode='w')
formatter_file = logging.Formatter('||NKPD|%(asctime)s|%(filename)s|%(levelname)s|LINE %(lineno)d: %(message)s')
fileHandler.setFormatter(formatter_file)
# configure console handler
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.CRITICAL)
formatter_console = logging.Formatter('||NKPD|%(filename)s|%(levelname)s| %(message)s')
consoleHandler.setFormatter(formatter_console)
# add handlers
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)
##########################

logger.debug('python path is: {0}'.format(sys.path))
logger.debug('project root is: {0}'.format(common.NKPD_PROJECT_ROOT))
logger.debug('path for 3rd party packages is {0}'.format(common.NKPD_LIB_PATH))

try:
    # ADD PLUGIN PATH TO NUKE ENVIRONMENT SO MENU.PY IS READ
    import nuke
    nuke.pluginAddPath(os.path.sep.join([common.NKPD_PROJECT_ROOT, 'controller']), addToSysPath=False)

except ImportError:
    logger.debug('Not running inside of Nuke')
    pass

from model.NKPD import ToolModel, ToolModelLocal, ToolProxyModel, NkpdFavorite, ToolItem, ToolItemProxy, FileItem, OBSOLETE_TOOL_DATA
from model.NukepediaDB import PLATFORM_KEY, NPDB, strToObj
from model.NukepediaDBLocal import NPDBLocal 
from view.MainWindow import MainWindow
from view.WidgetPage import WidgetPage
from view.Dialogs import SaveNewFavoriteDialog, MessageBox, PostInstallDialog
from view.FancyButton import FancyButtonSlotHolder, OperationButton
from view.LicenseAgreement import LicenseAgreementBox
from view.Buttons import ToolPushButton
from view.resources import ICON_CACHE
from LoginController import LoginController
from Installer import Installer
from controller.Processor import ProcessorBase

class MiscEventFilter(QtCore.QObject):
    """Event filter that installs and uninstalls via the enter/leave events respectively.
    !!!!!!!!!!!!!!!!!!!!
    NOT IN USE AS NUKE 13 CAUSES WEIRD RECURSION ERRORS WITH THIS
    !!!!!!!!!!!!!!!!!!!!
    """

    def __init__(self, ui):
        super(MiscEventFilter, self).__init__()
        self.ui = ui

    def eventFilter(self, widget, event):
        #widgetUnderPointer = QtWidgets.QApplication.instance().widgetAt(QtGui.QCursor.pos())
        #if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            #print widgetUnderPointer

        if event.type() == QtCore.QEvent.Type.ToolTip:
            # suppress tooltips if option is unchecked
            return (not self.ui.settingsDialog.optionsTab.showToolTipsWidget.isChecked())
        return super(MiscEventFilter, self).eventFilter(widget, event)

class LoadFavAction(QtWidgets.QAction):
    favoriteListLoaded = QtCore.Signal(list)

    def __init__(self, icon, text, parent):
        '''
        This class is a band aid because in PySide 1.2.1 and later, using a QtGui.QStandardItem
        as data to a QtWidgets.QAction doesn't work anymore.
        '''
        super(LoadFavAction, self).__init__(icon, text, parent)
        self.toolItemProxies = []
        self.triggered.connect(self.emitFavLoadedSignal)

    def setToolList(self, toolItemProxies):
        self.toolItemProxies = toolItemProxies

    def emitFavLoadedSignal(self):
        self.favoriteListLoaded.emit(self.toolItemProxies)


class ToolBrowser(QtWidgets.QWidget):
    '''Panel to browse tools in online repository'''

    aboutToClose = QtCore.Signal() # signal to emit so all running threads can be closed gracefully

    def __init__(self, parent=None):
        '''Wrap the MainWindow as a widget so the whole app can be wrapped as a Nuke panel'''

        super(ToolBrowser, self).__init__(parent)  
        self.setObjectName('Nukepedia Tool Browser')
        self.setWindowIcon(ICON_CACHE.getPixmap("NukepediaLogo_bridge"))
        self.sortDict = {'category':'category', 'name':'title', 'downloads':'downloads', 'date':'modDate', 'author':'author' }
        self.settings = common.NKPDSettings()
        #print 'repo location:', self.settings.repoLocation
        self.ui = MainWindow()
        self.__initRepoLocation()
        self.__setLogLevel()
        self.readSettings()
        #QtWidgets.QApplication.instance().focusChanged.connect(test)

        # Set up models now so the local model can be filled before the login process
        self.setupModels()
        # Get local data (installed tools in local SQLite database)
        self.getLocalToolData()
        # Now that the local database is initialised, let's back it up
        self.npdbLocal.backup()

        self.npdbInstance = NPDB(timeout=self.settings.timeOut)
        self.dbTaskQueue = common.DBTaskQueue(self.npdbInstance, parent=self)
        self.loginController = LoginController(self.ui.loginPage, self)

        self.connectSignalsWithSlots()

        self.setupUi()
        self.__setVersion()
        #self.eFilter = MiscEventFilter(self.ui)  
        self.setTabOrder(self.ui, self)

    def __cancelRequest(self):
        self.dbTaskQueue.cancel()
        self.ui.statusBar().showMessage('log in cancelled')

    def __updateLocalToolItem(self, item):
        '''
        Change the attributes for the incoming item in the local database.
        I.e. If the file item is being activated, make sure siblings (rows with same toolID) are unchecked.
        Update the database for all siblings.
        Also update bakeGizmo attributes according to the local DB table view
        
        This would probably be a lot easier if I used QT's SQL model...
        '''

        logger.debug('*** Adjusting active file states')
        model = item.model()
        logger.debug('*** GETTING LOCAL TOOL DATA...')
        
        changedColumn = model.headerLabels[item.column()]

        fileIdColumn = model.headerLabels.index('file id')
        toolIdColumn = model.headerLabels.index('tool id')
        toolId = model.item(item.row(), toolIdColumn).text()
        fileId = model.item(item.row(), fileIdColumn).text()

        if changedColumn == 'active':
            # set active file
            self.npdbLocal.updateActiveState(fileId, bool(item.checkState()))
    
            if item.checkState() == QtCore.Qt.Unchecked:
                # if a file is deactivated don't do anything to the other checkboxes
                # just update the database
                return
    
            # item is being checked, so let's uncheck all siblings and update the database accordingly
            for r in range(model.rowCount()):
                if r == item.row():
                    # don't do anything in the current row
                    continue
                if model.item(r, toolIdColumn).text() == toolId:
                    sibling = model.item(r, item.column())
                    sibling.setCheckState(QtCore.Qt.Unchecked) # handle check state
                    siblingID = model.item(r, fileIdColumn).text()
                    self.npdbLocal.updateActiveState(siblingID, bool(sibling.checkState())) # update database
                    
        elif changedColumn == 'bake gizmo':
            # change bake gizmo behaviour
            bakeGizmoColumn = model.headerLabels.index('bake gizmo')
            self.npdbLocal.updateGizmoBakeAttr(fileId, bool(item.checkState()))

    def __checkAndSetRepoFolder(self):
        '''Check if the repo folder chosen via the UI already contains a database file and react accordingly.'''
        
        def cancelRepoChange():
            self.ui.settingsDialog.optionsTab.resetRepoPath()

        def moveRepo():
            self.npdbInstance.getPluginPaths()
            print("moving")
            return True # ensures that the new path is saved in the settings

        def copyRepo():
            print("copying")
            return True # ensures that the new path is saved in the settings

        def newRepo():
            print("new repo")
            return True # ensures that the new path is saved in the settings

        def useExistingRepo(path):
            print("use existing repo")
            return True # ensures that the new path is saved in the settings

        repoPath = self.ui.settingsDialog.optionsTab.repoLocationPath.text()
        w = QtWidgets.QMessageBox()
        if os.path.isfile(os.path.join(repoPath, common.NKPD_DB_NAME)):
            # there is already a database in the folder so offer to use it
            ret = w.warning(self,
                      "Warning",
                      "This folder already contains a repository.\nUse existing database?",
                      QtWidgets.QMessageBox.No,
                      QtWidgets.QMessageBox.Yes)
            if ret == QtWidgets.QMessageBox.No:
                cancelRepoChange()
            elif ret == QtWidgets.QMessageBox.Yes:
                useExistingRepo(repoPath)
                self.settings.setRepoLocation(repoPath)
            return
        else:
            # folder is clean so offer apropriate options
            w.setText("What should happen with the old repository?")
            w.addButton('Copy', QtWidgets.QMessageBox.YesRole)
            w.addButton('Move', QtWidgets.QMessageBox.NoRole)
            w.addButton('New', QtWidgets.QMessageBox.AcceptRole)
            w.addButton('Cancel', QtWidgets.QMessageBox.RejectRole)
            ret = w.exec_()

            fnDict = {'Copy':copyRepo,
                      'Move':moveRepo,
                      'New':newRepo,
                      'Cancel':cancelRepoChange}

            if fnDict[w.clickedButton().text()]():
                # if the function returns True we change the repo path in the settings
                self.settings.setRepoLocation(repoPath)

    def __initRepoLocation(self):
        '''
        Check environment for NKPD_REPO_PATH and set the repo path accordingly.
        If the env variable does not exist activate the user setting and use that (default)
        Create the directory if it doesn't exist.
        '''
        
        if common.REPO_PATH:
            # repo path has been set via the environment variable, so use that and disable user settings
            #self.ui.settingsDialog.optionsTab.repoLocationBtn.setDisabled(True)
            self.ui.settingsDialog.optionsTab.repoLocationPath.setText(common.REPO_PATH)
            self.ui.settingsDialog.optionsTab.repoLocationPath.setDisabled(True)
            self.settings.setRepoLocation(common.REPO_PATH)
        else:
            # no valid env variable found, so let the user settings dictate the path
            #self.ui.settingsDialog.optionsTab.repoLocationBtn.setDisabled(False)
            #self.ui.settingsDialog.optionsTab.repoLocationPath.setDisabled(False)
            pass

        if not os.path.isdir(self.settings.repoLocation):
            os.makedirs(self.settings.repoLocation)

    def __getProxyFromFileData(self, fileData):
        '''
        Take file data from database and return the respective ToolItemProxy based on current model data.
        fileData example: {'platform': '000010000', 'version': '1.0', 'id': 1889}
        '''
        toolId = fileData['id']
        try:
            toolItem = self.model.getToolById(toolId)
            proxy = ToolItemProxy(toolItem)
            proxy.setActiveFileByData(fileData)
        except IndexError:
            '''
            Tool id does not exist. Insert placeholder.
            This is necessary to be able to load favorites
            that include tools that have been deleted from the data base.
            '''
            obsData = OBSOLETE_TOOL_DATA.copy()
            obsData['id'] = toolId
            proxy = ToolItemProxy(ToolItem(OBSOLETE_TOOL_DATA['category'], obsData))
        return proxy

    def __reportABug(self):
        bodyText = 'platform: {}'.format(sys.platform)
        bodyText += '\nnuBridge version: {}'.format(__version__)
        bodyText += '\n\nissue:'
        bodyText += '\n\n\nsteps to reproduce:' + '\n' * 5
        import webbrowser
        webbrowser.open('mailto:frank@nukepedia.com?Subject=[nuBridge Feedback]&Body={}'.format(bodyText))
        #QDesktopServices.openUrl('mailto:frank@nukepedia.com?Subject=[nuBridge Feedback]&Body={}'.format(bodyText))

    def __loginViaMenu(self):
        '''
        This is called via the login option in the settings menu.
        The easiest way to call the same routines is to set the sync
        the login page with the login widget.
        NOTE: THIS IS CURRNETLY DISABLED AS IT DOESN'T SEEM TO BE OF ANY REAL BENEFIT
        '''
        #self.loginController.loginPage.username.setText(self.ui.optionsMenu.loginWidget.username.text())
        #self.loginController.loginPage.password.setText(self.ui.optionsMenu.loginWidget.password.text())
        #self.loginController.loginPage.password.storePwd()
        #self.loginController.loginMonitor()
        pass

    def __logOut(self):
        '''Log out and revert back to log in page'''
        logger.debug('*** LOGGING OUT')

        self.model = ToolModel()  # reset model that holds online tool data
        self.ui.showLoginPage()
        self.loginController.setWidgetVisibility(True)
        self.ui.introPanel.setViewA(self.ui.loginPage) # re-assign login page to page fader
        self.ui.introPanel.showViewA()
        try:
            self.ui.pageAnimator.visibleWidget.hide() # this should be None but hiding seems to work nicely
        except AttributeError:
            # self.ui.pageAnimator.visibleWidget has not been set yet
            # which means the user is logging out before pulling down a tool page
            pass
        self.ui.pageAnimator.end = 0

    def __decorateToolButtons(self):
        '''
        Check toolItem if it exists in local database and compare it's modified date with the local version's downloaded date.
        If the modified date of toolItem is more recent then the local tool's download date, assign "updatedAvailable" key to data
        and set it to True, otherwise assign it and set it to False.
        Also update local database to include up-to-date info for "updateAvailable" attribute.
        '''

        #logger.debug('local containers: {0}'.format(self.toolDataLocal.keys()))
        localContainers = set(proxyItem.container for proxyItem in self.localToolProxyList)
        logger.debug('local containers: {0}'.format(localContainers))
        for onlineContainer, onlineToolList in iter(self.toolDataOnline.items()):
            # CHECK TOOLS FOR AVAILABLE UPDATES AND ASSIGN 'updateAvailable' KEY TO TOOL DATA
            # WITH RESPECTIVE VALUE
            logger.debug('resetting marked tools for {0}'.format(onlineContainer))
            markedToolList = []
            #if onlineContainer not in localContainers:
                ## the local conateiner is not even in the local database
                ## so there can't be a sibling
                #continue
            for onlineTool in onlineToolList:
                # LOOP OVER ALL ONLINE TOOLS AND ASSIGN UPDATE AND DOWNLOADED STATUS
                # ASSIGN INITIAL KEY VALUE PAIR TO TOOL, THEN PROCEDE TO CHECK IF VALUE NEEDS
                # TO BE ADJUSTED IF TOOL HAS AVAILABLE UPDATE AND IF IT
                onlineTool['updateAvailable'] = False
                onlineTool['hasBeenDownloaded'] = False

                if onlineTool['toolType'] not in localContainers:
                    # the local container is not even in the local database
                    # so there can't be a sibling
                    markedToolList.append(onlineTool)
                    continue
                try:
                    # FOUND A LOCAL SIBLING, LET'S CHECK IF IT'S UP-TO-DATE
                    localSibling = [t for t in self.localToolProxyList if t.id_ == onlineTool['id']][0]
                    logger.debug(u'online tool filetitle: {0}'.format(onlineTool['filetitle']))
                    onlineModDate = onlineTool['submitdate']
                    localModDate = localSibling.modDate
                    logger.debug(u'online tool file title: {0}'.format(onlineTool['filetitle']))
                    logger.debug('online tool submitdate: {0}'.format(onlineModDate))
                    logger.debug(u'local sibling file title: {0}'.format(localSibling.title))
                    logger.debug('local sibling submitdate: {0}'.format(localModDate))

                    if onlineModDate > localModDate:
                        logger.info('%s has an available update' % localSibling.title)
                        updateAvailable = True
                    else:
                        updateAvailable = False

                    onlineTool['hasBeenDownloaded'] = True
                    onlineTool['updateAvailable'] = updateAvailable
                    localSibling.updateAvailable = updateAvailable # not sure if this is required in any way

                except IndexError:
                    # CONTAINER EXISTS IN LOCAL DATABASE BUT NO LOCAL SIBLING FOUND
                    onlineTool['updateAvailable'] = False

                finally:
                    # BUILD THE TOOL LIST WITH MARKED TOOLS
                    markedToolList.append(onlineTool)

            # THROW ERROR IF WE DON'T END UP WITH THE RIGHT AMOUNT OF TOOLS IN THE NEW LIST
            if not len(self.toolDataOnline[onlineContainer]) == len(markedToolList):
                raise ValueError("Losing tools while tagging - please report this to admin@nukepedia.com")
            else:
                # ASSIGN NEW LIST TO DATA
                self.toolDataOnline[onlineContainer] = markedToolList

    def __openInstallDir(self):
        '''
        Open system file browser at install location for selected tool.
        The action that triggers this is only active for single selections, so we can just grab the first
        index of the selection
        '''

        tool = self.ui.settingsDialog.toolsTab.tableView.getSelectedTools()[0]
        openedLocations = []
        for p in tool.filePaths:
            # convert relative to absolute path
            p = os.path.join(self.settings.repoLocation, p)
            if os.path.isdir(p):
                if p not in openedLocations:
                    common.openSystemFileBrowser(p)
                    openedLocations.append(p)
            else:
                pp = os.path.dirname(p)
                if pp not in openedLocations:
                    common.openSystemFileBrowser(pp)
                    openedLocations.append(p)

    def __openDownloadDir(self):
        '''
        Open system file browser at download location for selected tool.
        The action that triggers this is only active for single selections, so we can just grab the first
        index of the selection
        '''

        tool = self.ui.settingsDialog.toolsTab.tableView.getSelectedTools()[0]
        absPath = os.path.join(self.settings.repoLocation, tool.downloadPath)
        common.openSystemFileBrowser(os.path.dirname(absPath))

    def __removeTools(self):
        '''Removes tool entirely, including installed files, downloaded files and database entry'''

        import shutil
        selectedTools = self.ui.settingsDialog.toolsTab.tableView.getSelectedTools()

        localPathNested = [t.filePaths for t in selectedTools]
        localPaths = [item for sublist in localPathNested for item in sublist]
        downloadPaths = [os.path.join(self.settings.repoLocation, os.path.dirname(t.downloadPath)) for t in selectedTools]

        pathString = '\n'.join(localPaths) +'\n' + '\n'.join(downloadPaths)
        msgBox = QtWidgets.QMessageBox()
        ret = msgBox.warning(self,
                              'Removing Tools',
                              'This will remove the selected tools from the local database and delete the following files:<br><br><font size = 2>{}</font>'.format(pathString),
                              QtWidgets.QMessageBox.Ok,
                              QtWidgets.QMessageBox.Cancel)
        if ret == QtWidgets.QMessageBox.Cancel:
            # user cancelled dialog - nothing to do
            return

        for p in localPaths + downloadPaths:
            # delete directory from install and download location
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)

        for toolProxyItem in selectedTools:
            if self.npdbLocal.removeTool(toolProxyItem):
                # tool has no more versions installed, to reset the progress bar
                self.model.getToolById(toolProxyItem.id_).hasBeenDownloaded = False

        # remove progressbar decorators
        try:
            self.toolView.updateDownloadStatus()
        except AttributeError:
            # tool page has not been pulled down
            pass

        # update local database which also updates the view
        self.__refreshLocalToolData()

    def __resetLoginFields(self):
        '''Empty login fields on both the page and the menu'''

        self.ui.loginPage.username.setText('')
        self.ui.loginPage.password.setText('')
        self.ui.loginPage.delBtn.setVisible(False)
        #self.ui.optionsMenu.loginWidget.username.setText('')
        #self.ui.optionsMenu.loginWidget.password.setText('')

    def __refreshLocalToolData(self):
        '''Reload the local tool data'''
        self.modelLocal.itemChanged.disconnect(self.__updateLocalToolItem)
        self.getLocalToolData()        

    def __saveFavorite(self, toolID, favorite):
        '''Saves new favorite in the online database'''

        logger.debug('Saving favorite list to online account')
        logger.debug('Contents: {}'.format(favorite.tools))

        def __manageFavID(response):
            if response == '':
                # existing favorite list was updated
                newID = favorite.id_
            else:
                # new favorite list was created
                newID = int(response)           
            if not toolID:
                # Assign the returned ID for a newly created favorite object
                favorite.id_ = newID
            self.__updateFavMenu()

        # prepare database tasks
        #taskQueue = common.DBTaskQueue(self.loginController.npdb, mode='setFavorite', parent=self)
        self.dbTaskQueue.setTask('setFavorite')
        self.dbTaskQueue.worker.setFav(favorite)
        self.dbTaskQueue.worker.setFavResponse.connect(__manageFavID)
        self.dbTaskQueue.start()
          
    def __setOnlineToolData(self, toolData):
        if not toolData:
            # request was cancelled
            return
        self.toolDataOnline = toolData
        # now that we have the online tools we can check for available updates
        # for tools that have already been installed
        # and mark tools that already exist in the local database
        # assign "updateAvailable" attribute to local tools and assign respective value
        # assign "hasBeenDownloaded" attribute to local tools and assign respective value
        self.__decorateToolButtons()
        # Fill model with online data after tools are marked for updates
        self.model.setTools(self.toolDataOnline)
        self.createContainerButtons()
    
    def __setFavoriteData(self, favDataList):
        '''Set users favourites for current session'''

        for favData in favDataList:
            #print favData
            # Update the fav dictionary to use proxy items derived from the sparse data base string
            favData['items'] = [self.__getProxyFromFileData(fileData) for fileData in favData['items']]
            f = NkpdFavorite(favData)
            self.favorites.append(f)

        self.__updateFavMenu()

    def __setLogLevel(self):
        '''
        Check environment for NKPD_LOG_LEVEL and set the logger accordingly.
        If the env variable does not exist activate the user setting and use that (default)
        '''
        if common.FILE_LOG_LEVEL:
            # log level has been set via the environment variable, so use that and disable user setting
            logger.setLevel(common.FILE_LOG_LEVEL)
            self.ui.settingsDialog.optionsTab.logWidget.setDisabled(True)
            self.settings.setFileLogLevel(common.FILE_LOG_LEVEL)
        else:
            # no valid env variable found, so let the user settings toggle the setting
            self.ui.settingsDialog.optionsTab.logWidget.setDisabled(False)
            if self.ui.settingsDialog.optionsTab.logWidget.isChecked():
                logger.setLevel(logging.DEBUG)
            else:
                logger.setLevel(logging.ERROR)

    def __setLogLevelSlot(self, value):
        '''Slot to set logging interactively'''
        if value:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.ERROR)        
        
    def __setVersion(self):
        versionText = 'v' + str(__version__) + ' - PySide{}'.format(common.pyside_version)
        #if os.path.splitext(__file__)[-1] in ('.py', '.pyc'):
        if os.path.splitext(inspect.getfile(NPDB))[-1] in ('.py', '.pyc'):
            versionText += 'DEV'
        self.ui.versionLabel.setText(versionText)

    def __updateFavMenu(self, *containerName):
        '''
        Update favorite lists for drop stack and tool buttons.
        ContainerName is only used to connect to an existing signal.
        '''
        self.ui.favStackMenuLoad.clear()
        self.ui.favStackMenuSave.clear()
        self.ui.favToolMenu.clear()
        
        if not self.favorites:
            # no favorites available - add dummy action
            self.ui.dropStack.btnLoad.setDisabled(True)
            favToolAction = QtWidgets.QAction(ICON_CACHE.getIcon('favorites'), 'no favorites available', self.ui.favToolMenu)
            #favToolAction.setDisabled(True)
            self.ui.favToolMenu.addAction(favToolAction)
            return

        self.ui.dropStack.btnLoad.setEnabled(True)

        # Create action to load all tools with updates
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # need to test this for plugins in various scenarios
        # (e.g. when update does not offer the platform anymore that is currently installed)
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        ## DEACTIVATED FEATURE AS IT GETS TOO TRICKY WITH NON-CROSS PLATFORM TOOLS
        #favStackActionLoadUpdates = LoadFavAction(ICON_CACHE.getIcon("favorites") , 'updates', self.ui.favStackMenuLoad)    

        # Add list of installed tools that have updates online
        #toolsWithUpdate = [tool for tool in self.model.getTools() if tool.updateAvailable]
        #favStackActionLoadUpdates.setToolList(toolsWithUpdate)
        
        ## Disable the action if no updates are available - DEACTIVATED FEATURE AS IT GETS TOO TRICKY WITH NON-CROSS PLATFORM TOOLS
        #if not toolsWithUpdate:
            #favStackActionLoadUpdates.setEnabled(False)
            
        # Add action to the drop stack menu
        #self.ui.favStackMenuLoad.addAction(favStackActionLoadUpdates)  - DEACTIVATED FEATURE AS IT GETS TOO TRICKY WITH NON-CROSS PLATFORM TOOLS
        self.ui.favStackMenuLoad.addSeparator()

        for fav in self.favorites:
            # Assign action for favorite menus in drop stack and in tool buttons
            #favStackActionLoad = QtWidgets.QAction(ICON_CACHE.getIcon("favorites") , fav.name, self.ui.favStackMenuLoad) # BUGGY, NEED CUSTOM ACTION AS WORKAROUND:
            favStackActionLoad = LoadFavAction(ICON_CACHE.getIcon("favorites") , fav.name, self.ui.favStackMenuLoad)
            
            # Skip favorite list called "downloaded" for saving actions
            # as it's generated automatically and should not be modified
            if fav.name != 'downloaded':
                favStackActionSave = QtWidgets.QAction(ICON_CACHE.getIcon("favorites") , fav.name, self.ui.favStackMenuSave)
                favStackActionSave.setData(fav) # Send data to saveStackAsFavorite() to overwrite existing favorite list
                favToolAction = QtWidgets.QAction(fav.name, self.ui.favToolMenu)
                self.ui.favStackMenuSave.addAction(favStackActionSave)
                self.ui.favToolMenu.addAction(favToolAction)

            logger.debug(u'preparing favorite list "{}"...'.format(fav.name))
            favStackActionLoad.setToolList(fav.toolProxies)

            # Add action to menu
            self.ui.favStackMenuLoad.addAction(favStackActionLoad)


        # CONNECT SIGNALS WITH SLOTS
        # stack menu load
        for action in self.ui.favStackMenuLoad.actions():
            if not action.isSeparator():
                action.favoriteListLoaded.connect(self.ui.dropStack.loadFavorites)

        # ADD AND CONNECT "IMPORT FROM FILE" OPTION AT BOTTOM OF LIST (AFTER ALL OTHER ACTIONS HAVE BEEN CONNECTED)
        favStackActionImport = QtWidgets.QAction(ICON_CACHE.getIcon("favorites") , 'Import from file...', self.ui.favStackMenuLoad)
        self.ui.favStackMenuLoad.addSeparator()
        self.ui.favStackMenuLoad.addAction(favStackActionImport)
        favStackActionImport.triggered.connect(self.slotImportStackFromFile)

        # stack menu save
        for action in self.ui.favStackMenuSave.actions():
            action.triggered.connect(self.saveStackAsFavorite)

        # tool menu
        for action in self.ui.favToolMenu.actions():
            action.setCheckable(True)
            action.toggled.connect(self.slotManageFavorites)

    def __updateTools(self):
        '''
        Downloads and installs the current version of the selected tools
        to do:
        install tools
        update models/views
        '''
        selectedTools = self.ui.settingsDialog.toolsTab.tableView.getSelectedTools()
        logger.error('updating tools - - NOT YET IMPLEMENTED')
                      
    def __updateToolView(self):
        try:
            self.toolView.updateDownloadStatus()
        except AttributeError:
            # tool view has not yet been pulled down
            pass

    def adjustUI(self):

        # Update the UI after tool data has been downloaded
        self.ui.htmlViewHeader.installBtn.setEnabled(self.isPro)

        # Check nuBridge version and show alert if necessary
        try:
            curVer = LooseVersion(__version__)
            availVer = LooseVersion(NPDB.getLatestVersion())
            if curVer < availVer:
                self.ui.welcomePage.showUpdateAlert(curVer.vstring, availVer.vstring)
        except:
            logger.exception('!! VERSION CHECK FAILED !!')

        if not self.isPro:
            # If logged in as guest disconnect some actions that require a pro account
            self.ui.dropStack.dropStackArea.stackHasContent.disconnect(self.ui.dropStack.btnSave.setEnabled)
            self.ui.dropStack.dropStackArea.stackHasContent.disconnect(self.ui.dropStack.btnInstall.setEnabled)

        else:
            # This is to ensure a login via the menu activates all features that are disabled for guests
            self.ui.dropStack.dropStackArea.stackHasContent.connect(self.ui.dropStack.btnSave.setEnabled)
            self.ui.dropStack.dropStackArea.stackHasContent.connect(self.ui.dropStack.btnInstall.setEnabled)

        # Disable/enable some widgets according to user status
        self.ui.dropStack.btnLoad.setEnabled(self.isPro)
        self.ui.dropStack.btnSave.setEnabled(self.isPro and len(self.ui.dropStack.dropStackArea.addedWidgets) > 0)

        self.ui.statusBar().showMessage('logged in as %s' % self.userInfo['name'])
        
        # Get tool and download count
        allTools = [item for sublist in self.toolDataOnline.values() for item in sublist]
        self.ui.welcomePage.setToolCount(len(allTools))
        totalDownloads = 0
        for t in allTools:
            totalDownloads += int(t['downloads'])        
        self.ui.welcomePage.setDownloadCount(totalDownloads)

        #if self.firstLogin:
        self.ui.showWelcomePage(self.userInfo)
        self.ui.loginPage.resetPage()

    def closeEvent(self, event):
        self.aboutToClose.emit()
        super(ToolBrowser, self).closeEvent(event)

    def containerChangeRequest(self):
        '''The user wants to change the visible page'''

        if not self.containers.keys(): # MAKE SURE THE LOGO IS ONLY FADED OUT WITH THE FIRST CONTAINER CHANGE
            self.ui.showMainApp()
        #self.ui.showMainApp() # this causes redundant fade animation in the background

        button = self.sender()
            
        # GET REQUESTED CONTAINER PAGE AND SEND IT TO ANIMATOR
        containerName = button.cName
        try:
            # re-use existing tool view
            self.toolView = self.containers[button]
            proxyModel = self.toolView.model

        except KeyError:
            # create new tool view for container and save it for re-use
            self.toolView = WidgetPage(self.settings, self.ui.pageAnimator)
            self.toolView.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.containers[button] = self.toolView
            slots = FancyButtonSlotHolder(self.slotInstall, self.slotInstallShowFileHistory,
                                          self.slotAddToStack, self.slotAddToStackShowFileHistory,
                                          self.slotShowDetail,
                                          self.slotVisitToolWebsite)
            self.toolView.setSlots(slots)
            
            # create proxy model for requested container
            proxyModel = self.getModel()
            if containerName == 'all':
                proxyModel.setFilterContainer('')
            else:
                proxyModel.setFilterContainer(containerName)
            self.toolView.setModel(proxyModel)
            proxyModel.layoutChanged.connect(self.toolView.build)

            # CONNECT SIGNALS WITH SLOTS
            self.ui.searchBox.textChanged.connect(proxyModel.searchFor)

        # set scroll direction based on settings
        self.toolView.setLayoutDirectionByIndex(self.settings.scrollBarDirection)
        self.ui.settingsDialog.optionsTab.scrollBarDirectionWidget.currentIndexChanged.connect(self.toolView.setLayoutDirectionByIndex)
        
        # show the widget
        self.ui.pageAnimator.showWidget(self.toolView)
        
        # UPDATE FILTER WIDGET
        # TEMPORARILY BLOCK FILTER CALLBACK TO NOT GENERATE CONTENT TWICE
        self.ui.filterWidget.blockSignals(True)
        self.ui.filterWidget.clear()
        toolCats = [c for c in proxyModel.getCategories()]
        filterList = sorted(toolCats)
        
        # DON'T SHOW "all" AS FILTER OPTION IF CONTAINER ONLY HAS ONE CATEGORY
        # ALSO DISABLE THE FILTER WIDGET IN THIS CASE
        #if len(filterList) > 1:
            #filterList.insert(0, 'all')
            #self.ui.filterWidget.setDisabled(False)
        #else:
            #self.ui.filterWidget.setDisabled(True)

        self.ui.filterWidget.setDisabled(False)
        filterList.insert(0, 'available updates')
        filterList.insert(0, 'installed')
        filterList.insert(0, 'all')
        self.ui.filterWidget.addItems(filterList)
        self.ui.filterWidget.insertSeparator(3)

        # RE-ACTIVATE CALLBACKS
        self.ui.filterWidget.blockSignals(False)

        # ENABLE SEARCH AND SORT WIDGETS
        for w in (self.ui.sortWidget, self.ui.searchBox, self.ui.sortOrderBtn):
            w.setEnabled(True)
        # SET FILTER TO "ALL"
        self.slotFilter(0)
        # APPLY TEXT SEARCH
        self.slotSearch(self.ui.searchBox.text())
        # SORT TOOLS
        self.slotSort()
        #self.toolView.setFocus()
        self.toolView.scrollBar.setFocus()

    def connectSignalsWithSlots(self):
        '''Connect all signals of the GUI's widgets with the corresponding slots.'''

        self.settings.timeOutChanged.connect(self.npdbInstance.setTimeout)

        self.loginController.signalProcessingLogin.connect(self.statusUpdate)
        self.loginController.signalLoginSuccessful.connect(self.initSession)
        self.loginController.signalLoginSuccessful.connect(self.slotUpdateUserName)
        self.loginController.signalLoginSuccessful.connect(self.ui.optionsMenu.close)
        
        self.ui.dropStack.btnSave.saveNewListSignal.connect(self.saveStackAsFavorite)
        self.ui.dropStack.btnSave.saveAsFileSignal.connect(self.slotExportStackAsFile)
        self.ui.dropStack.btnInstall.clicked.connect(self.slotInstall)
        self.ui.dropStack.dropStackArea.btnClicked.connect(self.slotShowDetail)
        self.ui.sortWidget.currentIndexChanged.connect(self.slotSort)
        self.ui.sortOrderBtn.toggled.connect(self.slotSort)
        self.ui.filterWidget.currentIndexChanged.connect(self.slotFilter)
        self.ui.searchBox.textChanged.connect(self.slotSearch)
        self.ui.htmlViewHeader.installBtn.pressed.connect(self.slotInstall)
        self.ui.htmlViewHeader.installBtn.altClicked.connect(self.slotInstallShowFileHistory)
        self.ui.htmlViewHeader.stackBtn.pressed.connect(self.slotAddToStack)
        self.ui.htmlViewHeader.stackBtn.altClicked.connect(self.slotAddToStackShowFileHistory)
        self.ui.htmlViewHeader.webBtn.clicked.connect(self.slotVisitToolWebsite)

        self.ui.optionsMenu.reportABug.triggered.connect(self.__reportABug)
        self.ui.optionsMenu.logoutAction.triggered.connect(self.__logOut)      
        #self.ui.optionsMenu.loginWidget.signalLogin.connect(self.__loginViaMenu)
        
        # connections for local tool table
        self.ui.settingsDialog.toolsTab.tableView.openInstallAction.triggered.connect(self.__openInstallDir)
        self.ui.settingsDialog.toolsTab.tableView.openDownloadAction.triggered.connect(self.__openDownloadDir)
        self.ui.settingsDialog.toolsTab.tableView.removeAction.triggered.connect(self.__removeTools)
        self.ui.settingsDialog.toolsTab.tableView.updateAction.triggered.connect(self.__updateTools)

        # connect settings UI to settings object to write settings ini and provide values for code
        #self.ui.settingsDialog.optionsTab.repoLocationPath.editingFinished.connect(self.__checkAndSetRepoFolder) # disable as it's too dangerous to change the repo via the UI
        self.ui.settingsDialog.optionsTab.scrollBarDirectionWidget.currentIndexChanged.connect(self.settings.setScrollBarDirection)
        self.ui.settingsDialog.optionsTab.showToolTipsWidget.stateChanged.connect(self.settings.setShowToolTips)
        if common.BAKE_GIZMOS is not None:
            self.ui.settingsDialog.optionsTab.bakeGizmosWidget.setDisabled(True)
        else:
            self.ui.settingsDialog.optionsTab.bakeGizmosWidget.currentIndexChanged.connect(self.settings.setBakeGizmos)

        if common.DOWNLOAD_ONLY:
            self.ui.settingsDialog.optionsTab.downloadOnlyWidget.setDisabled(True)
        else:
            self.ui.settingsDialog.optionsTab.downloadOnlyWidget.stateChanged.connect(self.settings.setDownloadOnly)       
        self.ui.settingsDialog.optionsTab.timeOutWidget.valueChanged.connect(self.settings.setTimeOutValue)
        self.ui.settingsDialog.optionsTab.maxThreadWidget.valueChanged.connect(self.settings.setMaxThreadCount)
        self.ui.settingsDialog.optionsTab.logWidget.stateChanged.connect(self.settings.setFileLogLevel)
        self.ui.settingsDialog.optionsTab.logWidget.stateChanged.connect(self.__setLogLevelSlot)

    def createContainerButtons(self):
        containers = sorted(self.model.containers, key=lambda i: i["name"])
        # SUMMARISE ALL UPDATES FOR "ALL" CONTAINER
        availableUpdates = sum([c['availableUpdates'] for c in containers])
        containers.append({'name':'all', 'availableUpdates':availableUpdates})
        # CREATE THE BUTTONS
        self.ui.setupContainerButtons(containers, self.containerChangeRequest)

    #def enterEvent(self, event):
        #QtWidgets.QApplication.instance().installEventFilter(self.eFilter)
        #super(ToolBrowser, self).enterEvent(event)
              
    def getLocalToolData(self):
        '''Retrieve data from local sqlite database'''

        logger.debug('*** GETTING LOCAL TOOL DATA...')
        # get local tool data
        self.npdbLocal = NPDBLocal(dbFile = os.path.join(self.settings.repoLocation, common.NKPD_DB_NAME))
        self.localToolProxyList = self.npdbLocal.getToolItems()
    
        # check for updates on already insttalled tools and assign "updateAvailable" key to all tools
        curMessage = self.ui.statusBar().currentMessage()
        self.ui.statusBar().showMessage('checking for tool updates...')
            
        self.ui.statusBar().showMessage(curMessage)
        # create and fill local tool model
        self.modelLocal.setTools(self.localToolProxyList)
    
        # connect signals for local tool model/table view
        self.modelLocal.itemChanged.connect(self.__updateLocalToolItem)

        # connect signals for when the user changes global bake settings
        self.settings.bakeGizmosChanged.connect(self.modelLocal.toggleBakeItems)

        if self.settings.bakeGizmos:
            # enable/disable the bakeGizmo items according to the current setting
            self.modelLocal.disableBakeGizmoItems()


    def updateLocalToolTable(self):
        self.modelLocal.itemChanged.disconnect(self.__updateLocalToolItem)
        self.getLocalToolData()

    def getDropstackItems(self):
        '''
        Return list of tool items that are currently in the drop stack.
        '''
        return [btn.tool for btn in self.ui.dropStack.dropStackArea.addedWidgets]
    
    def getModel(self):
        '''Create a proxy model instance and return it'''
        proxyModel = ToolProxyModel()
        proxyModel.setSourceModel(self.model)
        return proxyModel

    def initSession(self, userInfo):
        '''
        Download online data for logged in user and create containers.
        userInfo - dictionary with name and type info, e.g.:
                   {'name': u'Frank Rueter', 'type(s)': u'Public,ProUser'}
        '''
        self.favorites = []
        self.containers = {} # hold one WidgetPage per container button        
        self.userInfo = userInfo

        # Reset login fields
        self.__resetLoginFields()
        # If there are no container buttons this is the first login via the login page.
        # Otherwise the user is logging in from within an existing session via the settings menu.
        # NOTE: login via the settings menu is currenyl disabled as it doesn't seem to be of any real benefit
        self.firstLogin = False if self.ui.containerButtonGroup.buttons() else True

        if self.firstLogin:
            logger.debug('This is a log in from the LOGIN PAGE')
        else:
            logger.debug('This is a log after logging out')


        if 'type(s)' in self.userInfo and 'ProUser' in self.userInfo['type(s)']:
            # If we get here a pro user logged in
            logger.debug('This is a PRO USER login')
            self.isPro = True
        else:
            # a guest logged in
            logger.debug('This is a GUEST login')
            self.ui.statusBar().showMessage('logging in as guest')
            self.isPro = False

        # prepare database tasks
        #taskQueue = common.DBTaskQueue(self.loginController.npdb, mode='initAll', parent=self)
        self.dbTaskQueue.setTask('initAll')

        # connect progress signals
        self.loginController.signalLoginCancelled.connect(self.__cancelRequest)
        self.dbTaskQueue.worker.progressInfo.connect(self.ui.statusBar().showMessage)
        self.dbTaskQueue.npdbInstance.toolDownloadProgress.connect(self.ui.loginPage.busyBar.setValue)
        self.dbTaskQueue.npdbInstance.currentFileTitle.connect(self.ui.statusBar().showMessage)        

        # connect finished signals
        self.dbTaskQueue.worker.retrievedTools.connect(self.__setOnlineToolData)   # set online tool data for current session
        self.dbTaskQueue.worker.retrievedFavorites.connect(self.__setFavoriteData) # set favorites for current user
        self.dbTaskQueue.worker.retrievedNews.connect(self.ui.welcomePage.setNews) # check for news flash article        
        self.dbTaskQueue.worker.finished.connect(self.adjustUI)
        self.dbTaskQueue.start()

    #def leaveEvent(self, event):
        #QtWidgets.QApplication.instance().removeEventFilter(self.eFilter)
        #super(ToolBrowser, self).leaveEvent(event)

    def readSettings(self):
        '''Read settings and adjust widgets accordingly'''

        self.ui.settingsDialog.optionsTab.repoLocationPath.setText(self.settings.repoLocation)
        self.ui.settingsDialog.optionsTab.showToolTipsWidget.setChecked(self.settings.showToolTips)
        self.ui.settingsDialog.optionsTab.downloadOnlyWidget.setChecked(self.settings.downloadOnly)
        self.ui.settingsDialog.optionsTab.timeOutWidget.setValue(self.settings.timeOut)
        self.ui.settingsDialog.optionsTab.scrollBarDirectionWidget.setCurrentIndex(self.settings.scrollBarDirection)
        self.ui.settingsDialog.optionsTab.bakeGizmosWidget.setCurrentIndex(self.settings.bakeGizmos)
        self.ui.settingsDialog.optionsTab.maxThreadWidget.setValue(self.settings.maxThreadCount)
        self.ui.settingsDialog.optionsTab.logWidget.setChecked(self.settings.writeLogs)
        
    def saveStackAsFavorite(self):
        '''
        Save the current tools in the drop stack as a favorite with name and description from
        the dialog's result
        '''
        logger.debug('*** SAVING STACK AS FAVORITE')
        def saveStack(nkpdFavorite):
            self.slotManageFavorites(add=True, favorite=nkpdFavorite)

        toolItemList = self.getDropstackItems()
        try:
            # This only works if existing favorite list is being overwritten.
            favoriteToBeOverwritten =  self.sender().data()
            favoriteToBeOverwritten.tools = toolItemList
            saveStack(favoriteToBeOverwritten)

        except AttributeError:
            # We get here if a new list is being saved.
            dialog = SaveNewFavoriteDialog(toolItemList, self.favorites, parent=self.ui)
            dialog.savedFavorite.connect(saveStack)
            dialog.exec_()

    def setupUi(self):
        '''
        Initial filling of the UI with data from the model.
        '''
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.ui)
        self.setLayout(layout)

        sortOptions = list(self.sortDict.keys())
        self.ui.sortWidget.addItems(sortOptions)
        self.ui.sortWidget.setCurrentIndex(sortOptions.index('date'))

    def setupModels(self):
        '''Set up online model (live database) and local model (for installed tools) for application'''

        self.model = ToolModel()
        self.modelLocal = ToolModelLocal()
        self.ui.settingsDialog.toolsTab.tableView.setModelAndTweak(self.modelLocal)

    def slotAddToStack(self, latestVersion=True):
        '''Add tool(s) to the drop stack.'''

        #tool = self.sender().tool
        for tool in common.getToolItemProxies(self.sender().tool, latestVersion, parent=self.ui):
            logger.debug(u"Fancy button clicked, adding to stack: {0}".format(tool))
            if not self.ui.dropStack.dropStackArea.hasTool(tool):
                self.ui.dropStack.dropStackArea.addButton(tool)

    def slotAddToStackShowFileHistory(self):
        self.slotAddToStack(latestVersion=False)

    def slotExportStackAsFile(self, filePath):
        '''
        Save the drop stack to an xml file on disk
        filePath  -  path to xml file provided by DropStack FavoriteButtonSave.saveAsFileSignal
        '''
        from xml.etree import ElementTree as ET
        import time
        toolItems = self.getDropstackItems()
        logger.debug(u'Exporting list of {0} tools to {1}'.format(len(toolItems), filePath))
        
        root = ET.Element('NKPD')
        for toolItem in toolItems:
            if not toolItem.activeFile:
                # tool no longer exists in the Nukepedia database, so skip it
                logger.debug(u"Tool no longer exists: {}".format(toolItem.title))
                continue
            toolEle = ET.SubElement(root, 'Tool')
            logger.debug(u"Adding Tool to XML: {}".format(toolItem.title))
            # First write the tool item's data
            for k, v in iter(toolItem.toolData.items()):
                if k == 'files':
                    # ignore the "files" attr as it's irrelevant for this
                    continue
                attrEle = ET.SubElement(toolEle, str(k))
                if isinstance(v, time.struct_time):
                    attrEle.text = time.strftime('%Y-%m-%d %H:%M:%S', v)
                else:
                    logger.debug(u"\tAdding attr:: {}".format(v))
                    attrEle.text = uni_str(v)

            # Now write the active file's data
            activeFileEle = ET.SubElement(toolEle, 'activeFile')
            for k,v in iter(toolItem.activeFile.fileData.items()):
                if k == PLATFORM_KEY:
                    continue
                attrEle = ET.SubElement(activeFileEle, uni_str(k))
                attrEle.text = uni_str(v)

        tree = ET.ElementTree(root)
        tree.write(uni_str(filePath), encoding='utf-8', xml_declaration=True)

    def slotFilter(self, newIndex):
        if self.ui.pageAnimator.visibleWidget:
            categoryName = self.ui.filterWidget.currentText() if newIndex else None # return None if filter is "all"
            currentProxyModel = self.toolView.model
            currentProxyModel.setFilterCategory(categoryName)

    def slotImportStackFromFile(self):
        '''Import .nkpd file (xml format) and populate the stack with it's contents'''
        ret = QtWidgets.QFileDialog.getOpenFileName(None, 'Import Nukepedia Favorite File', os.path.expanduser('~'), 'Nukepedia Favorite Files (*.nkpd)')
        fileName = ret[0]
        if not fileName:
            return
        from xml.etree import ElementTree as ET
        self.ui.dropStack.dropStackArea.clearStack()
        tree = ET.parse(fileName)
        root = tree.getroot()
        for ele in root.iter('Tool'):
            toolData = {}
            for attr in ele:
                if attr.tag == 'activeFile':
                    # Collect file item data
                    fileEle = attr
                    fileData = {}
                    for attr in fileEle:
                        if attr.tag == 'platform':
                            # don't try to convert platform string as it will result in invalid integers
                            fileData[attr.tag] = attr.text
                        else:
                            obj = strToObj(attr.text)
                            logger.debug(u"{} is {}".format(attr.text, type(obj)))
                            fileData[attr.tag] = obj
                    # Create FileItem instance with collected data
                    activeFileItem = FileItem(fileData)
                else:
                    obj = strToObj(attr.text)
                    logger.debug(u"{} is {}".format(attr.text, type(obj)))
                    toolData[attr.tag] = obj

            # Create proxy item and assign active file item
            toolItemProxy = ToolItemProxy(ToolItem(toolData['category'], toolData))
            toolItemProxy.activeFile = activeFileItem
            # Add the item to the drop stack
            self.ui.dropStack.dropStackArea.addButton(toolItemProxy)


    def slotInstall(self, latestVersion=True):
        '''
        Install this tool.
        self.sender() may be:
             QtWidgets.QPushButton       - install from drop stack
             ToolPushButton    - install from detail page
             OperationButton   - install from fancy button
        '''

        installBtn = self.sender()
        if isinstance(installBtn, OperationButton):
            logger.debug(u"installing from fancy button (latestVersion:{})".format(latestVersion))
            requestedTools = common.getToolItemProxies(installBtn.tool, latestVersion, parent=self.ui)
            installObjects = {installBtn.parentWidget().parentWidget():requestedTools}
        elif isinstance(installBtn, ToolPushButton):
            logger.debug(u"installing from detail view")
            requestedTools = common.getToolItemProxies(installBtn.tool, latestVersion, parent=self.ui)
            installObjects = {installBtn.parentWidget():requestedTools}
        elif isinstance(installBtn, QtWidgets.QPushButton):
            logger.debug(u"installing from drop stack")
            # weed out missing files (files that were deleyed from the DB after being added to to a fav list)
            requestedTools = [t for t in self.ui.dropStack.dropStackArea.addedWidgets.values() if t.activeFile]
            # turn every tool item into a list of a single tool item to ensure consistency with the
            # install buttons for a single tool (which could be requesting a list of files to be installed)
            installObjects = {k:[v] for k,v in iter(self.ui.dropStack.dropStackArea.addedWidgets.items())}
        else:
            raise ValueError("Unknown sender for install slot")

        if not requestedTools:
            # file chooser dialog was cancelled
            return

        def __postLicenseAgreement():
            # if user agrees to license agreement, procede with download and installation
            self.installer = Installer(installObjects,
                                  self.settings,
                                  mainWidget=self)
            self.installer.signalInstallProgress.connect(self.ui.splashScreen.showMessage)
            self.installer.downloadFailed.connect(self.slotShowDownloadError)
            self.installer.downloadSuccessful.connect(self.slotUpdateContainerIcon)
            self.installer.downloadSuccessful.connect(self.__updateFavMenu)
            self.installer.installFailed.connect(self.slotShowInstallError)
            self.installer.installSuccessful.connect(self.slotShowCleanInstallInfo)
            self.installer.downloadQueueFinished.connect(self.updateLocalToolTable)
            self.installer.downloadQueueFinished.connect(self.__updateToolView)
            self.ui.splashScreen.updatePosition()
            self.ui.splashScreen.show()
            self.installer.install()

            ################################################################################################
            ## GET UPDATED LOCAL TOOL LIST AFTER INSTALL  - THE BELOW NEEDS TO BE RE-IMPLEMENTED WHEN THREADED DOWNLOAD IS DONE
            #self.modelLocal.itemChanged.disconnect(self.__updateLocalToolItem) # disconnect signal while installing tools
            #self.getLocalTooldata()                                 

            #self.ui.splashScreen.clearMessage()
            #self.ui.splashScreen.hide()

        # new
        def __showLicense(licenseText):
            laBox = LicenseAgreementBox(parent=self)
            laBox.setLicenseText(licenseText)
            self.ui.splashScreen.hide()
            laBox.accepted.connect(__postLicenseAgreement)
            laBox.open()

        # this crashes Nuke 13 eventually with recursion errors
        #self.ui.splashScreen.showMessage('retrieving license(s)')
        #self.ui.splashScreen.updatePosition()
        #self.ui.splashScreen.show()

        # prepare database tasks
        #taskQueue = common.DBTaskQueue(self.loginController.npdb, mode='getLicense', parent=self)
        self.dbTaskQueue.setTask('getLicense')
        self.dbTaskQueue.worker.setTools(*[dict(title=tool.title, id=tool.id_) for tool in requestedTools])
        self.dbTaskQueue.worker.retrievedLicense.connect(__showLicense)
        self.dbTaskQueue.worker.connectionError.connect(self.ui.splashScreen.hide)
        self.dbTaskQueue.worker.finished.connect(self.ui.splashScreen.hide)
        self.dbTaskQueue.start()

    def slotInstallShowFileHistory(self):
        self.slotInstall(latestVersion=False)

    def slotManageFavorites(self, add=True, favorite=None):
        '''
        Add or remove a tool to/from the favorites or save the whole stack to a favorite.
        If this is called from a tool button take favorite from sender's data.
        If this is called from the drop stack, favorite is passed as an argument
        '''
        # Copy the current list of favorites so we can check if
        # we are overwriting one of the favorites later
        oldFavList = list(self.favorites)

        sender = self.sender()
        if isinstance(sender, QtWidgets.QAction):
            # The function was called from a tool button or an overwriting menu item.
            sentData = sender.data()
            if isinstance(sentData, list):
                # The function was called from a tool button.
                # The tool is added ot removed from the favorite list.
                favorite, tool = sender.data()
                toolID = tool.id_
                
            elif isinstance(sentData, NkpdFavorite):
                # The function was called from the "overwrite" menu.
                # The drop stack is used to overwrite an existing favorite list.
                favorite = sentData
                toolID = None
        else:
            # The function was called from "Save new list" menu item.
            # The drop stack is being saved to a new favorite list.
            toolID = None

        if add:
            if toolID:
                # The function was called from a tool button.
                # Add the given tool to the respective nkpdFavorite object.
                warningTitle = '<b>Adding %s to %s.</b>' % (tool.title, favorite.name)
                proxyItems = common.getToolItemProxies(tool, latestVersionsOnly=True, parent=self.ui)
                for p in proxyItems:
                    favorite.addTool(p)
            else:
                # The function was called from the drop stack.
                # Save drop stack as favorite
                # We need to update self.favorites now unless an existing favorite was overwritten...
                warningTitle = '<b>Replacing %s.</b>' % favorite.name
                if favorite.name not in [f.name for f in self.favorites]:
                    self.favorites.append(favorite)
        else:
            # remove tool from respective nkpdFavorite object
            warningTitle = '<b>Removing %s to %s.</b>' % (tool.title, favorite.name)
            favorite.removeTool(tool)

        # save new favorite list online
        if favorite.name in [f.name for f in oldFavList]:
            warningInfo = 'Do you want to procede?'
            #msgBox = MessageBox(warningTitle, warningInfo, parent=self)
            ret = QtWidgets.QMessageBox.warning(self, warningTitle, '\n'.join([warningTitle, warningInfo]))
            if ret == QtWidgets.QMessageBox.Cancel:
                return
        self.__saveFavorite(toolID, favorite)

    
    def slotSearch(self, searchString):
        currentProxyModel = self.toolView.model
        currentProxyModel.searchFor(searchString)

    def slotShowDetail(self, tool=None):
        '''
        Show details for this tool. If triggered from the tool page, sender() is used,
        if triggered from the drop stack toolObject is used
        '''
        tool = tool or self.sender().tool
        self.ui.splashScreen.updatePosition()
        
        self.ui.splashScreen.show()
        self.ui.splashScreen.showMessage('Retrieving info for %s' % tool.title)        

        def __processDescRequest(html):
            self.ui.showDetailsPage(tool, html)

        #taskQueue = common.DBTaskQueue(self.loginController.npdb, mode='getDescription', parent=self)
        self.dbTaskQueue.setTask('getDescription')
        self.dbTaskQueue.worker.setTool(tool)
        self.dbTaskQueue.worker.retrievedDescription.connect(__processDescRequest)
        self.dbTaskQueue.worker.connectionError.connect(self.ui.splashScreen.hide)
        #self.dbTaskQueue.worker.finished.connect(self.ui.splashScreen.hide)
        self.dbTaskQueue.start()
        
    def slotShowDownloadError(self, errInfo):

        w = QtWidgets.QMessageBox()
        w.setText(errInfo[0])
        w.setInformativeText(errInfo[1])
        w.exec_()

    def slotShowInstallError(self, errInfo):
        '''
        Show an error message
        errInfo is a tuple with install dir, informative text and detailed text
        '''
        w = PostInstallDialog(errInfo[0])
        w.setText(errInfo[1])
        w.setDetails(errInfo[2])
        w.setWindowTitle('Manual Install Required')
        w.exec_()

    def slotShowCleanInstallInfo(self, info):
        '''
        Inform the user of download location
        info is a tuple with install dir and informative text
        '''

        w = PostInstallDialog(info[0])
        w.setText(info[1])
        w.setWindowTitle('Installation Successful')
        w.exec_()

    def slotSort(self, extraAttr=None):
        '''extraAttr catches return values from the signals that we don't actually need so far'''

        if self.ui.pageAnimator.visibleWidget:
            categoryName = self.sortDict[self.ui.sortWidget.currentText()]
            ascending = self.ui.sortOrderBtn.isChecked()
            currentProxyModel = self.toolView.model
            currentProxyModel.sortBy(categoryName, ascending=ascending)  

    def slotUpdateContainerIcon(self, containerName):
        '''decreaes available downloads count by one for the container button'''
        
        btnList = [btn for btn in self.ui.containerButtons if btn.cName in (containerName, 'all')]
        for btn in btnList:
            btn.decreaseAvailableUpdates()

    def slotUpdateUserName(self, userInfo):
        '''
        Set / Update user name on welcome page after successful login.
        Also update text in login option inside settings menu.
        userInfo is dictionary containing "name" key
        '''
        self.ui.welcomePage.setUserName(userInfo['name'])
        #if userInfo['name'] == 'guest':
            #self.ui.optionsMenu.loginWidget.group.setTitle('log in')
        #else:
            #self.ui.optionsMenu.loginWidget.group.setTitle('switch user')
       
    def statusUpdate(self, msg):
        self.ui.statusBar().showMessage(msg)
        self.ui.loginPage.legalTextWidget.setText(msg + '\nPlease hold while we get the online data.')

    def slotVisitToolWebsite(self):
        '''Configure the favorites menu for this tool, then show it'''
        tool = self.sender().tool
        self.ui.htmlViewHeader.goToToolWebsite(tool.id_)

nkpd_post_download_processes = []
npdb_custom_processor = None

def registerPostDownloadProcess(func):
    '''
    Registers func to be run after a successful download. This is for simple post process functions
    that don't need to communicate back to nuBridge (e.g. to copy the downloaded file into a backup area.
    To write a custom installer that works with nuBridge you must inherit from ProcessorBase and use Nukepedia.setProcessor(p)
    to register it.
    func - function that takes one argument which represents the downloaded tool item, e.g.:
           def MyPostDownloadOperation(tooItem):
               print dir(toolItem)
    '''
    global nkpd_post_download_processes
    nkpd_post_download_processes.append(func)

def setProcessor(proc):
    '''
    Sets proc to be used a processor after a file has been downloaded.
    Use this if you want to write your own installer to work with nuBridge
    proc  -  Processor class.
             proc must have a newPluginPath method to return the new plugin path to the nuBridge database
             as well as a newMenuInfo method to enable Nuke to load the newly installed tool
    '''
    global npdb_custom_processor
    npdb_custom_processor = proc

def main():
    # LAUNCH OUTSIDE OF NUKE
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("plastique")
    ex = ToolBrowser()
    ex.show()
    ex.raise_()
    sys.exit(app.exec_())


if __name__ == '__main__':
    #import sys
    #sys.stdout = None
    main()
