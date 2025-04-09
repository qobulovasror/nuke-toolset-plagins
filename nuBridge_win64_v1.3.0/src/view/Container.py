import sys
import common
from Qt import QtCore, QtWidgets, QtGui
from view.resources import ICON_CACHE

from .DetailsPage import *
from .FaderWidget import *



class ContainerButton(QtWidgets.QToolButton):
    '''
    Button for containers holds extra cName attribute to hold the container name to display underneath the icon
    as well as updateAvailable, which indicates if the container has a tool for which there is an update online.
    The icon is derived from cName and NKPD.getIconPath()
    '''
    def __init__(self, containerDict, parent=None):
        '''containerDict is a diciotnary with "name" and "updateAvailable" keys'''
        
        super(ContainerButton, self).__init__(parent)
        self.cName = containerDict['name']
        self.availableUpdates = containerDict['availableUpdates']
        
        try:
            self.setIcon(ICON_CACHE.getPixmap('container_%s' % self.cName))
            #self.setCustomIcon(False)
        except TypeError:
            # IF THIS HAPPENS SOMETHING IS WRONG (BUT SHOULDN'T STOP THE APP)
            print("missing container icon: 'container_%s'" % self.cName)
            
        style = self.style()
        self.setToolTip(self.cName)
        self.setText(self.cName)
        self.setIconSize(QtCore.QSize(50, 50))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setStyleSheet("QToolButton { border: none }")
        self.setCheckable(True)
        self.toggled.connect(self.setCustomIcon)

    def setCustomIcon(self, checked):
        '''switch between grey and coloured icon depending on whether button is checked'''
        if checked:
            pixmap = ICON_CACHE.getPixmap('container_%s_colour' % self.cName)
        else:
            pixmap = ICON_CACHE.getPixmap('container_%s' % self.cName)
        self.setIcon(pixmap)
    
    def decreaseAvailableUpdates(self):
        '''decrease the number for available updates by one unless it's already at zero'''
        if self.availableUpdates:
            self.availableUpdates -= 1
            self.update()
    
    def paintEvent(self, event):
        '''Draw update icon if required'''
        super(ContainerButton, self).paintEvent(event)
        if self.availableUpdates > 0:
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            rect = QtCore.QRect(0,0,20,20)
            rect.moveTopRight(QtCore.QPoint(self.width()-2, 0))
            painter.setBrush(QtGui.QColor(199, 89, 50))
            painter.setPen(QtCore.Qt.transparent)
            painter.drawEllipse(rect)
            painter.setPen(QtCore.Qt.white)
            painter.drawText(rect, QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter, str(self.availableUpdates))


if __name__ == '__main__':

    app = QtWidgets.QApplication( sys.argv )
    w = QtWidgets.QWidget()
    w.setLayout( QtWidgets.QHBoxLayout() )
    btn = ContainerButton({'name':'all', 'availableUpdates':1})
    palette = btn.palette()
    palette.setColor(btn.backgroundRole(), QtCore.Qt.darkGray)
    btn.setPalette(palette)
    w.layout().addWidget(btn)
    w.show()
    sys.exit( app.exec_() )


