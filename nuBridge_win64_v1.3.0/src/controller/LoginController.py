import base64
import keyring
import logging
import pickle
import os
import platform
import rsa
import sys
import uuid
#from PySide import QtCore, QtGui
from Qt import QtCore
import common

logger = logging.getLogger('Nukepedia.LoginController')

def _getMInfo():
    '''Get machine info as part of login process'''
    address = uuid.getnode()
    h = iter(hex(address)[2:].zfill(12))
    machineID = ''.join(i + next(h) for i in h)
    machineName = platform.node()
    operatingSystem = sys.platform
    return ':'.join((machineID, machineName, operatingSystem)).encode('utf8')

class Keyring(object):
    
    def __init__(self, forceManual=False):
        super(Keyring, self).__init__()
        self.forceManual = False
        self.filePath = os.path.join(common.NKPD_SUPPORT_PATH, '.nuBridge_Keyring')

    def __getPwd(self, u):
        '''Manually load credentials if keyring library is not compatible with current platform'''

        logger.debug('Using Custom Credentials Vault to retrieve password')
        try:
            with open(self.filePath, 'rb') as fileHandle:
                try:
                    userData = pickle.load(fileHandle)
                except:
                    userData = {}
        except IOError:
            return ''
        return userData.get(u, '')

    def __remove(self, u):
        '''Remove password from file'''

        with open(self.filePath, 'rb') as fileHandle:
            userData = pickle.load(fileHandle)
        del userData[u]
        with open(self.filePath, 'wb') as fileHandle:
            pickle.dump(userData, fileHandle, protocol=pickle.HIGHEST_PROTOCOL)

    def __storePwd(self, u, p):
        '''Manually restore credentials if keyring library is not compatible with current platform'''

        logger.debug('Using Custom Credentials Vault to write password')
        d = os.path.dirname(self.filePath)
        if not os.path.isdir(d):
            # first time, create the necessary directories
            os.makedirs(d)
            userData = {}
        else:
            # credentials exist, load tham so we can append to or modify the existing data
            try:
                with open(self.filePath, 'rb') as fileHandle:
                    userData = pickle.load(fileHandle)
            except:
                # if anything fails just don't restore credentials
                userData = {}

        userData[u] = p
        with open(self.filePath, 'wb') as fileHandle:
            pickle.dump(userData, fileHandle, protocol=pickle.HIGHEST_PROTOCOL)

    def read(self, u):
        '''Try to use keyring to retrieve the credentials. If it fails use manual method'''

        if not self.forceManual:
            try:
                p = keyring.get_password('nuBridge', u)
                logger.debug('Using System Keychain to get password')
                return p
            except RuntimeError as e:
                if str(e).startswith('No recommended backend was available.'):
                    return self.__getPwd(u)
                else:
                    # this is unexpected so raise it
                    raise
            except keyring.backends._OS_X_API.Error as e:
                if str(e) == "Can't fetch password from system":
                    # user denied system keychain access
                    pass
        else:
            return self.__getPwd(u)

    def remove(self, u):
        '''Remove the stored credentials'''

        if not self.forceManual:
            try:
                keyring.delete_password('nuBridge', u)
            except keyring.errors.PasswordDeleteError:
                self.__remove(u)
        else:
            self.__remove(u)

    def write(self, u, p):
        '''Try to use keyring to save the credentials. If it fails use manual method'''

        if not self.forceManual:
            try:
                keyring.set_password('nuBridge', u, p.decode("utf-8"))
                logger.debug('Using System Keychain to write password')
            except RuntimeError as e:
                if str(e).startswith('No recommended backend was available.'):
                    self.__storePwd(u, p)
                else:
                    # this is unexpected so raise it
                    raise
        else:
            self.__storePwd(u, p)

class LoginController(QtCore.QObject):
    '''Controls interaction of login process and login page'''

    aboutToClose = QtCore.Signal() # signal to emit so all running threads can be closed gracefully
    signalProcessingLogin = QtCore.Signal(str) # Emitted when login button is pressed
    signalLoginSuccessful = QtCore.Signal(dict)  # Emitted in case of successful login
    signalLoginFailed = QtCore.Signal(str)  # Emitted when login fails
    signalLoginCancelled = QtCore.Signal()

    def __init__( self, loginPage, parent=None ):
        super(LoginController, self).__init__(parent)
        self.loginPage = loginPage
        self.loginPage.legalTextWidget.setOpenExternalLinks(True)
        self.loginPage.errorMsg.setOpenExternalLinks(True)
        self.keyring = Keyring()
        self.connectSignalsWithSlots()

    def __encrypt(self, key):
        '''Encrypt password and machine info with provided key'''
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key)
        #if self.encryptionNeeded:            
        if self.loginPage.password.text() != "<!<place_holder>!>":
            # password did not come from keyring, so we still need to encrypt it
            text = self.loginPage.password.text()
            str_UTF8 = text.encode('utf8')
            # delete it from the widget
            self.loginPage.password.setText('')
            # store only the encrypted version as an attribute of the password widget
            self.loginPage.password.pwd = base64.urlsafe_b64encode(rsa.encrypt(str_UTF8, pubkey))

        # store in keyring if requested
        if self.loginPage.useKeyring.isChecked():
            self.keyring.write(self.loginPage.username.text(), self.loginPage.password.pwd)
        
        # store machine info in the same place as password (i.e. as an attribvute of the password widget)
        self.loginPage.password.machineInfo = base64.urlsafe_b64encode(rsa.encrypt(_getMInfo(), pubkey))
    
    def getFromKeyring(self, u):
        '''Get password from keyring for user name u'''
        p = self.keyring.read(u)
        if p:
            # found password in keyring, let's use it and make sure to avoid double encryption
            self.loginPage.password.pwd = p
            self.loginPage.password.setText("<!<place_holder>!>")
            self.setEncryptionNeeded(False)
            self.loginPage.delBtn.setVisible(True)
        else:
            # no password found, set the flag to encrypt what the user typed in
            self.setEncryptionNeeded(True)       
            self.loginPage.delBtn.setVisible(False)

    def setEncryptionNeeded(self, value):
        self.encryptionNeeded = bool(value)

    def setWidgetVisibility(self, visible):
        for widget in (self.loginPage.username,
                       self.loginPage.useKeyring,
                       self.loginPage.password,
                       self.loginPage.settingsButton,
                       #self.loginPage.guestBtn, # disabled guest login
                       self.loginPage.submitBtn,
                       self.loginPage.userGuideTextWidget):
            widget.setVisible(visible)

    def loginMonitor(self):
        '''Check user credentials via whoami.
        Proceed if pro user, otherwise stay on welcome page and show error message.
        '''
        self.setWidgetVisibility(False)
        self.loginPage.delBtn.setVisible(False) # need to set this manually rather than via setWidetVisibility
                                                # as it needs to react to user input

        def __proceedWithLogin():
            self.loginPage.hideError()
            self.loginPage.useKeyring.setChecked(False) # reset this with every login attempt
            self.signalProcessingLogin.emit('logging into Nukepedia...')
            taskQueue.npdbInstance.setUser(self.loginPage.username.text())
            taskQueue.npdbInstance.setPwd(self.loginPage.password.pwd)
            taskQueue.npdbInstance.setMachineInfo(self.loginPage.password.machineInfo)
       
            ## Get online data           
            taskQueue.setTask('whoAmI')
            # signals when cancelled
            self.signalLoginCancelled.connect(taskQueue.cancel)
            # signals when finished
            taskQueue.worker.retrievedUserInfo.connect(self.processUserInfo)
            taskQueue.start()

        taskQueue = self.parent().dbTaskQueue
        taskQueue.setTask('getKey')
        taskQueue.worker.retrievedKey.connect(self.__encrypt)
        taskQueue.worker.finished.connect(__proceedWithLogin)
        taskQueue.worker.connectionError.connect(self.loginCancelled)
        taskQueue.worker.clientIsObsolete.connect(self.loginCancelled)
        taskQueue.start()

    def processUserInfo(self, userInfo):
        useProUseLogic = True # not needed anymore as we will always need the proUser logic now - unless we make this tool free

        loginSuccess = userInfo['type(s)'] != 'Public'
        isPro = 'ProUser' in userInfo['type(s)']

        if useProUseLogic:
            ######## THIS IS USED FOR PRO USER LOGIC
            if loginSuccess and isPro:
                self.loginPage.hideError()
                self.signalLoginSuccessful.emit(userInfo)
    
            elif not loginSuccess:
                # UNSUCCESSFUL LOGIN
                self.setWidgetVisibility(True)
                errorMessage = 'Wrong user name or password.\nPlease try again.'
                logger.error(errorMessage)
                self.signalLoginFailed.emit(errorMessage)
                self.signalProcessingLogin.emit('')
                self.loginPage.legalTextWidget.setText(self.loginPage.legalText)
    
            else:
                # ACCOUNT NEEDS UPGRADING
                self.setWidgetVisibility(True)
                errorMessage = '''This account is not a pro account.<br><a style="color: #C74F24" href="http://www.nukepedia.com/nubridge">Click here to upgrade</a>'''
                logger.error(errorMessage)
                self.signalLoginFailed.emit(errorMessage)

            ######## END OF PRO USER LOGIC
        else:
            pass


    def loginCancelled(self):
        self.signalLoginCancelled.emit()
        self.loginPage.showBusyBar(False)
        self.setWidgetVisibility(True)
        self.loginPage.legalTextWidget.setText(self.loginPage.legalText)

    def removeFromKeyring(self):
        self.keyring.remove(self.loginPage.username.text())
        self.loginPage.password.setText('')

    def connectSignalsWithSlots(self):
        '''Connect all signals of the GUI's widgets with the corresponding slots'''
        self.loginPage.username.editingFinished.connect(lambda: self.getFromKeyring(self.loginPage.username.text()))
        #if common.NKPD_PLATFORM == 'Linux':
            #self.loginPage.username.editingFinished.connect(lambda: self.getFromKeyring(self.loginPage.username.text()))
        #else:
            #self.loginPage.username.textChanged.connect(self.getFromKeyring) # this pops up the KWallet window too many times
            
        self.loginPage.submitBtn.clicked.connect(self.loginMonitor)
        self.signalLoginFailed.connect(self.loginPage.showErrorState)
        self.loginPage.cancelBtn.clicked.connect(self.loginCancelled)
        self.loginPage.delBtn.clicked.connect(self.removeFromKeyring)

