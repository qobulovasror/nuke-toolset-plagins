import sys
import time
import copy

#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui, IsPySide
from .Buttons import ToolPushButton
from .resources import ICON_CACHE


class FancyButtonSmall(QtWidgets.QWidget):
    clicked = QtCore.Signal()
    removed = QtCore.Signal()
    FIXEDSIZE = (90, 90)

    def __init__(self, toolProxy, icon=None, parent=None):
        '''toolProxy is a ToolItemProxy object representing a downloadable tool file'''
        super(FancyButtonSmall, self).__init__(parent)
        if IsPySide:
            # PySide2 will raise an error when calling the palette during Nuke launch
            paletteToolTipBase = QtWidgets.QApplication.instance().palette().color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.ToolTipBase)
            self.setStyleSheet('QToolTip{background:rgb(%s, %s, %s)}' % paletteToolTipBase.getRgb()[:3])
        else:
            pass
        self.setMouseTracking(True)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # Button and mouse state
        self.mainButtonDown = False # TO DRAW ICON STATE PROPERLY
        self.removeButtonDown = False # TO DRAW ICON STATE PROPERLY
        self.mouseOver = False # TO DISPLAY DELETE ICON

        # Button colours
        self.widgetColMainUp = QtGui.QColor(60, 60, 60, 0)
        self.widgetColMainDown = QtGui.QColor(60, 60, 60, 0)

        # Labels
        self.titleCol = QtGui.QColor(199, 89, 50)
        self.textCol = QtGui.QColor(150, 150, 150)

        # Font
        self.font = QtWidgets.QApplication.font()
        self.font.setPixelSize(10)

        # Assign some Tool attributes for painting
        self.tool = toolProxy
        self.title = self.tool.title or 'deleted id {}'.format(self.tool.id_)

        if self.tool.activeFile:
            # If the given tool proxy has an active file (which should be the case),
            # put some file info into the tooltip
            fileInfo = 'v{}'.format(self.tool.activeFile.version)
            if self.tool.toolType == 'plugins':
                fileInfo = '{} - {}'.format(fileInfo, self.tool.activeFile.targetPlatform)
            self.setToolTip(u'<b>{0} ({1})</b><br>{2}'.format(self.tool.activeFile.filename,
                                                             fileInfo,
                                                             self.__wrapText(self.tool.shortDesc)))            
        else:
            # If the given tool proxy does not have an active file, it means the
            # the tool ot file was deleted from the database (but still referenced in existing favorite lists).
            # Put info about this into the tooltip
            if not self.tool.files:
                # entire tool has been deleted
                self.setToolTip('The requested tool seems to have been deleted from the database.')
            else:
                # file has been deleted but tool still exists
                self.setToolTip('The requested file seems to have been deleted from the database.')

        self.icon = icon
        self.progress = 0 # for download progress bar (1.0 is 100%)

    def __wrapText(self, text, maxChar = 50):
        '''Wrap text to only contain maxChar per line'''
        i = 1
        charList = list(text)
        while i*maxChar < len(charList):
            charList.insert(i*maxChar, '\n')
            i += 1
        return ''.join(charList)

    def __drawIcon(self, painter, img, pos, size, btn='main'):
        '''Draw icon with status'''

        enabledStatus = QtGui.QIcon.Normal
        if btn == 'main' and self.mainButtonDown:
            enabledStatus = QtGui.QIcon.Disabled
        elif btn == 'remove' and self.removeButtonDown:
            enabledStatus = QtGui.QIcon.Disabled
        icon = QtGui.QIcon(img)
        pixmap = icon.pixmap(size, enabledStatus, QtGui.QIcon.On)
        painter.drawPixmap(pos, pixmap)

    def mousePressEvent(self, event):
        '''Main button down'''

        self.mainButtonDown = self.iconRect.contains(event.pos()) and not self.removeIconRect.contains(event.pos())
        self.removeButtonDown = self.removeIconRect.contains(event.pos())
        self.update()


    def mouseReleaseEvent(self, event):
        '''Emit clicked or removed signals'''

        if self.removeIconRect.contains(event.pos()):
            self.removed.emit()
        elif self.iconRect.contains(event.pos()):
            self.clicked.emit()

        self.mainButtonDown = False
        self.removeButtonDown = False
        self.update()

    def enterEvent(self, event):
        '''Show remove icon if cursor is on top of main icon'''
        #self.mouseOver = self.iconRect.contains(event.pos()) or self.removeIconRect.contains(event.pos())
        self.mouseOver = True
        self.update()

    def leaveEvent(self, event):
        '''Hide remove icon if cursor is not on top of main icon'''
        self.mouseOver = False
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Set up icon rectangles
        self.mainRect = QtCore.QRect(0, 0, self.geometry().width(), self.geometry().height())
        iconSize = QtCore.QSize(58,58) # Match this to actual image resolution
        iconPos = QtCore.QPoint((self.mainRect.width()-iconSize.width())/2, 10)
        self.iconRect = QtCore.QRect(iconPos, iconSize)
        removeIconSize = QtCore.QSize(16, 16)
        removeIconPos = QtCore.QPoint(iconSize.width()+iconPos.x()-10, iconPos.y()-5)
        self.removeIconRect = QtCore.QRect(removeIconPos, removeIconSize)

        # Assign colours
        if self.mainButtonDown:
            painter.fillRect(self.mainRect, self.widgetColMainDown)
        else:
            painter.fillRect(self.mainRect, self.widgetColMainUp)

        # Prepare area for text
        titleRect = copy.copy(self.mainRect)
        titleRect.setTop(self.iconRect.height()+10)
        titleRect.moveLeft(2)

        # Draw the diagonal gradient
        corner = QtGui.QPolygon()
        pt1 = self.mainRect.topLeft()
        pt2 = self.mainRect.bottomLeft()
        pt3 = self.mainRect.bottomRight()
        pt4 = self.mainRect.topRight()
        pt2.setY(pt2.y() * .9)
        pt3.setY(pt3.y() * .9)
        grad = QtGui.QLinearGradient(pt2, pt4)
        grad.setColorAt(0, QtGui.QColor(255,255,255,10))
        grad.setColorAt(1, QtGui.QColor(255,255,255,0))
        corner << pt1 << pt2 << pt3
        painterPath = QtGui.QPainterPath()
        painterPath.addPolygon(corner)
        painter.fillPath(painterPath, QtGui.QBrush(grad))

        # Draw the category icon
        self.__drawIcon(painter, self.icon, iconPos, iconSize)

        # Draw the "remove" icon
        if self.mouseOver:
            self.__drawIcon(painter, ICON_CACHE.getPixmap("remove"), removeIconPos, removeIconSize, 'remove')

        # Draw the tool title
        titleFont = QtGui.QFont(self.font)
        titleFont.setBold(True)
        painter.setPen(self.titleCol)
        painter.setFont(titleFont)
        painter.drawText(titleRect, QtCore.Qt.AlignTop, self.title)

        # Progress Bar
        pBarHeight = 3
        pBar = QtCore.QRect(pt1.x(), pt1.y(), pt4.x() * self.progress, pBarHeight)
        painter.setPen(QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(QtGui.QColor(208, 128, 34))
        painter.drawRect(pBar)

        # If the button is a placeholder for a missing tool, draw strike through and return
        # This may happen if files in favorites were deleted from the database
        if not self.tool.activeFile:
            painter.drawPixmap(self.iconRect.x(), self.iconRect.y(), ICON_CACHE.getPixmap('questionMark'))
            painter.end()
            return

        # If we get this far, the tool has an active file as expected, so draw some info about it
        # Draw version info
        painter.setFont(self.font)
        inset = 10
        versionRect = self.mainRect.adjusted(inset,0,0,0)
        painter.drawText(versionRect, QtCore.Qt.AlignLeft, 'v{}'.format(self.tool.activeFile.version))
    
        # Draw platform icon
        if self.tool.toolType == 'plugins':
            # We only care about the platform for plugins
            if not self.mouseOver:
                # Hide platform icons on mouse over to not interfere with remove icon
                pixmap = QtGui.QPixmap(ICON_CACHE.getPixmap(self.tool.activeFile.targetPlatform))
                platformPosX = self.mainRect.width()-pixmap.width()-inset
                platformPosY = self.mainRect.y()                
                painter.drawPixmap(platformPosX, platformPosY, ICON_CACHE.getPixmap(self.tool.activeFile.targetPlatform))

        painter.end()

    def minimumSizeHint(self):
        return QtCore.QSize(*self.FIXEDSIZE)

    def sizeHint(self):
        return QtCore.QSize(*self.FIXEDSIZE)

    def setIcon(self, icon):
        self.icon = QtGui.QIcon(icon)

    def setValue(self, value):
        # set the value for the download progress
        self.progress = (min(value, 100) / 100.0)
        self.update()

class OperationButton(ToolPushButton):
    """Button to be used in FancyButton"""

    def __init__(self, text, tool, parent=None):
        '''Set text, default colors and default state of the button'''

        super(OperationButton, self).__init__(text, parent)
        self.setMouseTracking(True)
        self.setFlat(True)
        self.tool = tool
        self.bgColor = QtGui.QColor()
        self.textColor = QtGui.QColor()
        self.underMouse = False

        # FONT
        self.font = QtWidgets.QApplication.font()
        self.font.setPixelSize(9)
        self.font.setBold(True)

    def leaveEvent(self, event):
        self.underMouse = False
        self.update()

    def enterEvent(self, event):
        self.underMouse = True
        self.update()

    def setColors(self, bgColor, textColor):
        '''Set colors for background and text of the button.'''

        self.bgColor = bgColor
        self.textColor = textColor

    #def setTool(self, tool):
        #'''use to ensure that sender().tool points to the right tool'''
        #self.tool = tool

    def paintEvent(self, event):
        '''Paint the button according to it's current state'''
        painter = QtGui.QPainter(self)
        painter.setRenderHint(painter.Antialiasing)

        if self.isDown():
            painter.setBrush(self.bgColor.darker())
            painter.setPen(self.textColor)

        elif self.underMouse:
            painter.setBrush(self.bgColor.lighter())
            painter.setPen(self.textColor.lighter())

        else:
            painter.setBrush(self.bgColor)
            painter.setPen(self.textColor)

        painter.drawRect(self.rect())
        painter.setFont(self.font)
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, self.text())

    def sizeHint(self):
        '''Calculate an accurate size for the button'''
        s = super(OperationButton, self).sizeHint()
        return QtCore.QSize(s.width() - 40, s.height()*.7)


class OperationButtonBox(QtWidgets.QWidget):
    """Button box for OperationButtons."""

    def __init__(self, parent=None):
        super(OperationButtonBox, self).__init__(parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.buttons = []
        self.buttonWidth = 0
        self.buttonHeight = 0

    def setupUi(self, installBtn, addToStackBtn, webBtn):
        '''Set up the design of the button box.'''

        self.buttons = [installBtn, addToStackBtn, webBtn]
        self.buttonWidth = max([b.sizeHint().width() for b in self.buttons])
        self.buttonHeight = max([b.sizeHint().height() for b in self.buttons])

        for b in self.buttons:
            b.resize(self.buttonWidth, self.buttonHeight)

        palette = self.parentWidget().palette()
        lightness = palette.color(QtGui.QPalette.ColorRole.Window).lightness()
        textColor = QtGui.QColor(150, 150, 150)
        
        baseGreen = QtGui.QColor(50, 70, 50)
        baseBlue = QtGui.QColor(60, 60, 70)
        baseRed = QtGui.QColor(75, 55, 50)

        baseGreen.setHsl(baseGreen.hslHue(), baseGreen.saturation(), lightness)
        baseBlue.setHsl(baseBlue.hslHue(), baseBlue.saturation(), lightness)
        baseRed.setHsl(baseRed.hslHue(), baseRed.saturation(), lightness)

        installBtn.setColors(baseGreen, textColor)
        addToStackBtn.setColors(baseBlue, textColor)
        webBtn.setColors(baseRed, textColor)

        #installBtn.setToolTip('<b>Install "%s"</b><br>The tool will be '\
            #'downloaded and installed in '\
            #'~/.nuke/Nukepedia.' % installBtn.tool.title)
        #addToStackBtn.setToolTip('<b>Add "%s" to the drop stack.</b><br>This '\
            #'enables the user to collect tools for bulk installing or to '\
            #'create favorite lists' % addToStackBtn.tool.title)
        #favBtn.setToolTip('<b>Add or remove "%s" to/from the current favorites.'\
            #'</b><br>To start a new favorite list '\
            #'use the drop stack' % favBtn.tool.title)

        self.layout.addWidget(installBtn)
        self.layout.addWidget(addToStackBtn)
        self.layout.addWidget(webBtn)

    def minimumSizeHint(self):
        '''Calculate the minimum size from margins, spacing and button sizes.'''

        m = self.layout.contentsMargins()
        s = self.layout.spacing()
        c = len(self.buttons)

        width = m.left() + m.right() + (c - 1) * s + c * self.buttonWidth
        height = m.top() + m.bottom() + self.buttonHeight
        return QtCore.QSize(width, height)

    def sizeHint(self):
        '''Calculate the size of the button box to fill the parent.'''

        if self.parent():
            width = max(self.minimumSizeHint().width(), self.parent().width())
        else:
            width = self.minimumSizeHint().width()

        return QtCore.QSize(width, self.minimumSizeHint().height())


class ToolDisplay(QtWidgets.QPushButton):
    """Widget to show information about a tool, draggable"""

    def __init__(self, tool, icon=None, parent=None):
        super(ToolDisplay, self).__init__(parent)
        self.tool = tool
        self.setInfo()
        self.icon = icon
        self.indicator = QtGui.QPixmap(ICON_CACHE.getPixmap('update', 'medium1'))
        self.spacing = 2

        self.dragSensitivity = 10
        self.startDragPos = None
        self.progress = 0 # for download progress bar (1.0 is 100%)

        # FONT
        font = QtWidgets.QApplication.font()
        self.fontTitle = font
        self.fontTitle.setPixelSize(12)
        self.fontTitle.setBold(True)

        self.fontSubTitle = QtWidgets.QApplication.font()
        self.fontSubTitle.setPixelSize(10)
        self.fontSubTitle.setBold(False)        

        self.__setupUi()

    def __setupUi(self):
        '''Design the display.'''

        self.setMinimumWidth(200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        palette = self.palette()
        baseColor = palette.color(QtGui.QPalette.ColorRole.Window)

        if baseColor.lightness() > 180:
            self.bgColorUp = palette.color(QtGui.QPalette.ColorRole.Window).darker(110)
            self.titleCol = QtGui.QColor(230, 45, 0)
            self.textCol = QtGui.QColor(80, 80, 80)            
        else:
            self.bgColorUp = palette.color(QtGui.QPalette.ColorRole.Window).lighter(120)
            self.titleCol = QtGui.QColor(199, 89, 50)
            self.textCol = QtGui.QColor(150, 150, 150)            
            
        self.bgColorDown = self.bgColorUp.darker()
        self.textColDown = self.textCol.darker()
        self.titleColDown = self.titleCol.darker()


    def setInfo(self):
        #self.title = '%s (%s)' % (self.tool.title, self.tool.container) # show container id for testing
        self.title = self.tool.title
        self.desc = 'Uploaded by %s on %s\ndownloads: %s' % (self.tool.author, time.strftime('%b %d %Y', self.tool.modDate), self.tool.downloads)
        self.subTitle = self.tool.category
        self.updateDownloadedStatus()

    def setTool(self, tool):
        self.tool = tool
        self.setInfo()
        self.update()

    def paintEvent(self, event):
        # Button is not down anymore, if it's a paintEvent after a finished drag and drop
        if self.startDragPos:
            p = self.mapFromGlobal(QtGui.QCursor.pos())
            point = p - self.startDragPos
            if point.manhattanLength() > self.dragSensitivity:
                self.setDown(False)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # CALCULATE CONTENT AREA
        rect = self.rect()
        rect.adjust(self.spacing, self.spacing, -self.spacing, -self.spacing)
        p = 10
        self.paddedRect = QtCore.QRect(rect.x() + p, rect.y() + p, rect.width() - p, rect.height() - p)

        # DRAW BACKGROUND
        bgColor = self.bgColorDown.lighter() if self.underMouse() else self.bgColorUp
        bgColor = self.bgColorDown if self.isDown() else bgColor
        painter.fillRect(rect, bgColor)

        # PREPARE AREAS FOR ICON AND TEXT
        size = 25
        iconSize = QtCore.QSize(size, size)
        titleRect = QtCore.QRect(self.paddedRect)
        titleRect.setLeft(2 * size)
        descRect = QtCore.QRect(self.paddedRect)
        descRect.setTop(2 * size)

        # DRAW ICON
        self.__drawIcon(painter, QtCore.QPoint(self.paddedRect.x(), self.paddedRect.y()), iconSize)
        # DRAW INDICATOR IF REQUIRED (I.E. FOR UPDATE ICON)
        if self.tool.updateAvailable:
            painter.drawPixmap(QtCore.QPoint(self.width() - self.indicator.width() - 2, 2), self.indicator)
        
        # DRAW TITLE
        titleCol = self.titleColDown.lighter() if self.underMouse() else self.titleCol
        titleCol = self.titleColDown if self.isDown() else titleCol
        painter.setPen(titleCol)
        painter.setFont(self.fontTitle)
        painter.drawText(titleRect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, self.title)
        
        # DRAW SUBTITLE
        textCol = self.textColDown.lighter() if self.underMouse() else self.textCol
        textCol = self.textColDown if self.isDown() else textCol
        painter.setPen(textCol)
        painter.setFont(self.fontSubTitle)
        painter.drawText(titleRect.x(), titleRect.y() + 25, self.subTitle)
        
        if not self.underMouse():
            # DRAW DESCRIPTION
            painter.drawText(descRect, self.desc)
            
        else:
            # DRAW ROLLOVER
            circlePath = QtGui.QPainterPath()
            gap = 15
            circleRect = QtCore.QRect(0, 0, 10, 10)
            circlePath.addEllipse(circleRect)
            circleRect.translate(gap, 0)
            circlePath.addEllipse(circleRect)
            circleRect.translate(gap, 0)
            circlePath.addEllipse(circleRect)
            circlePath.translate(rect.width() * .6, rect.height() * .35)
            painter.fillPath(circlePath, QtCore.Qt.darkGray)
            #self.setCursor(QtCore.Qt.PointingHandCursor)

        # DRAW PROGRESS BAR
        pBar = QtCore.QRect(rect.x(), rect.y(), rect.width() * self.progress, 3)
        painter.setPen(QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(QtGui.QColor(208, 128, 34))
        painter.drawRect(pBar)
        
    def __drawIcon(self, painter, pos, size):
        '''Draw icon with status'''
        enabledStatus = QtGui.QIcon.Disabled if self.isDown() else QtGui.QIcon.Normal
        pixmap = QtGui.QIcon(self.icon).pixmap(size, enabledStatus, QtGui.QIcon.On)
        painter.drawPixmap(pos, pixmap)

    def minimumSizeHint(self):
        return QtCore.QSize(150, 50)

    def setValue(self, value):
        # set the value for the download progress
        self.progress = (min(value, 100) / 100.0)
        self.update()

    def updateDownloadedStatus(self):
        '''
        Sets progress bar based on tool attr and is used to
        indicate if tools exists locally when button is used
        '''
        self.progress = int(self.tool.hasBeenDownloaded)

    def sizeHint(self):
        return QtCore.QSize(300, 80)

    def mousePressEvent(self, event):
        '''For dragging the widget: Store position of mousePressEvent.'''

        if event.button() == QtCore.Qt.LeftButton:
            self.startDragPos = event.pos()
        return super(ToolDisplay, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        '''
        For dragging the widget: Emit "clicked" only if the mouseReleaseEvent
        occurs very close to the mousePressEvent, otherwise start dragging.
        '''
        if event.buttons() != QtCore.Qt.LeftButton:
            return super(ToolDisplay, self).mouseMoveEvent(event)

        if self.startDragPos:
            self.setDown(False)
            point = event.pos() - self.startDragPos
            if point.manhattanLength() < self.dragSensitivity:
                
                return super(ToolDisplay, self).mouseMoveEvent(event)

        drag = QtGui.QDrag(self)
        try:
            pixmap = self.icon.pixmap(24,24)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
        except AttributeError:
            # no icon mostly for testing.
            # all buttons  hosuld have an icon eventuyally
            pass
        #drag.setHotSpot(event.pos() - self.rect().topLeft())
        drag.setMimeData(QtCore.QMimeData())
        drag.start(QtCore.Qt.CopyAction)
        return super(ToolDisplay, self).mouseMoveEvent(event)


class FancyButton(ToolDisplay):
    '''
    Custom widget to represent a NKPD tool.
    Allows installing, drag and drop, adding to stack and
    manipulating favorites'''

    def __init__(self, tool, slots, repoLocation, icon=None, parent=None):

        super(FancyButton, self).__init__(tool, icon, parent)
        self.repoLocation = repoLocation
        self.setupUi()
        self.setSlots(slots)
        self.setTool(tool)

    def setupUi(self):
        '''Set up the ui of the button box, it will be shown on mouseOver only'''

        self.setToolTip(self.__wrapText(self.tool.shortDesc))
        self.buttonBox = OperationButtonBox(self)

        self.installBtn = OperationButton('install', self.tool, self.buttonBox)
        self.addToStackBtn = OperationButton('add to stack', self.tool, self.buttonBox)
        self.webBtn = OperationButton('visit website', self.tool, self.buttonBox)

        self.buttonBox.setupUi(self.installBtn, self.addToStackBtn, self.webBtn)
        self.buttonBox.move(self.buttonBox.x(), self.sizeHint().height() - self.buttonBox.sizeHint().height())
        self.buttonBox.hide()
        
    def setTool(self, tool):
        '''point sender().tool to the correct tool object for all buttons'''

        super(FancyButton, self).setTool(tool)
        for btn in self.buttonBox.buttons:
            btn.setTool(tool)

        platformCompatibilityList = ','.join([f.targetPlatform for f in self.tool.getLatestVersions()])
        fileList = u','.join([f.filename for f in self.tool.getLatestVersions()])
        toolTipText = u'v{} available builds: {}<br>{}<br><br>{}'.format(self.tool.getLatestVersions()[0].version,
                                                                        platformCompatibilityList,
                                                                        fileList,
                                                                        self.tool.shortDesc)

        self.setToolTip(toolTipText)
        self.installBtn.setToolTip(u'<b>Install "{0}"</b><br>The tool will be '\
                              u'downloaded and installed in {1}<br>Hold alt to chose older versions'.format(tool.title, self.repoLocation))
        self.addToStackBtn.setToolTip(u'<b>Add "%s" to the drop stack.</b><br>This '\
                                 u'enables the user to collect tools for bulk installing or to '\
                                 u'create favorite lists' % tool.title)
        self.webBtn.setToolTip(u'<b>Add or remove "%s" to/from the current favorites.'\
                          u'</b><br>To start a new favorite list '\
                          u'use the drop stack' % tool.title)        


    def setSlots(self, slots):

        self.slots = slots
        self.installBtn.pressed.connect(self.slots.slotInstall)
        self.installBtn.altClicked.connect(self.slots.slotInstallShowFileHistory)
        self.addToStackBtn.pressed.connect(self.slots.slotAddToStack)
        self.addToStackBtn.altClicked.connect(self.slots.slotAddToStackShowFileHistory)
        self.webBtn.clicked.connect(self.slots.slotShowFavorites)
        self.clicked.connect(self.slots.slotShowDetail)

    def enterEvent(self, event):
        '''Show the button box on mouseOver.'''
        self.buttonBox.show()
        self.update()

    def leaveEvent(self, event):
        '''Hide the button box on mouseOver.'''
        self.buttonBox.hide()
        self.update()

    def setIcon(self, icon):
        self.icon = QtGui.QIcon(icon)

    def __wrapText(self, text, maxChar=50):
        '''wrap text to only contain maxChar per line'''
        i = 1
        charList = list(text)
        while i * maxChar < len(charList):
            charList.insert(i * maxChar, '\n')
            i += 1
        return ''.join(charList)



class FancyButtonSlotHolder(object):
    """Convenience class for holding all slots called by FancyButton signals."""

    def __init__(self, slotInstall, slotInstallShowFileHistory, slotAddToStack, slotAddToStackShowFileHistory, slotShowDetail, slotShowFavorites):
        self.slotInstall = slotInstall
        self.slotInstallShowFileHistory = slotInstallShowFileHistory
        self.slotAddToStack = slotAddToStack
        self.slotAddToStackShowFileHistory = slotAddToStackShowFileHistory
        self.slotShowDetail = slotShowDetail
        self.slotShowFavorites = slotShowFavorites


