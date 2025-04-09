import sys
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets

class LicenseAgreementBox(QtWidgets.QDialog):
    '''Scroll box showing licenses'''
    def __init__(self, parent=None):
        super(LicenseAgreementBox, self).__init__(parent)
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setupUI()
        self.connectSignalsWithSlots()
        self.setMinimumSize(QtCore.QSize(600, 550))

    def setupUI(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.licenseField = QtWidgets.QTextEdit()
        self.licenseField.setReadOnly(True)
        buttonBox = QtWidgets.QDialogButtonBox()
        self.agreeBtn = QtWidgets.QPushButton('I have read and agree to the licenses shown above')
        self.cancelBtn = QtWidgets.QPushButton('Cancel')
        buttonBox.addButton(self.agreeBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        buttonBox.addButton(self.cancelBtn, QtWidgets.QDialogButtonBox.RejectRole)
 
        self.layout().addWidget(self.licenseField)
        self.layout().addWidget(buttonBox)

    def setLicenseText(self, text):
        self.licenseField.setText(text)

    def connectSignalsWithSlots(self):
        self.agreeBtn.clicked.connect(self.accept)
        self.cancelBtn.clicked.connect(self.reject)

    #def open(self):
        #'''This fixes the positioning on windows. OSX and linux behave without this hack'''
        #try:
            #self.move(self.parentWidget().x(), self.parentWidget().y())
        #except AttributeError:
            #pass
        #super(LicenseAgreementBox, self).open()
    

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = LicenseAgreementBox()
    w.setLicenseText('legal blurb - '*1000)
    print(w.exec_())
    sys.exit(app.exec_())

    