import os
import sys
import common
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui

from .DetailsPage import HtmlView, HtmlViewHeader
from .Dialogs import LoginWidget, OptionsMenu
from .DropStack import DropStack
from .FaderWidget import PageFader
from .LoginPage import LoginPage
from .WelcomePage import WelcomePage
from .PageAnimator import VerticalAnimator
from .SearchWidget import SearchLineEdit
from .SlidingDockLayout import SlidingDocksWidget
from .Container import ContainerButton
from .SplashScreen import SplashScreen

from model.NukepediaDB import NPDB
from view.Dialogs import SettingsDialog
from view.resources import ICON_CACHE
from compat import range


class MainWindow(QtWidgets.QMainWindow):
    '''GUI of the main window'''
    signalLocal = QtCore.Signal(bool)
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.initUI()
        self.versionLabel = QtWidgets.QLabel()
        self.statusBar().addPermanentWidget(self.versionLabel)
        self.containerButtons = []
        #self.setTabOrder(self.loginPage.password, self.loginPage.username)

    def __createSearchBar(self):
        # CREATE SORT WIDGET
        sortLayout = QtWidgets.QHBoxLayout()
        self.sortWidget = QtWidgets.QComboBox()
        self.sortWidget.setEnabled(False)
        self.sortWidget.setToolTip('Sort the currently visible tools')
        self.sortOrderBtn = QtWidgets.QToolButton(self.topDockWidget)
        self.sortOrderBtn.setCheckable(True)
        self.sortOrderBtn.setToolTip('Sort order')
        sortIcon = QtGui.QIcon()
        sortIcon.addPixmap(ICON_CACHE.getPixmap("sortAscending"), state=QtGui.QIcon.On)
        sortIcon.addPixmap(ICON_CACHE.getPixmap("sortDescending"), state=QtGui.QIcon.Off)
        self.sortOrderBtn.setIcon(sortIcon)
        self.sortOrderBtn.setMinimumHeight(10)
        self.sortOrderBtn.setEnabled(False)
        #divider = QtGui.QIcon()
        #divider.setFrameShape(QtGui.QIcon.VLine)

        # CREATE FILTER COMBOBOX
        self.filterWidget = QtWidgets.QComboBox()
        self.filterWidget.setEnabled(False)
        self.filterWidget.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.filterWidget.setToolTip('Filter currently visible tools by tool type.')

        # CREATE SEARCH WIDGET
        self.searchBox = SearchLineEdit()
        self.searchBox.setEnabled(False)
        self.searchBox.setToolTip('Search currently visible tools for author or tool name')

        # ADD TO LAYOUT
        sortLayout.setSpacing(0)
        sortLayout.addWidget(QtWidgets.QLabel('sort by'))
        sortLayout.addSpacing(5)
        sortLayout.addWidget(self.sortWidget)
        sortLayout.addWidget(self.sortOrderBtn)
        self.searchLayout.addWidget(QtWidgets.QLabel('show'))
        self.searchLayout.addWidget(self.filterWidget)
        self.searchLayout.addLayout(sortLayout)
        self.searchLayout.addWidget(self.searchBox)
        self.searchLayout.addSpacing(50)

    def __initOptionsMenu(self):
        self.settingsButton.resize(44,24)
        self.settingsButton.setStyleSheet("QToolButton::menu-indicator { image: none }")
        self.optionsMenu = OptionsMenu(self)
        self.settingsButton.setMenu(self.optionsMenu)
        self.settingsButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.settingsDialog = SettingsDialog(self)
        self.optionsMenu.settingsAction.triggered.connect(self.settingsDialog.open)

    def backToToolsView(self):
        #print 'tool master page index:', self.toolPageMaster.currentIndex()
        self.toolPageMaster.showViewA()
        self.mainWidget.changeTopDock(0)

    def initUI(self):
        '''Build UI of the MainWindow'''
        # list of container buttons to hook up mousePressEvent
        self.loginPage = LoginPage()
        self.containerButtonGroup = QtWidgets.QButtonGroup()
        self.favStackMenuLoad = QtWidgets.QMenu(self)
        self.favStackMenuSave = QtWidgets.QMenu(self)       
        self.favToolMenu = QtWidgets.QMenu(self)    
    
        ###### CREATE MAIN LAYOUTS ###################################################################
        self.settingsButton = QtWidgets.QToolButton()
        self.settingsButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.settingsButton.setIcon(ICON_CACHE.getIcon('settings'))
        self.settingsButton.setToolTip('open settings dialog')
        self.settingsButton.setStyleSheet("QToolButton { border: none }")
       
        self.mainWidget = SlidingDocksWidget()
        self.setCentralWidget(self.mainWidget)

        # PREP MAIN AREA AND DOCKS
        self.topDockWidget = QtWidgets.QWidget(self.mainWidget)
        self.bottomDockWidget = QtWidgets.QWidget(self.mainWidget)
    
        # PAGE ANIMATOR FOR MAIN TOOL BROWSING (SLIDING PAGES)
        self.pageAnimator = VerticalAnimator(duration=700)
        #self.detailsPage = DetailsPage(self)
        self.htmlViewHeader = HtmlViewHeader(self)
    
        self.htmlView = HtmlView(self)
        self.toolPageMaster = PageFader(self.pageAnimator, self.htmlView, duration=400, parent=self.mainWidget)
        self.htmlViewHeader.backBtn.clicked.connect(self.backToToolsView) # fade from details view back to tool view
    
        # LAYOUTS IN DOCKS
        self.topDockLayout = QtWidgets.QVBoxLayout(self.topDockWidget)      # LAYOUT FOR TOP DOCK (FOR CONTAINER BUTTONS AND SEARCH BAR)
    
        self.bottomDockLayout = QtWidgets.QHBoxLayout(self.bottomDockWidget)   # LAYOUT FOR BOTTOM DOCK (FOR DROP STACK)
        self.containerLayout = QtWidgets.QHBoxLayout()    # LAYOUT FOR CONTAINER BUTTONS IN TOP DOCK
        self.searchLayout = QtWidgets.QHBoxLayout()       # LAYOUT FOR SEARCH AND FLITER BAR
        self.topDockLayout.addLayout(self.containerLayout)  # ADD CONTAINER LAYOUT TO DOCK
        self.topDockLayout.addLayout(self.searchLayout)     # ADD SEARCH LAYOUT TO DOCK
    
        self.placeHolderButton = ContainerButton({'name':'python', 'availableUpdates':0}, self.topDockWidget)  # Dummy button to calculate later size of layout without having set the containerbuttons
        self.containerLayout.addWidget(self.placeHolderButton)
    
        # ###### CREATE WIDGETS ###################################################################
        # CREATE SORT AND SEARCH AREA
        self.__createSearchBar()
        self.searchLayout.addWidget(self.settingsButton)   # ADD SETTINGS BUTTON TO LAYOUT
    
        # CREATE DROP STACK
        self.dropStack = DropStack(mainUI=self)
        self.dropStack.setFavMenuLoad(self.favStackMenuLoad)
        self.dropStack.setFavMenuSave(self.favStackMenuSave)
        self.bottomDockLayout.addWidget(self.dropStack)
    
        # TOP AND BOTTOM DOCKS
        self.topDockWidget.resize(self.topDockWidget.sizeHint())
        self.mainWidget.setTopWidgets(self.topDockWidget, self.htmlViewHeader)
        self.mainWidget.setBottom(self.bottomDockWidget)
    
        # BUILD SETTINGS MENU
        self.__initOptionsMenu()
   
        # SET LOGIN/INFO PAGE (CROSS FADING WIDGET) AS THE PAGE ANIMATOR'S START PAGE
        self.welcomePage = WelcomePage()
    
        self.loginPage.settingsButton.clicked.connect(self.settingsDialog.open)

        self.introPanel = PageFader(self.loginPage, self.welcomePage, parent=self.mainWidget)
        self.introPanel.setViewC(self.htmlView)
        self.mainWidget.setCenter(self.introPanel)

        self.splashScreen = SplashScreen(self)
        self.splashScreen.hide()
    
        self.setWindowTitle('Tool Browser')

    def setupContainerButtons(self, containers, callback):
        '''
        "containers" is a list of dictionaries with "name" and "updateAvailable" keys.
        "callback" is the slot that will be connected to their "clicked" action
        '''
        # reset container buttons first to avoid duplicates when users
        # log out and back in repeatedly
        for btn in self.containerButtons:
            btn.setParent(None)
        self.containerButtons = []

        self.containerLayout.removeWidget(self.placeHolderButton)
        self.placeHolderButton.close()
        fKeys = ['F%s' % (i+1) for i in range(12)]
        # DEFINE THE PREFERRED ORDER OF CONTAINERS HERE:
        customOrder = ['all', 'gizmos', 'python', 'plugins', 'toolsets', 'presets', 'misc', 'hiero', 'blink']
        sortedContainers = sorted(containers, key=lambda container: customOrder.index(container['name']))
        for index, container in enumerate(sortedContainers):
            containerButton = ContainerButton(container)
            toolTip = containerButton.toolTip()
            #containerButton.setToolTip('\n'.join([toolTip, 'Hotkey:', fKeys[index]]))
            containerButton.clicked.connect(callback)
            self.containerLayout.addWidget(containerButton)
            self.containerButtons.append(containerButton)
            self.containerButtonGroup.addButton(containerButton)

    def showLoginPage(self):
        '''Show the login page, hide docks'''
        self.mainWidget.hideDocks()
        self.toolPageMaster.hide()
        self.mainWidget.setCenter(self.introPanel)
        self.introPanel.show()
        self.introPanel.showViewA()
        self.loginPage.username.setFocus()
        self.settingsButton.hide()

    def showWelcomePage(self, userInfo):
        '''Show the main app, but with a welcome page instead of a table of tools.'''
        self.mainWidget.showDocks()
        self.toolPageMaster.hide()
        for button in self.containerButtonGroup.buttons():
            button.setChecked(False)

        if not self.introPanel.isVisible():
            self.mainWidget.setCenter(self.introPanel)
            self.introPanel.show()
        self.introPanel.showViewB()
        self.settingsButton.show()

    def showMainApp(self):
        '''
        Switches from the intro to the main app, docks remain visible.
        The introPanel is not used any more, change to the pageAnimator
        to show the tools.
        '''

        self.introPanel.setViewA(QtWidgets.QWidget()) # this avoids the login page to pop in when pulling down the first container pages
        self.introPanel.duration = 500
        self.introPanel.showViewA()
        self.toolPageMaster.show()
        self.mainWidget.setCenter(self.toolPageMaster)
        self.mainWidget.showDocks()
        # MAKE SURE THE INTRO PANEL IS HIDDEN SO IT DOESN'T STEAL MOUSE EVENTS:
        self.introPanel.faderWidget.timeLine.finished.connect(lambda: self.introPanel.setHidden(True))

    def showDetailsPage(self, tool, html):
        '''Fade from tool view to dettails view (online html description of a tool)'''
        self.htmlViewHeader.setTool(tool)
        self.mainWidget.changeTopDock(1)
        self.htmlView.loadFinished.connect(self.splashScreen.hide)
        self.htmlView.setHtml(html)
        self.htmlView.setTool(tool)
        if self.toolPageMaster.isVisible():
            self.toolPageMaster.showViewB() # needed for tool FancyButton
        else:
            self.introPanel.showViewC()     # needed for tool FancyButtonSmall before tool page is down
        self.htmlViewHeader.setFocus()

    def keyPressEvent(self, event):
        '''Define keyboard shortcuts'''
        fKeys = [eval('QtCore.Qt.Key_F%s' % (i+1)) for i in range(len(self.containerButtons))]
        if event.key() in (fKeys):
            pass # deactivating hotkeys for containers for now until they make more sense and don't conflict with Nuke
            ## fkeys for available container buttons
            #index = fKeys.index(event.key())
            #button = self.containerButtons[index]
            #button.clicked.emit()
            #for b in self.containerButtons:
                #b.setChecked(False)
            #button.setChecked(True)
        elif event.key() == QtCore.Qt.Key_Backspace:
            # shortcut for back button on detail page
            self.htmlViewHeader.backBtn.click()

    def moveEvent(self, e):
        '''Adjust the position of the splashscreen if the window is moved.'''
        
        if self.splashScreen.isVisible():
            self.splashScreen.updatePosition()

    def showEvent(self, event):
        '''Get rid of that unnecessary space around the widget when registering this widget as a nuke panel'''
        p = self
        while True:
            parentWidget = p.parentWidget()
            try:
                parentWidget.layout().setContentsMargins(0,0,0,0)
            except:
                break
            p = parentWidget
        super(MainWindow, self).showEvent(event)

    def sizeHint(self):
        return QtCore.QSize(640,820)

def main():
    import sys

    def slotContainerButton(ui):
        print("container button clicked")
        ui.showMainApp()

    def showWelcomePage(ui):
        #ui.setupContainerButtons(['misc', 'gizmos'], lambda: slotContainerButton(ui))
        ui.showWelcomePage({'name':'test dude'})

    def showSettings():
        print("showing settings")

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("plastique")
    w = QtWidgets.QWidget()
    ui = MainWindow()
    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(ui)
    w.setLayout(layout)    
    ui.settingsButton.clicked.connect(showSettings)
    #ui.loginPage.guestBtn.clicked.connect(lambda: showWelcomePage(ui))
    w.show()
    w.raise_()
    print(w.size())
    #ui.showLoginPage()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()