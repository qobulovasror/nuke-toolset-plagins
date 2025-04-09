#from PySide import QtCore, QtGui
import common
from Qt import QtCore, QtWidgets
from .resources import ICON_CACHE


class SearchLineEdit(QtWidgets.QLineEdit):
    '''A search widget with icon and a "clear" button'''
    def __init__( self, parent = None ):
        QtWidgets.QLineEdit.__init__( self, parent )

        self.clearButton = QtWidgets.QToolButton(self)
        self.clearButton.setIcon(ICON_CACHE.getIcon("clear"))
        self.clearButton.setCursor( QtCore.Qt.ArrowCursor )
        self.clearButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clearButton.hide()
        self.clearButton.clicked.connect( self.clear)
        self.textChanged.connect(self.updateCloseButton)

        self.searchButton = QtWidgets.QToolButton(self)
        self.searchButton.setIcon(ICON_CACHE.getIcon("search"))
        self.searchButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")

        #frameWidth = self.style().pixelMetric( QtWidgets.QStyle.PM_DefaultFrameWidth )
        frameWidth = 1

        self.setStyleSheet("QLineEdit { padding-left: %spx; padding-right: %spx; } " % (self.searchButton.sizeHint().width() + frameWidth + 1, self.clearButton.sizeHint().width() + frameWidth + 1))
        msz = self.minimumSizeHint()
        self.setMinimumSize(max(msz.width(), self.searchButton.sizeHint().width() + self.clearButton.sizeHint().width() + frameWidth * 2 + 2), max(msz.height(), self.clearButton.sizeHint().height() + frameWidth * 2 + 2))


    def resizeEvent(self, event):
        sz = self.clearButton.sizeHint()
        #frameWidth = self.style().pixelMetric( QtWidgets.QStyle.PM_DefaultFrameWidth )
        frameWidth = 1
        self.clearButton.move(self.rect().right() - frameWidth - sz.width(), (self.rect().bottom() + 1 - sz.height()) / 2)
        self.searchButton.move(self.rect().left() + 1, (self.rect().bottom() + 1 - sz.height()) / 2)

    def updateCloseButton(self, text):
        if text:
            self.clearButton.setVisible(True)
        else:
            self.clearButton.setVisible(False)


def main():
    import sys
    app = QtWidgets.QApplication([])
    w = SearchLineEdit()
    w.show()
    sys.exit( app.exec_() )    

if __name__ == '__main__':
    main()
