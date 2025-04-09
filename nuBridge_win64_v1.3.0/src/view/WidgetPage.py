import sys
import common
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets
try:
    from .FancyButton import FancyButton
    from .PaginationWidget import PageScroller
    from .resources import ICON_CACHE
except:
    from FancyButton import FancyButton
    from PaginationWidget import PageScroller
    from resources import ICON_CACHE    
from compat import range

class ToolView(QtWidgets.QWidget):
    """Table view for FancyButtons of ten tools."""

    def __init__(self, maxWidgets, parent=None):
        super(ToolView, self).__init__(parent)
        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setAlignment(QtCore.Qt.AlignTop)
        self.maxWidgets = maxWidgets
        self.currentButtons = []

    def setTools(self, toolList, slots, repoLocation):
        '''Add list of ToolItems to the grid'''

        for index in range(self.maxWidgets):
            if index < len(toolList):
                tool = toolList[index]
                try:
                    btn = self.currentButtons[index]
                    # button already exists in this cell, so just change it's tool and icon
                    #print 'just changing existing button'
                    btn.setTool(tool)
                    if btn.isHidden():
                        btn.show()
                except IndexError:
                    # button doesn't exist yet in this cell, let's create one
                    #print 'creating new button'
                    btn = FancyButton(tool, slots, repoLocation)
                    self.grid.addWidget(btn, index/2, index%2)
                    self.currentButtons.append(btn)
                btn.setIcon(ICON_CACHE.getPixmap(tool.category, 'small'))
            else:
                # toolList was smaller than maxWidgets, so hide other buttons if they exist
                try:
                    #print 'hide existing button'
                    self.currentButtons[index].hide()
                except IndexError:
                    pass

    #def minimumSizeHint(self):
        #return QtCore.QSize(self.width(), 500)

class WidgetPage(QtWidgets.QWidget):
    '''
    Page to collect widgets in a grid and allows loading and saving of widget lists.
    Uses pagination to only show a certain amount of widgets.
    Used for itemsPage.
    '''
    def __init__(self, settings, parent=None):
        '''Stack of widgets laid out in a grid.'''
        super(WidgetPage, self).__init__(parent)
        self.settings = settings
        self.maxWidgets = 10
        self.slots = None
        self.model = None
        self.layoutDirection = QtWidgets.QBoxLayout.Direction.Down
        self.setupUi()
        
    def setLayoutDirection(self, direction):
        if direction == 'vertical':
            self.layoutDirection = QtWidgets.QBoxLayout.Direction.LeftToRight
            self.scrollBar.setOrientation(QtCore.Qt.Orientation.Vertical)
        else:
            self.layoutDirection = QtWidgets.QBoxLayout.Direction.Down
            self.scrollBar.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.biDirLayout.setDirection(self.layoutDirection)
    
    def setLayoutDirectionByIndex(self, index):
        if index:
            self.setLayoutDirection('vertical')
        else:
            self.setLayoutDirection('horizontal')

    def setupUi(self):
        '''Build the view consisting of a ToolView and a PageScroller.'''

        self.scrollBar = PageScroller(self)
        self.biDirLayout = QtWidgets.QBoxLayout(self.layoutDirection)
        self.setLayout(self.biDirLayout)
        self.toolView = ToolView(self.maxWidgets)
        self.biDirLayout.addWidget(self.toolView)

        #self.scrollBar.installEventFilter(self)
        self.scrollBar.signalPageChanged.connect(self.showPage)
        self.toolView.stackUnder(self.scrollBar) # make sure teh page indicator is drawn on top of the buttons
        self.biDirLayout.addWidget(self.scrollBar)

        # SET FOCUS FOR ARROW KEYS
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        # INSTALL SCROLL EVENT
        #self.installEventFilter(self.scrollBar)

    def showPage(self, index):
        '''Fill the grid with the tools of the current page.'''

        tools = self.model.getTools()
        start = index * self.maxWidgets
        end = min((index + 1) * self.maxWidgets, len(tools))
        self.toolView.setTools(tools[start: end], self.slots, self.settings.repoLocation)

    def setSlots(self, slots):
        '''Set the slots to be called by clicking on the OperationButtons'''
        self.slots = slots

    def setModel(self, toolProxyModel):
        '''Set the data model representing tools for this view.'''

        self.model = toolProxyModel
        self.build()

    def build(self):
        '''
        Initial build after model changed.
        Update the scroll bar.
        Show paginationWidget only if there is more than one page.
        '''

        tools = self.model.getTools()
        pageCount = len(tools) / self.maxWidgets + 1
        self.scrollBar.setPageCount(pageCount)

        if pageCount - 1:
            self.scrollBar.show()
            # THIS FIXES A BUG WHERE THE WIDGET IS TOO SMALL AFTER SCROLLING TO A PAGE
            # WITH LESS THAN THE MAX AMOUNT OF BUTTONS, CHANGING CONTAINERS, THEN SWITCHING BACK:
            self.setMinimumHeight(self.height())
        else:
            self.scrollBar.hide()

        self.showPage(0)

    def keyPressEvent(self, event):
        '''Allows changing the page using left and right arrow keys.'''

        if event.key() == QtCore.Qt.Key_Left:
            self.scrollBar.previousPage()

        elif event.key() == QtCore.Qt.Key_Right:
            self.scrollBar.nextPage()

        else:
            event.ignore()

    def showEvent(self, event):
        self.updateDownloadStatus()
        super(WidgetPage, self).showEvent(event)

    def updateDownloadStatus(self):
        '''Make sure the progress ar on all buttons is set according to their downloaded status'''
        for ch in self.toolView.children():
            try:
                ch.updateDownloadedStatus()
                ch.repaint()
            except AttributeError:
                # if ch is layout
                pass
    
    def wheelEvent(self, event):
        '''pass wheel event to scrollbar'''

        if event.delta() > 0:
            self.scrollBar.previousPage()
        else:
            self.scrollBar.nextPage()
        return True

def getTestWidgetPage():
    '''Need this as extra module so I can use it for testing PageAnimator'''
    from nkpd_tests.fancyButtonTest import TestSlots
    # WIDGETS
    mainWindow = QtWidgets.QWidget()
    widgetPage = WidgetPage(common.NKPDSettings())
    typeComboBox = QtWidgets.QComboBox()
    catComboBox = QtWidgets.QComboBox()
    sortComboBox = QtWidgets.QComboBox()
    searchField = QtWidgets.QLineEdit()
    typeComboBox.addItems(['gizmos', 'plugins', 'python', 'misc', 'toolsets', 'presets'])
    catComboBox.addItems(['transform', '3d', 'image', 'channel', 'filter', 'keyer'])
    sortComboBox.addItems(['author', 'title', 'downloads'])

    # LAYOUT
    changeLayoutBtn = QtWidgets.QPushButton('switch layout')
    changeLayoutBtn.clicked.connect(lambda: widgetPage.setLayoutDirectionByIndex(1))
    filterLayout = QtWidgets.QHBoxLayout()
    mainLayout = QtWidgets.QVBoxLayout()
    mainLayout.addLayout(filterLayout)
    mainWindow.setLayout(mainLayout)
    filterLayout.addWidget(typeComboBox)
    filterLayout.addWidget(catComboBox)
    filterLayout.addWidget(sortComboBox)
    filterLayout.addWidget(searchField)
    mainLayout.addWidget(changeLayoutBtn)
    mainLayout.addWidget(widgetPage)

    # MODEL
    proxyModel = getTestModel()
    widgetPage.setSlots(TestSlots().slots)
    widgetPage.setModel(proxyModel)

    # TEST SLOTS
    def typeSlot():
        print("filtering for type", typeComboBox.currentText())
        print("will be managed by container buttons")

    def categorySlot():
        #print 'filtering by category', catComboBox.currentText()
        widgetPage.model.setFilterCategory(catComboBox.currentText())

    def sortSlot():
        #print 'sorting by', sortComboBox.currentText()
        widgetPage.model.sortBy(sortComboBox.currentText(), True)

    def searchSlot():
        #print 'searching for', searchField.text()
        proxyModel.searchFor(searchField.text())

    # CONNECTIONS
    typeComboBox.currentIndexChanged.connect(typeSlot)
    catComboBox.currentIndexChanged.connect(categorySlot)
    sortComboBox.currentIndexChanged.connect(sortSlot)
    searchField.textChanged.connect(searchSlot)
    proxyModel.layoutChanged.connect(widgetPage.build)

    return mainWindow


def getTestToolView():
    from nkpd_tests.fancyButtonTest import TestSlots
    w = ToolView(10)
    w.setTools(getTestModel().getTools()[:10], TestSlots().slots)
    return w


def getTestModel():
    '''Return a ToolProxyModel to be displayed with a view'''

    import os
    projectRoot = os.path.sep.join(sys.path[0].split(os.path.sep)[:-1])
    sys.path.append(projectRoot)
    from model.NKPD import ToolModel, ToolProxyModel
    from model.NukepediaDB import NPDB
    npdb = NPDB()
    npdb.setMachineInfo(None)
    model = ToolModel()
    model.setTools(npdb.getTools())
    proxyModel = ToolProxyModel()
    proxyModel.setSourceModel(model)
    proxyModel.setFilterContainer('gizmos')
    return proxyModel


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = getTestWidgetPage()
    #w = getTestToolView()
    w.show()
    w.raise_()
    sys.exit(app.exec_())
