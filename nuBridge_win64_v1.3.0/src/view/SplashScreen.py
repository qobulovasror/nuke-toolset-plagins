import sys
import common
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets, QtGui
from .resources import ICON_CACHE


class SplashScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SplashScreen, self).__init__(parent)
        self._pixmap = ICON_CACHE.getPixmap('NukepediaLogo_splash')
        self._message = ''
        self._alignment = QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom
        self.setupUi()

    def setupUi(self):
        self._color = QtGui.QColor(255, 255, 255, 255)
        self.setFixedSize(self._pixmap.size() * 2)
        self.updatePosition()

        # self.setMask(self._pixmap.mask())
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
        #                     QtCore.Qt.WindowStaysOnTopHint)

        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def clearMessage(self):
        self._message = ''
        self.repaint()

    def showMessage(self, message):
        self._message = str(message)
        self.repaint()

    def paintEvent(self, event):
        textbox = QtCore.QRect(self.rect())
        #textbox.setRect(textbox.x() + 5, textbox.y() + 5,
                        #textbox.width() - 10, textbox.height() - 10)
        painter = QtGui.QPainter(self)
        pixmapRect = self._pixmap.rect()
        pixmapRect.moveLeft((self.rect().width() - pixmapRect.width()) / 2.0 )
        painter.drawPixmap(pixmapRect, self._pixmap)
        metric = QtGui.QFontMetrics(QtWidgets.QApplication.font())
        textbox.moveBottom(pixmapRect.height())

        # draw text to get bounding rect after wrapping
        textboxReal = painter.drawText(textbox, self._alignment|QtCore.Qt.TextWordWrap, self._message)
        textboxReal.setHeight(metric.height() * 2)
        textboxReal.moveBottom(textbox.bottom())
        # draw BG rect
        painter.setBrush(QtGui.QBrush(QtGui.QColor(128,128,128)))
        painter.setPen(QtCore.Qt.transparent)
        painter.drawRect(textboxReal)
        # draw text again ontop of textbox
        painter.setPen(self._color)
        painter.drawText(textboxReal, self._alignment|QtCore.Qt.TextWordWrap, self._message)

    def updatePosition(self):
        '''Place the splash screen in the center of it's parent widget.'''
        c = self.parent().rect().center()
        self.move(QtCore.QPoint(c.x() - self._pixmap.width() , c.y() - self._pixmap.height()))

class TestBackgroundThread(QtCore.QThread):

    signalMadeProgress = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(TestBackgroundThread, self).__init__(parent)

    def run(self):
        progress = 0
        while progress < 10:
            progress += 1
            msg = 'Calculation made progress: %d' % progress
            self.signalMadeProgress.emit(msg + '++---+'*progress)
            QtCore.QThread.msleep(500)



