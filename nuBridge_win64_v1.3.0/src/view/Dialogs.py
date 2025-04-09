import os
import sys
import common
import webbrowser

#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui, QtCompat
from .LoginPage import PasswordWidget
from model.NKPD import NkpdFavorite, ToolUpdateItemDelegate, FileModel, FileProxyModel
from view.resources import ICON_CACHE

class PostInstallDialog(QtWidgets.QDialog):

    def __init__(self, path, parent=None):
        super(PostInstallDialog, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.path = path
        self.setupUI()

    def setupUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        self.label = QtWidgets.QLabel()
        self.infoText = QtWidgets.QLabel()
        self.infoText.setWordWrap(True)
        
        self.btnBox = QtWidgets.QDialogButtonBox()
        btnGotToDir = QtWidgets.QPushButton('Go To Install Directory')
        btnOk = QtWidgets.QPushButton('Ok')
        self.btnBox.addButton(btnGotToDir, QtWidgets.QDialogButtonBox.AcceptRole)
        self.btnBox.addButton(btnOk, QtWidgets.QDialogButtonBox.RejectRole)
        
        btnGotToDir.clicked.connect(self.__openInstallDir)
        btnOk.clicked.connect(self.close)
        
        layout.addWidget(self.label)
        layout.addWidget(self.infoText)
        layout.addWidget(self.btnBox)

    def setText(self, text):
        self.label.setText(text)

    def setDetails(self, text):
        self.infoText.setText(text)
    
    def __openInstallDir(self):

        common.openSystemFileBrowser(self.path)
        self.close()

class MessageBox(QtWidgets.QMessageBox):
    def __init__(self, text, infoText, parent=None):
        super(MessageBox, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)       
        self.setText(text)
        self.setInformativeText(infoText)
        self.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel)

class SettingsDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.tabWidget = QtWidgets.QTabWidget()

        self.btnBox = QtWidgets.QDialogButtonBox()
        btnClose = QtWidgets.QPushButton('Close')
        btnClose.clicked.connect(self.close)        

        self.layout().addWidget(self.tabWidget)
        self.layout().addWidget(btnClose)
        self.setupTabs()
        self.close()

    def setupTabs(self):
        self.networkTab = NetworkTab(self)
        self.optionsTab = OptionsTab(self)
        self.toolsTab = InstalledToolsTab()
        self.tabWidget.addTab(self.toolsTab, 'Installed Tools')
        self.tabWidget.addTab(self.optionsTab, 'Options')
        self.tabWidget.addTab(self.networkTab, 'Network')
    
    #def open(self):
        #'''This fixes the positioning on windows. OSX and linux behave without this hack'''
        #try:
            #self.move(self.parentWidget().x(), self.parentWidget().y())
        #except AttributeError:
            #pass
        #super(SettingsDialog, self).open()
    

class InstalledToolsView(QtWidgets.QTableView):
    signalDeleteTools = QtCore.Signal(list)

    def __init__(self, parent=None):
        super(InstalledToolsView, self).__init__(parent)
        #itemDelegate = ToolUpdateItemDelegate(self)
        #self.setItemDelegate(itemDelegate)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        #self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        #horizontalHeader = self.horizontalHeader()
        #horizontalHeader.setMinimumSectionSize(itemDelegate.pixmap.size().width())
        self.verticalHeader().hide()
        self.setupActions()

    def contextMenuEvent(self, event):
        super(InstalledToolsView, self).contextMenuEvent(event)
        self.mainMenu.exec_(self.mapToGlobal(event.pos()))

    def hideColumns(self):
        fieldsToHide = ['file id', 'tool id']
        for f in fieldsToHide:
            self.hideColumn(self.model().headerLabels.index(f))

    def setModelAndTweak(self, model):
        '''set model and do tweaks that require the data to be present'''
        self.setModel(model)
        self.resizeColumnsToContents()
        #self.horizontalHeader().setResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        QtCompat.setSectionResizeMode(self.horizontalHeader(), QtWidgets.QHeaderView.ResizeMode.Fixed)
        model.itemChanged.connect(self.resizeColumnsToContents)

    def setupActions(self):
        self.mainMenu = QtWidgets.QMenu(self)
        openMenu = QtWidgets.QMenu('open')
        self.mainMenu.addMenu(openMenu)

        self.openInstallAction = QtWidgets.QAction('open install location', self)
        self.openDownloadAction = QtWidgets.QAction('open download location', self)
        self.removeAction = QtWidgets.QAction('remove from database', self)
        self.updateAction = QtWidgets.QAction('update', self)
        
        openMenu.addAction(self.openDownloadAction)
        openMenu.addAction(self.openInstallAction)
        self.mainMenu.addAction(self.removeAction)
        self.mainMenu.addAction(self.updateAction)
        
        self.updateAction.setDisabled(True) # not yet implemented

    def getSelectedTools(self):
        '''return selected tool items'''

        toolItemColumn = 4 # where the toolItem object resides in the model
        indexList = self.selectionModel().selectedRows(toolItemColumn)
        return [self.model().itemFromIndex(toolIndex) for toolIndex in indexList]

    def selectionChanged(self, selected, deselected):
        '''check item when selected'''

        super(InstalledToolsView, self).selectionChanged(selected, deselected)
        self.openInstallAction.setEnabled((len(self.getSelectedTools()) == 1) and bool(self.getSelectedTools()[0].filePaths))
        self.openDownloadAction.setEnabled((len(self.getSelectedTools()) == 1) and bool(self.getSelectedTools()[0].downloadPath))

    def sizeHint(self):
        return QtCore.QSize(600,400)
    
    def showEvent(self, event):
        self.resizeColumnsToContents()
        self.hideColumns()
        super(InstalledToolsView, self).showEvent(event)

class InstalledToolsTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InstalledToolsTab, self).__init__(parent)

        # BUTTONS
        infoLabel = QtWidgets.QLabel('right click on selected rows for more options')

        # TABLE
        self.tableView = InstalledToolsView()

        # LAYOUT
        layout = QtWidgets.QVBoxLayout()
        topLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(topLayout)
        self.setLayout(layout)
        topLayout.addWidget(infoLabel)
        layout.addWidget(self.tableView)


class NetworkTab(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(NetworkTab, self).__init__(parent)
        self.setupUI()

    def setupUI(self):
        #self.tabWidget = QTableWidget()
        
        self.setLayout(QtWidgets.QVBoxLayout())
        #groupBox = QtWidgets.QGroupBox('Network Settings')
        #layout = QtWidgets.QHBoxLayout()
        infoText ='''To use a proxy connection please set the environment variable "HTTP_PROXY" with the correct credentials.<br><a style="color: #C74F24" href=\"http://www.nukepedia.com/nubridge-user-manual/#EnvVars\">Check the manual for details</a>'''
        infoLabel = QtWidgets.QLabel()
        infoLabel.setText(infoText)
        infoLabel.setOpenExternalLinks(True)
        
        self.layout().addWidget(infoLabel)
        #proxyLabel = QtWidgets.QLabel('HTTP Proxy (not yet implemented):')
        #portLabel = QtWidgets.QLabel('Port (not yet implemented):')
        #proxyWidget = QtWidgets.QLineEdit()
        #portWidget = QtWidgets.QSpinBox()

        #groupBox.setLayout(layout)
        #layout.addWidget(proxyLabel)
        #layout.addWidget(proxyWidget)
        #layout.addWidget(portLabel)
        #layout.addWidget(portWidget)

        #saveBtn = QtWidgets.QPushButton('Save')
        #self.layout().addWidget(groupBox)
        #self.layout().addWidget(saveBtn)

    def connectSignalsWithSlots(self):
        self.buttonBox.accepted.connect(self.save)

    def save(self):
        raise NotImplementedError

class OptionsTab(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(OptionsTab, self).__init__(parent)
        self.repoLocationPath = None
        self.setupUI()
        self.connectSignals()    

    def setupUI(self):
        formLayout = QtWidgets.QFormLayout()
        self.setLayout(formLayout)
        # default values for the following values are defined in SettingsDialog.readSettings()
        repoPathTTMessage = '''The location of the current repository. This is the location where files are downloaded to and where the default installer puts files for Nuke to pick up.<br>
        The environment variable NKPD_REPO_PATH can be used to override this setting.
        '''
        if common.REPO_PATH:
            repoPathTTMessage += '<br><br><b>NKPD_REPO_PATH is set to {}, so the file browser is disabled. Remove the environment variable to activate the browser</b>'.format(common.REPO_PATH)

        self.repoLocationPath = QtWidgets.QLineEdit()
        self.repoLocationPath.setEnabled(False)
        self.repoLocationBtn = QtWidgets.QPushButton('... (coming soon)')
        self.repoLocationBtn.setDisabled(True)
        self.repoLocationBtn.setToolTip(repoPathTTMessage)
        self.repoLocationPath.setToolTip(repoPathTTMessage)
        
        self.scrollBarDirectionWidget = QtWidgets.QComboBox()
        self.scrollBarDirectionWidget.addItem('horizontal', QtWidgets.QBoxLayout.Direction.Down)
        self.scrollBarDirectionWidget.addItem('vertical', QtWidgets.QBoxLayout.Direction.LeftToRight)
        self.showToolTipsWidget = QtWidgets.QCheckBox()

        self.bakeGizmosWidget = QtWidgets.QComboBox()
        self.bakeGizmosWidget.addItem('Per Tool')
        self.bakeGizmosWidget.addItem('Always')
        self.bakeGizmosWidget.addItem('Never')
        self.bakeGizmosWidget.setToolTip('Whether or not to bake gizmos into groups upon creation from the nuBridge menu. If set to "Per Tool" the individual settings in the "Installed Tools" tab are used')

        downloadOnlyTTMessage = 'If checked no installation attempt via processors (default or custom) will occur after downloading.<br>Any post download callbacks registered via "Nukepedia.registerPostDownloadProcess" will still be triggered.'
        if common.DOWNLOAD_ONLY:
            downloadOnlyTTMessage += '<br><br><b>NKPD_DOWNLOAD_ONLY is set, so this setting is deactivated. Remove the environment variable to activate this setting</b>'
        self.downloadOnlyWidget = QtWidgets.QCheckBox()
        self.downloadOnlyWidget.setToolTip(downloadOnlyTTMessage)
        self.timeOutWidget = QtWidgets.QSpinBox()
        self.timeOutWidget.setToolTip('Time in seconds to wait for server response.\nThis may have be increased when using a high thread count.')
        self.maxThreadWidget = QtWidgets.QSpinBox()
        self.maxThreadWidget.setToolTip('Maximum amount of download threads that are alowed to run at the same time\nwhen downloading via the drop stack.\nIf this is set too high the timeout value may have to be increased as well.')
        self.logWidget = QtWidgets.QCheckBox()
        logTTMessage = 'Activates file logging to {}.<br><br>This can also be set via the environment variable NKPD_LOG_LEVEL=debug.'.format(os.path.join(common.NKPD_SUPPORT_PATH, 'NKPD.log'))
        if common.FILE_LOG_LEVEL:
            logTTMessage += '<br><br><b>NKPD_LOG_LEVEL is set, so this setting is deactivated. Remove the environment variable to activate this setting</b>'
        self.logWidget.setToolTip(logTTMessage)
        
        repoLayout = QtWidgets.QHBoxLayout()
        repoLayout.addWidget(self.repoLocationPath)
        #repoLayout.addWidget(self.repoLocationBtn) # don't allow changing the repo via the settings, it's too dangerous
        formLayout.addRow('repo location', repoLayout)
        formLayout.addRow('scrollbar direction', self.scrollBarDirectionWidget)
        #formLayout.addRow('show tooltips', self.showToolTipsWidget) #disabled due to required event filter crashing Nuke 13
        formLayout.addRow('download only', self.downloadOnlyWidget)
        formLayout.addRow('bake gizmos', self.bakeGizmosWidget)
        formLayout.addRow('timeout (sec)', self.timeOutWidget)
        formLayout.addRow('maximum download threads', self.maxThreadWidget)
        formLayout.addRow('write logs', self.logWidget)

    def connectSignals(self):
        self.repoLocationBtn.clicked.connect(self.openFolderBrowser)
    
    def openFolderBrowser(self):
        self.previousPath = self.repoLocationPath.text()
        path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                "Choose folder for Nukepedia tool repo",
                                                self.repoLocationPath.text())
        if path:
            if self.repoLocationPath.text() != path:
                self.repoLocationPath.setText(path)
                self.repoLocationPath.editingFinished.emit()

    def resetRepoPath(self):
        '''set path to self.previousPath'''

        if self.previousPath:
            self.repoLocationPath.setText(self.previousPath)


class SaveNewFavoriteDialog(QtWidgets.QDialog):
    
    savedFavorite = QtCore.Signal(NkpdFavorite)
    def __init__(self, toolList, favorites=[], parent=None):
        super(SaveNewFavoriteDialog, self).__init__(parent)
        self.favorites = favorites
        self.tools = toolList
        self.setupUI()

    def setupUI(self):

        # WIDGETS
        groupSaveNew = QtWidgets.QGroupBox()
        self.nameField = QtWidgets.QLineEdit('name')
        self.descriptionField = QtWidgets.QLineEdit('description')
        saveBtn = QtWidgets.QPushButton('Save Favorite')
        cancelBtn = QtWidgets.QPushButton('Cancel')
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.addButton(saveBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(cancelBtn, QtWidgets.QDialogButtonBox.RejectRole)

        # LAYOUT
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        grpLayout = QtWidgets.QVBoxLayout()
        groupSaveNew.setLayout(grpLayout)
        grpLayout.addWidget(self.nameField)
        grpLayout.addWidget(self.descriptionField)
        layout.addWidget(groupSaveNew)
        layout.addWidget(self.buttonBox)

        self.connectSignalsAndSlots()

    def connectSignalsAndSlots(self):
        self.buttonBox.accepted.connect(self.save)
        self.buttonBox.rejected.connect(self.cancel)

    def save(self):
     
        # check if name is already in use:
        if self.nameField.text() in [f.name for f in self.favorites]:
            msg = QtWidgets.QMessageBox()
            msg.setText('The name "%s" is already used. Please chose a different one' % self.nameField.text())
            msg.exec_()
            self.nameField.selectAll()
            return
        # create new favorite
        favData = dict(name=self.nameField.text(),
                       description=self.descriptionField.text(),
                       items=self.tools,
                       id=0)
     
        newFavorite = NkpdFavorite(favData)
     
        self.savedFavorite.emit(newFavorite)
        self.accept()
    
    def cancel(self):
        self.reject()
    
    def setTextSelection(self, selected):
        if selected:
            self.nameField.selectAll()
        else:
            self.nameField.deselect()




class LoginWidget(QtWidgets.QWidget):
    signalLogin = QtCore.Signal()

    def __init__(self, parent=None):
        '''Mini widget to use as widget action in settings menu'''
        super(LoginWidget, self).__init__(parent)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.group = QtWidgets.QGroupBox()
        self.group.setTitle('log in')
        groupLayout = QtWidgets.QVBoxLayout()
        mainLayout = QtWidgets.QVBoxLayout()
        self.username = QtWidgets.QLineEdit()
        self.password = PasswordWidget()
        self.username.setPlaceholderText('user name')
        self.password.setPlaceholderText('password')
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode(2))
        self.btnSubmit = QtWidgets.QPushButton()
        self.btnSubmit.setIcon(ICON_CACHE.getIcon('login'))
        self.originalStyleSheet = self.username.styleSheet()
        for w in (self.username, self.password, self.btnSubmit):
            groupLayout.addWidget(w)

        self.group.setLayout(groupLayout)
        mainLayout.addWidget(self.group)
        self.setLayout(mainLayout)
        self.connectSignalsAndSlots()


    def showErrorState(self):
        '''turn widget into error state'''

        self.username.setStyleSheet('border: 1px solid darkorange;')
        self.password.setStyleSheet('border: 1px solid darkorange;')
        self.username.setText('')
        self.password.setText('')
        
    def showNormalState(self):
        '''return widget to normal state (from error state)'''
        self.username.setStyleSheet(self.originalStyleSheet)
        self.password.setStyleSheet(self.originalStyleSheet)

    def connectSignalsAndSlots(self):
        
        # MAKE RETURN BUTTON WORK INTUITIVELY
        self.username.returnPressed.connect(self.btnSubmit.click)
        self.password.returnPressed.connect(self.btnSubmit.click)
        
        # EMIT LOGIN SIGNAL
        self.btnSubmit.clicked.connect(self.signalLogin.emit)

class OptionsMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(OptionsMenu, self).__init__(parent)
        self.websiteAction = QtWidgets.QAction('Visit Website', self)
        self.userGuideAction = QtWidgets.QAction('User Guide', self)
        self.settingsAction = QtWidgets.QAction('Settings', self)
        self.aboutAction = QtWidgets.QAction('About', self)
        self.logoutAction = QtWidgets.QAction('Log Out', self)
        self.reportABug = QtWidgets.QAction('Report a Bug', self)
        self.websiteAction = QtWidgets.QAction('Visit Website', self)
        self.userGuideAction = QtWidgets.QAction('User Guide', self)
        self.settingsAction = QtWidgets.QAction('Settings', self)
        self.aboutAction = QtWidgets.QAction('About', self)
        self.logoutAction = QtWidgets.QAction('Log Out', self)
        #loginAction = QWidgetAction(self)       
        #self.loginWidget = LoginWidget()
        #self.loginWidget.setFocusProxy(self.loginWidget.username)
        #loginAction.setDefaultWidget(self.loginWidget)
        self.addAction(self.reportABug)
        self.addAction(self.websiteAction)
        self.addAction(self.userGuideAction)
        self.addAction(self.settingsAction)
        self.addAction(self.aboutAction)
        self.addSeparator()
        self.addAction(self.logoutAction)
        #self.addAction(loginAction)
        self.connectSignalsWithSlots()

    def __goToUserGuide(self):
        #QDesktopServices.openUrl('http://www.nukepedia.com/nubridge-user-manual')
        webbrowser.open('http://www.nukepedia.com/nubridge-user-manual')
        
    def __goToWebsite(self):
        #QDesktopServices.openUrl('http://www.nukepedia.com')
        webbrowser.open('http://www.nukepedia.com')

    def __showAbout(self):
        aboutBox = AboutBox()
        aboutBox.exec_()

    def focusNextPrevChild(self, next):
        return QtWidgets.QWidget.focusNextPrevChild(self, next)
    
    def connectSignalsWithSlots(self):
        # PREVENT ANY ACTIONS THAT MIGHT ACCIDENTALLY BE SELECTED TO BE ACTIVATED
        # WHEN LOGIN HAPPENS
        self.websiteAction.triggered.connect(self.__goToWebsite)
        self.userGuideAction.triggered.connect(self.__goToUserGuide)
        self.aboutAction.triggered.connect(self.__showAbout)
        #self.loginWidget.btnSubmit.clicked(self.setActiveAction(None))

class FileChoserDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(FileChoserDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        super(FileChoserDelegate, self).paint(painter, option, index)
        if index.column() == 0:
            rect = option.rect
            rect.setWidth(rect.height())
            rect.setSize(rect.size() * .5)
            rect.translate(rect.size().width() * 0.5,
                           rect.size().height() * 0.5)
            if (option.state & QtWidgets.QStyle.State_Selected):
                painter.drawPixmap(rect, ICON_CACHE.getPixmap('sortDescending'))

        else:
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
            
class FileChoserView(QtWidgets.QTableView):
    selectionExists = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(FileChoserView, self).__init__(parent)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        #self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        #self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.verticalHeader().hide()
        self.setItemDelegate(FileChoserDelegate())

    def setModelAndTweak(self, model):
        '''set model and do tweaks that require the data to be present'''
        self.setModel(model)
        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.sortByColumn(0, QtCore.Qt.DescendingOrder)
        #self.clicked.connect(self.selectByCheckBox)

    def selectionChanged(self, selected, deselected):
        '''check item when selected'''
        super(FileChoserView, self).selectionChanged(selected, deselected)
        self.selectionExists.emit(bool(len(self.selectionModel().selectedRows())))

    def getSelectedFiles(self):
        '''return selected file items'''
        indexList = self.selectionModel().selectedRows(1) # get index from column 1 as that is where teh ToolItem lives
        return [self.model().getItemByIndex(modelIndex) for modelIndex in indexList]

    def sizeHint(self):
        '''adjust widget width to fit content of FileChoserView'''

        vwidth = self.verticalHeader().width()
        hwidth = self.horizontalHeader().length()
        swidth = self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent)
        fwidth = self.frameWidth() * 2
        return QtCore.QSize(vwidth + hwidth + swidth + fwidth, self.height())
      

class FileChoserWidget(QtWidgets.QDialog):

    def __init__(self, toolItem, latestOnly=False, mainUI=None):
        super(FileChoserWidget, self).__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.mainUI = mainUI
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        model = FileModel(toolItem)
        proxyModel = FileProxyModel()
        proxyModel.setSourceModel(model)
        proxyModel.latestOnly = latestOnly

        self.fileView = FileChoserView()
        self.fileView.setModelAndTweak(proxyModel)

        self.btnBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.btnBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False) #enable via selection
        layout.addWidget(self.fileView)
        layout.addWidget(self.btnBox)
        self.connectSignalsAndSlots()

    def connectSignalsAndSlots(self):
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)
        self.fileView.selectionExists.connect(self.btnBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled)       
    
    def resizeEvent(self, event):
        '''Center the dialog on the mainUI when called via exec_'''
        parentScreenPos = self.mainUI.mapToGlobal(self.mainUI.geometry().topLeft())
        self.move(parentScreenPos.x() + (self.mainUI.geometry().width() * .5) - (self.geometry().width() * .5),
                  parentScreenPos.y())
        super(FileChoserWidget, self).resizeEvent(event)
    
class AboutBox(QtWidgets.QMessageBox):
    def __init__(self, parent=None):
        super(AboutBox, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)       
        self.setText('About')
        self.setIconPixmap(ICON_CACHE.getPixmap('NukepediaLogo_bridge'))
        text = 'nuBridge - A gateway to Nukepedia<br><br><br>\
        <b>written by:</b><br>Frank Rueter (frank@nukepedia.com)<br><br>\
        <b>server side programming by:</b><br>Paul McInnes<br><br>\
        <b>special thanks</b> to Aaron Richiger for all his mentoring<br><br>\
        <b>additional thanks for help with code and design to:</b><br>\
        Ivan Busquets, Jan Dubberke, Aaron Richiger, Tibold Kandrai, Sebastian Elsner, Johan Aberg<br>\
        '
        self.setInformativeText(text)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication([])
    w = OptionsTab()
    w.show()
    w.raise_()
    sys.exit(app.exec_())