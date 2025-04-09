import os
import sys
import logging
import common
import controller.common as common
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui, IsPySide

from .FancyButton import FancyButtonSmall
from .Dialogs import FileChoserWidget

from model.NKPD import ToolItem, ToolItemProxy
from view.resources import ICON_CACHE


logger = logging.getLogger('Nukepedia.DropStack')

class FavoriteButtonLoad(QtWidgets.QToolButton):
    '''Menu button to list favorites'''
    def __init__( self, parent=None ):
        super( FavoriteButtonLoad, self ).__init__( parent )
        self.setStyleSheet("QtWidgets.QToolButton { border: none }")
        self.setPopupMode( QtWidgets.QToolButton.InstantPopup )
        self.favIcon = QtGui.QIcon(ICON_CACHE.getIcon("favorites_load"))
        self.setIcon(self.favIcon)
        self.setIconSize(QtCore.QSize(30, 30))
        self.menu = QtWidgets.QMenu() # DUMMY - THE REAL MENU WILL BE ASSIGNED BY CONTROLLER CODE

    def updateMenu( self, menuItems ):
        '''
        Update favorites list.
        menuItems  -  list of favorite names
        '''
        self.menu.clear()
        for i in menuItems:
            favAction = QtWidgets.QAction( self.favIcon, i, self.menu )
            self.menu.addAction( favAction )


class FavoriteButtonSave(QtWidgets.QToolButton):
    '''Menu button to save favorites'''
    saveNewListSignal = QtCore.Signal()
    saveAsFileSignal = QtCore.Signal(str)

    def __init__( self, parent=None ):

        super( FavoriteButtonSave, self ).__init__( parent )
        self.setStyleSheet("QtWidgets.QToolButton { border: none }")
        self.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.favIcon = QtGui.QIcon(ICON_CACHE.getIcon("favorites_save"))
        self.setIcon( self.favIcon )
        self.setIconSize(QtCore.QSize(30, 30))
        self.menuTop = QtWidgets.QMenu()
        
        self.saveNewAction = QtWidgets.QAction('save list online...', self.menuTop)
        self.saveFileAction = QtWidgets.QAction('export list as file...', self.menuTop)
        self.menuTop.addAction(self.saveNewAction)
        self.menuTop.addAction(self.saveFileAction)
        self.saveNewAction.triggered.connect(self.saveNewListSignal.emit)
        self.saveFileAction.triggered.connect(self.launchFileBrowser)

        self.setMenu(self.menuTop)

    def setOverwriteMenu(self, menu):
        '''set overwrite menu to menu'''
        menu.setTitle('overwrite list')
        self.menuTop.insertMenu(self.saveNewAction, menu)

    def updateMenu(self, menuItems):
        '''
        Update favorites list.
        menuItems  -  list of favorite names
        '''
        self.menuOverwrite.clear()
        for i in menuItems:
            favAction = QtWidgets.QAction(self.favIcon, i, self.menuOverwrite)
            self.menuOverwrite.addAction(favAction)

    def launchFileBrowser(self):
        '''Launch file browser to sabe nkpdfav file and emit signal with file path if confirmed'''
        ret = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Nukepedia Favorite File', os.path.expanduser('~'), 'Nukepedia Favorite Files (*.nkpd)')
        fileName = ret[0]
        if fileName:
            # EMIT SIGNAL ONLY IF FILE NAME WAS SPECIFIED
            self.saveAsFileSignal.emit(fileName)

class DropStackArea(QtWidgets.QScrollArea):
    '''Stack of buttons dropped interactively or loaded from data online. Each button can only exist once in the DropStack'''
    btnClicked =  QtCore.Signal(ToolItem) # USE SIGNAL TO PASS ITEM DATA FOR RESPECTIVE BUTTON
    stackHasContent = QtCore.Signal(bool)

    def __init__(self, parent=None):
        '''item is a dictionary representing a downloadable tool'''
        super( DropStackArea, self ).__init__(parent)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.setLineWidth(3)
        self.setAcceptDrops(True)
        self.addedWidgets = {}

        palette = self.palette()
        baseColor = palette.color(QtGui.QPalette.ColorRole.Window)
        if baseColor.lightness() > 180:
            bgColour = palette.color(QtGui.QPalette.ColorRole.Window).darker(110)
        else:
            bgColour = palette.color(QtGui.QPalette.ColorRole.Window).lighter(110)
        
        ###################################################################################################
        ## THIS IS REQUIRED FOR THE PAINT EVENT TO KICK IN AFTER USING QtGui.QApplication.setStyle (BUG)
        logger.debug(u'**** IsPyside: %s', IsPySide)
        if IsPySide:
            # only activate this hack for PySde (PySide2 will raise an error).
            paletteToolTipBase = QtWidgets.QApplication.instance().palette().color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.ToolTipBase)
            toolTipStyle = 'QToolTip {background:rgb(%s, %s, %s)}' % paletteToolTipBase.getRgb()[:3]
            backgroundStyle = 'background:rgb(%s,%s,%s)' % bgColour.getRgb()[:3]
            self.setStyleSheet('''
            %s;
            %s;''' % (toolTipStyle, backgroundStyle))
        else:
            pass
        ###################################################################################################
            
        self.bgPixmap = ICON_CACHE.getPixmap('dropStackBG')

        # LAYOUT
        self.buttonArea = QtWidgets.QWidget() #TO MAKE SCROLLING WORK
        self.btnLayout = QtWidgets.QHBoxLayout()
        self.buttonArea.setLayout( self.btnLayout )
        self.btnLayout.setAlignment( QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft )
        self.btnLayout.SetMinAndMaxSize

        ## SCROLL AREA
        #self.setGeometry( 0, 0, 800, 400 )
        self.setMinimumHeight(120)
        
        ###################################
        ## THIS WORKS WITHOUT FLICKER WHEN TOOLS ARE ADDED TO SCROLL AREA, BUT IT
        ## PREVENTS paintEvent() FROM BEING TRIGGERED WHEN QtWidgets.QApplication.setStyle() is used (BUG)
        ## UNLESS self.setStyleSheet IS USED
        self.setWidgetResizable(True)
        ###################################
        
        self.setWidget(self.buttonArea)
        self.text = 'drop tools here'
        self.setToolTip('hold alt when dropping tools to chose older versions')
      

    def addButton(self, toolItem):
        '''Add a widget to the layout and emit signal with toolItems as argument'''

        logger.debug('button added for {0}'.format(toolItem))
        smallBtn = FancyButtonSmall(toolItem)
        smallBtn.setIcon(ICON_CACHE.getPixmap(toolItem.category, size='large'))
        self.btnLayout.addWidget(smallBtn)

        # PASS ON BUTTON'S SIGNAL TO EMIT IT'S DATA TO SHOW DETAILS PAGE IN PARENT WIDGET
        smallBtn.clicked.connect(lambda: self.btnClicked.emit(toolItem))
        smallBtn.removed.connect(lambda: self.removeWidget(smallBtn))

        # KEEP TRACK OF WIDGETS IN THE STACK
        self.addedWidgets[smallBtn] = toolItem
        self.repaint()
        self.stackHasContent.emit(bool([w for w in self.addedWidgets if w.tool.activeFile]))

        
    def dragEnterEvent(self, event):
        event.accept()

    def hasTool(self, tool):
        '''Test whether this tool is already on the stack'''
        return tool in [w.tool for w in self.addedWidgets]


    def dropEvent(self, event):
        '''get requested tool file and add it to drop stack'''       
                  
        droppedTool = event.source().tool
        # if alt key is pressed, all files are shown, not just the one(s) belonging to the latest version
        altKeyPressed = event.keyboardModifiers() == QtCore.Qt.AltModifier
        requestedTools = common.getToolItemProxies(droppedTool, latestVersionsOnly=not altKeyPressed, parent=self.parentWidget().mainUI)
        for tool in requestedTools:
            if not self.hasTool(tool):
                self.addButton(tool)
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()

    def clearStack(self, *args):
        """Clear the stack of buttons.
        args  -  testing against an error after copmile on windows. not actually used.
        """
        for w in list(self.addedWidgets.keys()):
            self.removeWidget( w )
        self.repaint()
        self.stackHasContent.emit(False)

    def removeWidget( self, widget ):
        self.btnLayout.removeWidget( widget )
        self.addedWidgets.pop(widget)
        #widget.setParent( None )
        widget.deleteLater()
        self.stackHasContent.emit(bool(self.addedWidgets))

    # UNFORTUNATELY THIS SEEMS TO MAKE THE SLIDING DOCKS GO JERKY
    def paintEvent( self, event ):
        painter = QtGui.QPainter()
        painter.begin( self.viewport() )
        if not self.addedWidgets:
            painter.drawPixmap(QtCore.QPoint(10,self.height()-self.bgPixmap.height()*2.5), self.bgPixmap)
        painter.end()


    #def minimumSizeHint(self):
        #return QtCore.QSize(50,10)


class DropStack(QtWidgets.QWidget):
    '''Drop Stack to hold selections and favorites'''
    def __init__( self, mainUI, parent=None ):
        super( DropStack, self ).__init__( parent )

        self.mainUI = mainUI
        self.setupUI()
        self.connectSignalsAndSlots()       
        
    def setupUI(self):

        # Layouts
        layout = QtWidgets.QGridLayout()
        btnLayout = QtWidgets.QVBoxLayout()

        # Stack
        self.dropStackArea = DropStackArea()

        ## BUTTONS
        # Load
        self.btnLoad = FavoriteButtonLoad()
        self.btnLoad.setToolTip('Load a favorite list into the drop stack')
        self.btnLoad.setFixedSize(30, 30)

        # Save
        self.btnSave = FavoriteButtonSave()
        self.btnSave.setToolTip('Save current contents of the drop stack as a favorite list')
        self.btnSave.setFixedSize(30, 30)
        self.btnSave.setEnabled(False)

        # Clear
        self.btnClear = QtWidgets.QToolButton()
        self.btnClear.setStyleSheet("QToolButton { border: none }")
        self.btnClear.setText( 'clear' )
        self.btnClear.setToolTip( 'Clear Stack' )
        self.btnClear.setFixedSize( 30, 30 )
        self.btnClear.setIcon( ICON_CACHE.getIcon("clearStack")  )
        self.btnClear.setIconSize( QtCore.QSize(30, 30) )
        self.btnClear.setEnabled(False)

        # Install
        self.btnInstall = QtWidgets.QPushButton( self )
        self.btnInstall.setText( 'Install' )
        self.btnInstall.setToolTip( 'Installs all the tools that are currently loaded in the drop stack' )
        self.btnInstall.setDisabled(True)
        
        # Add buttons
        for b in (self.btnLoad, self.btnSave, self.btnClear):
            btnLayout.addWidget(b)

        # Add to layout
        layout.addWidget(self.dropStackArea, 0, 1)
        layout.addWidget(self.btnInstall, 1, 1)
        layout.setColumnStretch(0,10)
        layout.setColumnStretch(1,50)
        layout.addLayout(btnLayout, 0, 0)
        self.setLayout(layout)

    def connectSignalsAndSlots(self):
        # make sure the connections to the stack buttons are unique so we don't connect them multiple times
        # when a user logs in through the menu after browsing as guest
        self.btnClear.clicked.connect(self.dropStackArea.clearStack, type=QtCore.Qt.UniqueConnection)
        self.dropStackArea.stackHasContent.connect(self.btnSave.setEnabled, type=QtCore.Qt.UniqueConnection)
        self.dropStackArea.stackHasContent.connect(self.btnClear.setEnabled, type=QtCore.Qt.UniqueConnection)
        self.dropStackArea.stackHasContent.connect(self.btnInstall.setEnabled, type=QtCore.Qt.UniqueConnection)


    def setFavMenuLoad(self, menu):
        '''set the menu for "load favorites"'''
        self.btnLoad.setMenu(menu)
        
    def setFavMenuSave(self, menu):
        '''set the menu for "overwrite list"'''
        self.btnSave.setOverwriteMenu(menu)

    def loadFavorites(self, toolList):
        '''
        Load favorites into drop stack.
        toolList  -  list of ToolItemProxies
        '''
        logger.debug('clearing stack')
        self.dropStackArea.clearStack()
        logger.debug('getting fav data via sending button')
        
        for toolData in toolList:
            logger.debug('\ttoolData:'.format(toolData))
            self.dropStackArea.addButton(toolData)

