import sys
#from PySide import QtCore, QtGui
from Qt import QtCore, QtWidgets
from model.NukepediaDB import NPDB
from .resources import ICON_CACHE

    
class PasswordWidget(QtWidgets.QLineEdit):
    '''Store encrypted info for login here'''

    def __init__(self, parent=None):
        super(PasswordWidget, self).__init__(parent)
        self.setPlaceholderText('password')
        self.pwd = None
        self.machineInfo = None
        self.setEchoMode(QtWidgets.QLineEdit.EchoMode(QtWidgets.QLineEdit.Password))
        
class LoginPage(QtWidgets.QWidget):
    '''Simple Login Page'''

    def __init__(self, parent = None):
        super(LoginPage, self).__init__(parent)
        # CREATE WIDGETS
        layout = QtWidgets.QVBoxLayout()
        subLayout = QtWidgets.QHBoxLayout()
        busyBarLayout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(100,0,100,100)
        #layout.setAlignment(QtCore.Qt.AlignBottom)
        self.setLayout(layout)
        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setPixmap(ICON_CACHE.getPixmap('NukepediaLogo_bridge'))
        self.iconLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.settingsButton = QtWidgets.QPushButton('Settings')
        self.settingsButton.setToolTip('Show settings dialog and local tool table')
        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText('user name')
        self.password = PasswordWidget()
        self.useKeyring = QtWidgets.QCheckBox('remember password')
        self.delBtn = QtWidgets.QPushButton('forget')
        self.delBtn.setMaximumWidth(50)
        self.delBtn.setToolTip('Stop remembering the credentials for the current user name')
        self.delBtn.setVisible(False) # only show if there is a stored password for the given user
        self.submitBtn = QtWidgets.QPushButton('login')
        self.submitBtn.setAutoDefault(True)
        self.submitBtn.setDefault(True)
        self.submitBtn.setMaximumWidth(100)
        self.submitBtn.setLayoutDirection(QtCore.Qt.RightToLeft)

        self.busyBar = QtWidgets.QProgressBar()
        self.busyBar.setTextVisible(True)
        self.busyBar.setVisible(False)
        self.busyBar.setAlignment(QtCore.Qt.AlignLeft)
        self.cancelBtn = QtWidgets.QPushButton('Cancel')
        self.cancelBtn.setVisible(False)

        #self. = QtWidgets.QPushButton('login as guest')
        self.legalText = '''By logging in you accept Nukepedia's <a style="color: #C74F24" href="http://www.nukepedia.com/terms-of-use/">terms of use</a>'''
        self.legalTextWidget = QtWidgets.QLabel(self.legalText)
        self.legalTextWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.userGuideText = '''View <a style="color: #C74F24" href="http://www.nukepedia.com/nubridge-user-manual">user guide</a> online'''
        self.userGuideTextWidget = QtWidgets.QLabel(self.userGuideText)
        self.userGuideTextWidget.setOpenExternalLinks(True) # for soem reason the second QtWidgets.QLabel needs this to function
        self.userGuideTextWidget.setAlignment(QtCore.Qt.AlignCenter)

        self.errorMsg = QtWidgets.QLabel()
        #self.errorMsg.setVisible(False)
        self.errorMsg.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # LAYOUT
        layout.addWidget(self.iconLabel)
        layout.addSpacing(20)
        layout.addWidget(self.errorMsg)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        subLayout.addWidget(self.useKeyring)
        subLayout.addWidget(self.delBtn)
        subLayout.addStretch()
        subLayout.addWidget(self.submitBtn)
        layout.addLayout(subLayout)
        #layout.addWidget(self.submitBtn)
        #layout.addWidget(self.guestBtn)
        layout.addSpacing(20)
        layout.addWidget(self.legalTextWidget)
        layout.addSpacing(40)
        layout.addWidget(self.settingsButton)
        layout.addSpacing(20)
        layout.addWidget(self.userGuideTextWidget)
        busyBarLayout.addWidget(self.busyBar)
        busyBarLayout.addWidget(self.cancelBtn)
        layout.addLayout(busyBarLayout)

        self.connectSignalsAndSlots()

    def connectSignalsAndSlots(self):
        self.delBtn.clicked.connect(self.delBtn.hide)
        self.submitBtn.clicked.connect(self.showBusyBar)
        self.username.returnPressed.connect(self.submitBtn.click)
        self.password.returnPressed.connect(self.submitBtn.click)

    def showErrorState(self, msg='login failed'):
        '''Show the error state of this widget'''
        self.errorMsg.setText(msg)
        self.errorMsg.setVisible(True)
        self.showBusyBar(False)

    def hideError(self):
        self.errorMsg.setVisible(False)

    def showBusyBar(self, mode):
        if self.sender() is self.submitBtn:
            mode = True
        self.busyBar.setVisible(mode)
        self.cancelBtn.setVisible(mode)

    def resetPage(self):
        self.busyBar.setValue(0)
        self.showBusyBar(False)
        self.settingsButton.show()
        self.legalTextWidget.setText(self.legalText)
    
    def showEvent(self, event):
        self.iconLabel.setFocus()
        super(LoginPage, self).showEvent(event)
    
    def mousePressEvent(self, event):
        self.iconLabel.setFocus()
        super(LoginPage, self).mousePressEvent(event)    

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication([])
    loginPage = LoginPage()
    loginPage.show()
    loginPage.raise_()
    sys.exit(app.exec_())